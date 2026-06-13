# -*- coding: utf-8 -*-
"""鏋佺畝鍔炲叕鎵撳寘鑴氭湰"""
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
    "main.py", "--name=极简办公", "--onefile", "--noconsole", "--clean",
    "--hidden-import=pandas", "--hidden-import=openpyxl", "--hidden-import=pypdf",
    "--hidden-import=docx", "--hidden-import=PIL", "--hidden-import=pdfplumber", "--hidden-import=pdfminer", "--hidden-import=yt_dlp", "--hidden-import=requests", "--hidden-import=docx.table", "--hidden-import=lxml", "--hidden-import=docx.oxml.ns",
    "--distpath=dist", "--workpath=build", "--specpath=.",
])
out = os.path.join(tool_dir, "dist", "极简办公.exe")
if os.path.exists(out):
    mb = os.path.getsize(out) / 1024 / 1024
    print("鏋佺畝鍔炲叕.exe 鎵撳寘鎴愬姛 ({:.1f} MB)".format(mb))
else:
    print("鎵撳寘澶辫触")






