"""Exercise CI gates against real, temporary Git repositories."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


class SourceChecksTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        script = self.root / "Scripts/ci/check_source.py"
        script.parent.mkdir(parents=True)
        shutil.copy2(Path(__file__).with_name("check_source.py"), script)
        self.git("init", "--quiet")
        self.git("config", "user.name", "CI fixture")
        self.git("config", "user.email", "ci@example.invalid")
        self.write(".gitignore", "Saved/\n")
        self.write("valid.py", "answer = 42\n")
        self.commit()
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.STDOUT)

    def write(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    def commit(self):
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "CI fixture")

    def check(self):
        return subprocess.run([sys.executable, "Scripts/ci/check_source.py", "--base", self.base],
                              cwd=self.root, text=True, capture_output=True)

    def test_valid_repository(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_python_fails(self):
        self.write("broken.py", "answer = (\n")
        self.commit()
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("broken.py", result.stderr)

    def test_duplicate_json_key_fails(self):
        self.write("fixture.uproject", '{"FileVersion": 3, "FileVersion": 4}\n')
        self.commit()
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate JSON key", result.stderr)

    def test_ignored_file_in_commit_fails(self):
        self.write("Saved/diagnostic.txt", "Keep local.\n")
        self.git("add", "--force", "Saved/diagnostic.txt")
        self.commit()
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Saved/diagnostic.txt", result.stderr)

    def test_whitespace_error_fails(self):
        self.write("fixture.txt", "Trailing whitespace   \n")
        self.git("add", "fixture.txt")
        result = self.check()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("trailing whitespace", result.stderr)


if __name__ == "__main__":
    unittest.main()
