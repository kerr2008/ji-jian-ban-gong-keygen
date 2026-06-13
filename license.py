# -*- coding: utf-8 -*-
"""
解锁/授权模块
按机器码+天数生成解锁码，离线验证
"""

import os
import sys
import hashlib
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import platform
import uuid

# 二维码图片支持
try:
    from PIL import Image, ImageTk
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False
    Image = None
    ImageTk = None

# ============ 核心算法 ============

# 密钥（你自己独享，不要泄漏）
SECRET_KEY = b"JJBG_2026_@kerr2008#Secret!"


def get_machine_code():
    """生成唯一机器码（基于硬件特征）"""
    try:
        # 组合多个特征：CPU + 主板 + MAC 地址
        parts = [
            platform.processor() or "",
            platform.node() or "",
            str(uuid.getnode()),  # MAC 地址
            os.environ.get("COMPUTERNAME", ""),
        ]
        raw = "|".join(parts).encode("utf-8")
        code = hashlib.md5(raw).hexdigest()[:16].upper()
        # 格式化：分成4组
        return "-".join([code[i:i+4] for i in range(0, 16, 4)])
    except:
        return "ERROR-0000-0000-0000"


def generate_license(machine_code, days):
    """生成解锁码
    machine_code: 机器码（如 ABCD-1234-EF56-7890）
    days: 有效天数（0=永久）
    返回：解锁码
    """
    raw = (machine_code + str(days) + "|JJBG_2026").encode("utf-8")
    code = hashlib.sha256(raw + SECRET_KEY).hexdigest()[:24].upper()
    # 分成6组，每组4位
    return "-".join([code[i:i+4] for i in range(0, 24, 4)])


def verify_license(machine_code, license_code):
    """验证解锁码
    返回：(是否有效, 剩余天数消息)
    """
    license_code = license_code.strip().upper()
    machine_code = machine_code.strip().upper()

    # 尝试不同天数
    for days in [0, 7, 30, 90, 180, 365, 9999]:
        expected = generate_license(machine_code, days)
        if expected == license_code:
            if days == 0:
                return True, "永久授权"
            else:
                return True, str(days) + "天授权"

    return False, "解锁码无效"


def load_license_file():
    """从本地加载已保存的授权信息（兼容新旧格式）"""
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            mc = data.get("machine_code", "")
            lc = data.get("license_code", "")
            # 新格式：从 devices 取当前机器码
            if not mc:
                current = get_machine_code()
                for d in data.get("devices", []):
                    if d.get("machine_code") == current:
                        mc = current
                        break
            return mc, lc
        except:
            pass
    return "", ""


def save_license(machine_code, license_code):
    """保存授权信息到本地（支持多设备）"""
    lic_file = _get_license_path()
    try:
        data = {"devices": [], "activate_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if os.path.exists(lic_file):
            try:
                with open(lic_file, "r", encoding="utf-8") as f:
                    old = json.load(f)
                if "devices" in old:
                    data["devices"] = old["devices"]
            except:
                pass
        data["license_code"] = license_code
        # 添加或更新当前设备
        current_mc = machine_code
        found = False
        for d in data["devices"]:
            if d.get("machine_code") == current_mc:
                d["bind_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                found = True
                break
        if not found:
            data["devices"].append({
                "machine_code": current_mc,
                "bind_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


def get_device_count():
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            devices = data.get("devices", [])
            return len(devices)
        except:
            pass
    return 0


def add_device_license(machine_code, license_code):
    """将新设备绑定到已有授权
    返回：(成功, 消息)
    """
    lic_file = _get_license_path()
    if not os.path.exists(lic_file):
        return False, "请先在主设备上激活"
    try:
        with open(lic_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing_code = data.get("license_code", "")
        if not existing_code:
            return False, "未检测到授权信息"
        # 验证机器码与现存授权是否匹配
        valid, msg = verify_license(machine_code, existing_code)
        if not valid:
            return False, "授权码与此设备不匹配"
        # 检查是否已绑定
        for d in data.get("devices", []):
            if d.get("machine_code") == machine_code:
                d["bind_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(lic_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True, "设备已重新绑定"
        data["devices"].append({
            "machine_code": machine_code,
            "bind_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        with open(lic_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True, f"已绑定新设备（共 {len(data['devices'])} 台）"
    except Exception as e:
        return False, f"绑定失败: {str(e)[:50]}"


def _get_license_path():
    """授权文件保存路径（用户目录下）"""
    app_dir = os.path.join(os.path.expanduser("~"), ".jjbg_license")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "license.dat")


def is_activated():
    """检查当前电脑是否已激活（支持多设备）"""
    lic_file = _get_license_path()
    if os.path.exists(lic_file):
        try:
            with open(lic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            lcode = data.get("license_code", "")
            current_mc = get_machine_code()
            # 1. 检查单设备旧格式
            old_mc = data.get("machine_code", "")
            if old_mc and old_mc == current_mc and lcode:
                valid, _ = verify_license(old_mc, lcode)
                if valid:
                    return True
            # 2. 检查多设备格式
            devices = data.get("devices", [])
            for d in devices:
                if d.get("machine_code") == current_mc and lcode:
                    valid, _ = verify_license(current_mc, lcode)
                    if valid:
                        return True
        except:
            pass
    return False


# ============ 解锁窗口 GUI ============

class LicenseDialog:
    """解锁对话框"""

    def __init__(self, root, on_activated):
        self.root = root
        self.on_activated = on_activated
        self.dialog = None
        self.copy_btn = None
        self._show()

    def _show(self):
        self.dialog = tk.Toplevel(self.root)
        self.dialog.title("极简办公 — 激活")
        self.dialog.geometry("420x640")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#F5F5F5")

        # 居中
        self.dialog.update_idletasks()
        w, h = 420, 640
        sw = self.dialog.winfo_screenwidth()
        sh = self.dialog.winfo_screenheight()
        self.dialog.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))

        # 阻止关闭
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)

        # 可滚动内容容器
        canvas = tk.Canvas(self.dialog, bg="#F5F5F5", highlightthickness=0)
        scrollbar = tk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#F5F5F5")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        main = scroll_frame

        machine_code = get_machine_code()

        # Logo/标题
        tk.Label(main, text="极简办公", font=("Microsoft YaHei", 18, "bold"),
                 bg="#F5F5F5", fg="#1A73E8").pack(pady=(15, 5))
        tk.Label(main, text="请先激活软件后方可使用", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#666666").pack(pady=(0, 15))

        # 机器码区域
        tk.Label(main, text="本机机器码：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333333", anchor="w").pack(fill="x", padx=30)

        code_frame = tk.Frame(main, bg="#FFFFFF", bd=1, relief="solid", padx=10, pady=8)
        code_frame.pack(fill="x", padx=30, pady=(0, 5))
        tk.Label(code_frame, text=machine_code,
                 font=("Consolas", 13, "bold"),
                 bg="#FFFFFF", fg="#D93025").pack()

        # 一键复制按钮
        self.copy_btn = tk.Button(main, text="📋 一键复制机器码",
                                  command=lambda: self._copy_code(machine_code),
                                  bg="#1A73E8", fg="white",
                                  font=("Microsoft YaHei", 10, "bold"),
                                  relief="flat", padx=20, pady=6, cursor="hand2")
        self.copy_btn.pack(pady=(0, 15))

        # 解锁码输入
        tk.Label(main, text="解锁码：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333333", anchor="w").pack(fill="x", padx=30)

        self.entry_code = tk.Entry(main, font=("Consolas", 12),
                                    bg="#FFFFFF", fg="#333333",
                                    relief="solid", bd=1, justify="center")
        self.entry_code.pack(fill="x", padx=30, pady=(0, 15), ipady=5)

        # 激活按钮
        btn_frame = tk.Frame(main, bg="#F5F5F5")
        btn_frame.pack(fill="x", padx=30, pady=(0, 10))

        self.btn_activate = tk.Button(btn_frame, text="🔓 激活",
                                      command=self._try_activate,
                                      bg="#1A73E8", fg="white",
                                      font=("Microsoft YaHei", 10, "bold"),
                                      relief="flat", padx=20, pady=6, cursor="hand2")
        self.btn_activate.pack(fill="x")

        # 分隔线
        tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=30, pady=(5, 8))

        # ======== 微信联系和二维码区块 ========
        if _HAS_PIL:
            # 微信联系 1（主微信）
            qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "微信二维码.jpg")
            if os.path.exists(qr_path):
                img = Image.open(qr_path)
                max_w = 200
                w0, h0 = img.size
                if w0 > max_w:
                    ratio = max_w / w0
                    img = img.resize((max_w, int(h0 * ratio)), Image.LANCZOS)
                self.qr_photo = ImageTk.PhotoImage(img)
                tk.Label(main, image=self.qr_photo, bg="#F5F5F5").pack(pady=(3, 0))
                tk.Label(main, text="微信联系1: kerr2008", font=("Microsoft YaHei", 9, "bold"),
                         bg="#F5F5F5", fg="#1A73E8").pack(pady=(0, 5))
            else:
                tk.Label(main, text="微信联系1: kerr2008", font=("Microsoft YaHei", 10, "bold"),
                         bg="#F5F5F5", fg="#E65100").pack(pady=(5, 3))

            # 分隔
            tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=40, pady=(2, 5))

            # 微信联系 2（备用微信）
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "备用二维码.jpg")
            if os.path.exists(backup_path):
                img2 = Image.open(backup_path)
                max_w2 = 180
                w0, h0 = img2.size
                if w0 > max_w2:
                    ratio = max_w2 / w0
                    img2 = img2.resize((max_w2, int(h0 * ratio)), Image.LANCZOS)
                self.qr_photo2 = ImageTk.PhotoImage(img2)
                tk.Label(main, image=self.qr_photo2, bg="#F5F5F5").pack(pady=(2, 0))
                tk.Label(main, text="微信联系2: xin012169", font=("Microsoft YaHei", 9),
                         bg="#F5F5F5", fg="#888888").pack(pady=(0, 3))
            else:
                tk.Label(main, text="微信联系2: xin012169", font=("Microsoft YaHei", 9),
                         bg="#F5F5F5", fg="#888888").pack(pady=(2, 3))
        else:
            tk.Label(main, text="微信联系1: kerr2008", font=("Microsoft YaHei", 10, "bold"),
                     bg="#F5F5F5", fg="#E65100").pack(pady=(5, 2))
            tk.Label(main, text="微信联系2: xin012169", font=("Microsoft YaHei", 9),
                     bg="#F5F5F5", fg="#888888").pack(pady=(0, 5))

        # 底部购买信息
        buy_frame = tk.Frame(main, bg="#FFF8E1", bd=1, relief="solid", padx=15, pady=10)
        buy_frame.pack(fill="x", padx=30, pady=(0, 10))

        tk.Label(buy_frame, text="微信联系1: kerr2008",
                 font=("Microsoft YaHei", 10, "bold"),
                 bg="#FFF8E1", fg="#E65100").pack()
        tk.Label(buy_frame,
                 text="7天体验 9.9元 | 30天 29.9元 | 永久 199元\n重装系统后可再次申领\n一个授权码可绑定多台设备",
                 font=("Microsoft YaHei", 8),
                 bg="#FFF8E1", fg="#666666", justify="center").pack()

    def _copy_code(self, code):
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(code)
        # 反馈
        old_text = self.copy_btn.cget("text")
        old_bg = self.copy_btn.cget("bg")
        self.copy_btn.config(text="✅ 已复制！粘贴发给卖家", bg="#0F9D58")
        self.dialog.after(3000, lambda: self.copy_btn.config(text=old_text, bg=old_bg))

    def _try_activate(self):
        code = self.entry_code.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入解锁码")
            return

        mc = get_machine_code()
        valid, msg = verify_license(mc, code)

        if valid:
            save_license(mc, code)
            messagebox.showinfo("激活成功", "🎉 激活成功！" + msg + "\n\n感谢使用极简办公！")
            self.dialog.destroy()
            if self.on_activated:
                self.on_activated()
        else:
            messagebox.showerror("激活失败", "解锁码无效，请检查后重试\n\n如需购买请联系微信：kerr2008")

    def _on_close(self):
        if messagebox.askokcancel("退出", "未激活无法使用软件\n\n确定退出吗？"):
            self.root.destroy()
            sys.exit(0)

    def wait(self):
        """等待对话框关闭"""
        self.root.wait_window(self.dialog)
