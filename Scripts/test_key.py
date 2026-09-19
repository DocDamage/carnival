import unreal

def test_key():
    try:
        k1 = unreal.Key()
        k1.key_name = unreal.Name("B")
        unreal.log_warning(f"k1: {k1}, {k1.key_name}")
    except Exception as e:
        unreal.log_warning(f"k1 failed: {e}")

    try:
        k2 = unreal.Key(key_name="B")
        unreal.log_warning(f"k2: {k2}")
    except Exception as e:
        unreal.log_warning(f"k2 failed: {e}")

test_key()

