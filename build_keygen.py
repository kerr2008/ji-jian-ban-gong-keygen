# -*- coding: utf-8 -*-
"""极简办公解锁码生成器打包脚本"""
import sys, os
os.environ["PYTHONNOUSERSITE"] = "1"
tool_dir = os.path.dirname(__file__)
pyi_dir = os.path.join(tool_dir, "pyinstaller_dist")
ws_pkg = r"C:\Users\popoz\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages"
sys.path.insert(0, pyi_dir)
if ws_pkg not in sys.path:
    sys.path.insert(0, ws_pkg)
os.chdir(tool_dir)
import site as site_module
site_module.USER_SITE = ''
site_module.getusersitepackages = lambda: ''
import PyInstaller.__main__
PyInstaller.__main__.run([
    "keygen.py", "--name=解锁码生成器", "--onefile", "--windowed", "--noconsole", "--clean",
    "--distpath=dist", "--workpath=build_k", "--specpath=.",
])
out = os.path.join(tool_dir, "dist", "解锁码生成器.exe")
if os.path.exists(out):
    mb = os.path.getsize(out) / 1024 / 1024
    print("解锁码生成器.exe 打包成功 ({:.1f} MB)".format(mb))
else:
    print("打包失败")
