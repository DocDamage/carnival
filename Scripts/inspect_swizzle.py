import unreal

unreal.log_warning(f"Swizzle matches: {[x for x in dir(unreal) if 'Swizzle' in x or 'swizzle' in x]}")
s = unreal.InputModifierSwizzleAxis()
unreal.log_warning(f"Swizzle dir: {dir(s)}")
for p in dir(s):
    if not p.startswith("_"):
        unreal.log_warning(f"Swizzle prop: {p}")

