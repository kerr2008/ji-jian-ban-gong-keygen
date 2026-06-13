# -*- coding: utf-8 -*-
"""
极简办公 v1.0 — 主程序（8个模块 + 解锁验证 + 购买入口）
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from theme import ThemeManager, configure_ttk_styles
from extractor import ExtractorFrame
from excel_tool import ExcelToolFrame
from pdf_tools import PdfToolsFrame
from sensitive import SensitiveFilterFrame
from image_tool import ImageToolFrame
from file_tool import FileToolFrame
from data_tool import DataToolFrame

from PIL import Image, ImageTk
import tkinter as tk
from license import LicenseDialog, is_activated, get_machine_code, get_device_count, add_device_license
from media_tool import MediaToolFrame


class MainApplication:
    def __init__(self, root):
        self.root = root
        self.theme = ThemeManager()

        self.root.title("极简办公 v1.0")
        self.root.geometry("960x680")
        self.root.minsize(800, 600)

        # ========== 解锁验证 ==========
        self.activated = is_activated()
        if not self.activated:
            # 显示解锁窗口（阻塞，必须激活才能继续）
            dialog = LicenseDialog(root, self._on_activated)
            dialog.wait()
            self.activated = is_activated()  # 激活后更新状态
        # ========== 主界面 ==========
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.main_container, width=180)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.nav_buttons_frame = tk.Frame(self.sidebar)
        self.nav_buttons_frame.pack(fill="x", pady=(10, 0))

        self.main_panel = tk.Frame(self.main_container)
        self.main_panel.pack(side="right", fill="both", expand=True)

        self.nav_buttons = []
        self.nav_items = [
            ("📫", "信息提取", "extractor"),
            ("📊", "Excel工坊", "excel"),
            ("📕", "PDF工具箱", "pdf"),
            ("🖤", "图片处理", "image"),
            ("📧", "文件管理", "file"),
            ("🔡", "数据工具", "data"),
            ("🔍", "敏感词过滤", "sensitive"),
            ("🌐", "媒体下载", "media"),
        ]

        for icon, text, key in self.nav_items:
            btn = self._create_nav_button(icon, text, key)
            btn.pack(fill="x", padx=8, pady=1)
            self.nav_buttons.append(btn)

        # ========== 底部 ==========
        bottom_frame = tk.Frame(self.sidebar)
        bottom_frame.pack(side="bottom", fill="x", pady=10, padx=8)

        # 购买按钮
        self.buy_btn = tk.Button(bottom_frame, text="💰 付费购买",
                                 command=self._show_buy_info,
                                 bg="#E65100", fg="white",
                                 font=("Microsoft YaHei", 9, "bold"),
                                 relief="flat", padx=10, pady=5,
                                 cursor="hand2")
        self.buy_btn.pack(fill="x", pady=(0, 5))

        # 续费按钮
        self.renew_btn = tk.Button(bottom_frame, text="🔄 续费授权",
                                   command=self._show_renew_dialog,
                                   bg="#0F9D58", fg="white",
                                   font=("Microsoft YaHei", 9),
                                   relief="flat", padx=10, pady=4,
                                   cursor="hand2", anchor="w")
        self.renew_btn.pack(fill="x", pady=(0, 5))

        # 客服二维码按钮
        self.cs_btn = tk.Button(bottom_frame, text="💬 联系客服",
                                command=self._show_customer_service,
                                bg="#1A73E8", fg="white",
                                font=("Microsoft YaHei", 9),
                                relief="flat", padx=10, pady=4,
                                cursor="hand2", anchor="w")
        self.cs_btn.pack(fill="x", pady=(0, 5))

        self.theme_btn = tk.Button(bottom_frame, text="🌙 深色模式",
                                   command=self._toggle_theme,
                                   font=("Microsoft YaHei", 9),
                                   relief="flat", padx=10, pady=4,
                                   cursor="hand2", anchor="w")
        self.theme_btn.pack(fill="x")
        tk.Label(bottom_frame, text="v1.0 | 办公自动化工具 | 会员享受所有更新",
                 font=("Microsoft YaHei", 7),
                 fg="#888888").pack(fill="x", pady=(5, 0))

        # ========== 初始化面板 ==========
        self.frames = {}
        self.current_frame = None
        self.current_key = None

        for icon, text, key in self.nav_items:
            frame = ttk.Frame(self.main_panel)
            self.frames[key] = frame

        # 创建模块界面
        self.extractor_frame = ExtractorFrame(self.frames["extractor"], self.theme)
        self.extractor_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.excel_frame = ExcelToolFrame(self.frames["excel"], self.theme)
        self.excel_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.pdf_frame = PdfToolsFrame(self.frames["pdf"], self.theme)
        self.pdf_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.image_frame = ImageToolFrame(self.frames["image"], self.theme)
        self.image_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.file_frame = FileToolFrame(self.frames["file"], self.theme)
        self.file_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.data_frame = DataToolFrame(self.frames["data"], self.theme)
        self.data_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.sensitive_frame = SensitiveFilterFrame(self.frames["sensitive"], self.theme)
        self.sensitive_frame.pack(fill="both", expand=True, padx=15, pady=15)
        self.media_frame = MediaToolFrame(self.frames["media"], self.theme)
        self.media_frame.pack(fill="both", expand=True, padx=15, pady=15)

        self._apply_theme()
        self._switch_to("extractor")
        self._center_window()

    def _on_activated(self):
        self.activated = True

    def _show_buy_info(self):
        machine = get_machine_code()
        msg = (
            "💰 极简办公 · 购买授权\n\n"
            "─────────────────────────\n\n"
            "微信联系：kerr2008\n\n"
            "┌───定价───┐\n"
            "🪎 7天体验   9.9元\n"
            "🪍 30天标准  29.9元\n"
            "🪌 永久授权  99元\n\n"
            "┌───附赠───┐\n"
            "🎵 购买即赠：\n"
            "  路 Excel 模板包（50个）\n"
            "  路 合同模板包（20个）\n"
            "  路 终身免费升级\n\n"
            "┌───购买流程───┐\n"
            "1️⃣ 加微信：kerr2008\n"
            "2️⃣ 选择套餐，付款\n"
            "3️⃣ 发送以下机器码：\n\n"
            "   " + machine + "\n\n"
            "4️⃣ 我回解锁码，复制粘贴即可\n\n"
            "─────────────────────────"
        )
        messagebox.showinfo("💰 购买授权", msg)


    def _show_renew_dialog(self):
        """续费授权窗口 - 显示机器码 + 微信二维码 + 输入解锁码"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔄 续费/授权")
        dialog.geometry("400x680")
        dialog.resizable(False, False)
        dialog.configure(bg="#F5F5F5")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        w, h = 400, 680
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry("{:.0f}x{:.0f}+{:.0f}+{:.0f}".format(w, h, (sw-w)//2, (sh-h)//2))
        
        # 可滚动容器
        canvas = tk.Canvas(dialog, bg="#F5F5F5", highlightthickness=0)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#F5F5F5")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=370)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main = scroll_frame
        machine_code = get_machine_code()
        device_count = get_device_count()
        
        # 标题
        tk.Label(main, text="🔄 续费 / 授权管理", font=("Microsoft YaHei", 16, "bold"),
                 bg="#F5F5F5", fg="#1A73E8").pack(pady=(12, 5))
        tk.Label(main, text="会员享受所有更新，一个授权码可绑定多台设备",
                 font=("Microsoft YaHei", 9), bg="#F5F5F5", fg="#666666").pack(pady=(0, 8))
        
        # ========== 机器码区块 ==========
        mc_frame = tk.LabelFrame(main, text=" 本机信息 ", font=("Microsoft YaHei", 9, "bold"),
                                  bg="#F5F5F5", fg="#333", padx=12, pady=8)
        mc_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        tk.Label(mc_frame, text="本机机器码：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333", anchor="w").pack(fill="x")
        code_display = tk.Frame(mc_frame, bg="#FFFFFF", bd=1, relief="solid", padx=8, pady=5)
        code_display.pack(fill="x", pady=(2, 5))
        tk.Label(code_display, text=machine_code,
                 font=("Consolas", 12, "bold"),
                 bg="#FFFFFF", fg="#D93025").pack()
        
        btn_row = tk.Frame(mc_frame, bg="#F5F5F5")
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="📋 复制机器码",
                  command=lambda mc=machine_code: self._copy_text(dialog, mc),
                  bg="#1A73E8", fg="white",
                  font=("Microsoft YaHei", 9), relief="flat",
                  padx=10, pady=3, cursor="hand2").pack(side="left", padx=(0, 5))
        tk.Label(btn_row, text="已绑定设备: {} 台".format(device_count),
                 font=("Microsoft YaHei", 8), bg="#F5F5F5", fg="#888").pack(side="left", padx=(5, 0))
        
        # ========== 价格区块 ==========
        price_frame = tk.Frame(main, bg="#FFF8E1", bd=1, relief="solid", padx=15, pady=8)
        price_frame.pack(fill="x", padx=20, pady=(0, 8))
        tk.Label(price_frame, text="💰 价格方案", font=("Microsoft YaHei", 10, "bold"),
                 bg="#FFF8E1", fg="#E65100").pack()
        tk.Label(price_frame,
                 text="7天体验  9.9元  |  30天标准  29.9元\n* 永久授权  199元（重装可再次申领）\n一个授权码可绑定多台电脑使用",
                 font=("Microsoft YaHei", 9), bg="#FFF8E1", fg="#333333", justify="center").pack()
        
        # ========== 解锁码输入区块 ==========
        lic_frame = tk.LabelFrame(main, text=" 输入解锁码激活 ", font=("Microsoft YaHei", 9, "bold"),
                                   bg="#F5F5F5", fg="#333", padx=12, pady=8)
        lic_frame.pack(fill="x", padx=20, pady=(0, 8))
        
        tk.Label(lic_frame, text="解锁码：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333", anchor="w").pack(fill="x")
        entry_code = tk.Entry(lic_frame, font=("Consolas", 11),
                               bg="#FFFFFF", fg="#333",
                               relief="solid", bd=1, justify="center")
        entry_code.pack(fill="x", pady=(2, 8), ipady=4)
        
        tk.Button(lic_frame, text="🔓 验证激活",
                  command=lambda: self._renew_activate(dialog, entry_code, machine_code),
                  bg="#0F9D58", fg="white",
                  font=("Microsoft YaHei", 10, "bold"), relief="flat",
                  padx=20, pady=5, cursor="hand2").pack(fill="x")
        
        # ========== 微信联系 + 二维码区块 ==========
        tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=30, pady=(5, 8))
        
        tk.Label(main, text="📱 扫码联系购买/续费", font=("Microsoft YaHei", 10, "bold"),
                 bg="#F5F5F5", fg="#333").pack()
        
        # 微信联系 1 + 二维码
        self._show_qr_code(main, "微信二维码.jpg", "微信联系1: kerr2008")
        
        tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=40, pady=(2, 5))
        
        # 微信联系 2 + 备用二维码
        self._show_qr_code(main, "备用二维码.jpg", "微信联系2: xin012169")
        
        # 关闭按钮
        tk.Button(main, text="关闭", command=dialog.destroy,
                  bg="#1A73E8", fg="white",
                  font=("Microsoft YaHei", 10), relief="flat",
                  padx=20, pady=4, cursor="hand2").pack(pady=(8, 5))
        
        dialog.wait_window()

    def _show_customer_service(self):
        """客服窗口 - 显示两个微信二维码和联系方式"""
        dialog = tk.Toplevel(self.root)
        dialog.title("💬 联系客服")
        dialog.geometry("380x580")
        dialog.resizable(False, False)
        dialog.configure(bg="#F5F5F5")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        w, h = 380, 580
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry("{:.0f}x{:.0f}+{:.0f}+{:.0f}".format(w, h, (sw-w)//2, (sh-h)//2))
        
        # 可滚动容器
        canvas = tk.Canvas(dialog, bg="#F5F5F5", highlightthickness=0)
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="#F5F5F5")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=350)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main = scroll_frame
        
        tk.Label(main, text="💬 联系客服", font=("Microsoft YaHei", 16, "bold"),
                 bg="#F5F5F5", fg="#1A73E8").pack(pady=(10, 5))
        tk.Label(main, text="购买 / 续费 / 使用问题 扫码咨询",
                 font=("Microsoft YaHei", 9), bg="#F5F5F5", fg="#666666").pack(pady=(0, 10))
        
        # 微信联系 1（主微信）
        self._show_qr_code(main, "微信二维码.jpg", "微信联系1: kerr2008")
        
        # 分隔线
        tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=20, pady=8)
        
        # 微信联系 2（备用微信）
        self._show_qr_code(main, "备用二维码.jpg", "微信联系2: xin012169")
        
        # 底部提示
        tk.Label(main, text="添加时请备注：极简办公",
                 font=("Microsoft YaHei", 8),
                 bg="#F5F5F5", fg="#888888").pack(pady=(5, 2))
        
        tk.Button(main, text="关闭", command=dialog.destroy,
                  bg="#1A73E8", fg="white",
                  font=("Microsoft YaHei", 10), relief="flat",
                  padx=20, pady=4, cursor="hand2").pack(pady=(5, 5))
        
        dialog.wait_window()

    def _show_qr_code(self, parent, filename, caption):
        """通用二维码展示方法"""
        try:
            from PIL import Image, ImageTk
            qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            if os.path.exists(qr_path):
                img = Image.open(qr_path)
                max_w = 200
                w0, h0 = img.size
                if w0 > max_w:
                    ratio = max_w / w0
                    img = img.resize((max_w, int(h0 * ratio)), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                # 保持引用防止GC
                if not hasattr(self, "_qr_photos"):
                    self._qr_photos = []
                self._qr_photos.append(photo)
                tk.Label(parent, image=photo, bg="#F5F5F5").pack(pady=(3, 0))
                tk.Label(parent, text=caption, font=("Microsoft YaHei", 9),
                         bg="#F5F5F5", fg="#1A73E8").pack(pady=(0, 3))
            else:
                tk.Label(parent, text="📱 微信联系：kerr2008",
                         font=("Microsoft YaHei", 10, "bold"),
                         bg="#F5F5F5", fg="#E65100").pack(pady=(3, 3))
        except:
            tk.Label(parent, text="📱 微信联系：kerr2008",
                     font=("Microsoft YaHei", 10, "bold"),
                     bg="#F5F5F5", fg="#E65100").pack(pady=(3, 3))

    def _copy_text(self, dialog, text):
        """复制文本到剪贴板并反馈"""
        dialog.clipboard_clear()
        dialog.clipboard_append(text)
        # 显示临时反馈（使用已有的或创建临时Label）
        import tkinter.messagebox as mb
        mb.showinfo("已复制", "机器码已复制到剪贴板\n发送给卖家即可获取解锁码")
    
    def _renew_activate(self, dialog, entry, machine_code):
        """在续费窗口中验证解锁码（支持多设备绑定）"""
        from license import verify_license, save_license, add_device_license
        code = entry.get().strip()
        if not code:
            messagebox.showwarning("提示", "请输入解锁码")
            return
        valid, msg = verify_license(machine_code, code)
        if valid:
            # 保存授权
            save_license(machine_code, code)
            messagebox.showinfo("成功", "激活成功！" + msg + "\n\n授权码已绑定此设备\n可继续在其他电脑上使用同一授权码")
            dialog.destroy()
            # 刷新界面
            self._switch_to(self.current_key)
        else:
            messagebox.showerror("失败", "解锁码无效，请检查后重试\n\n如需购买请联系微信：\nkerr2008 或 xin012169")
    
    def _create_nav_button(self, icon, text, key):
        c = self.theme.colors
        btn = tk.Button(self.nav_buttons_frame,
                        text="  " + icon + "  " + text,
                        command=lambda k=key: self._switch_to(k),
                        font=("Microsoft YaHei", 10),
                        relief="flat", padx=15, pady=6,
                        cursor="hand2", anchor="w",
                        bg=c["sidebar_bg"], fg=c["sidebar_fg"],
                        activebackground=c["sidebar_hover"],
                        activeforeground=c["sidebar_fg"])
        return btn

    def _switch_to(self, key):
        if self.current_key == key:
            return
        c = self.theme.colors
        if self.current_frame:
            self.current_frame.pack_forget()
        self.current_key = key
        self.current_frame = self.frames[key]
        self.current_frame.pack(fill="both", expand=True)
        for i, (icon, text, k) in enumerate(self.nav_items):
            btn = self.nav_buttons[i]
            if k == key:
                btn.configure(bg=c["sidebar_selected"], fg=c["accent"])
            else:
                btn.configure(bg=c["sidebar_bg"], fg=c["sidebar_fg"])

    def _toggle_theme(self):
        self.theme.toggle()
        c = self.theme.colors
        self.theme_btn.config(
            text="☀️ 浅色模式" if self.theme.is_dark else "🌙 深色模式",
            bg=c["sidebar_bg"], fg=c["sidebar_fg"])
        self._apply_theme()
        for name in ["extractor", "excel", "pdf", "image", "file", "data", "sensitive", "media"]:
            try:
                getattr(self, name + "_frame").apply_theme()
            except:
                pass

    def _apply_theme(self):
        c = self.theme.colors
        self.root.configure(bg=c["bg"])
        self.main_container.configure(bg=c["bg"])
        self.sidebar.configure(bg=c["sidebar_bg"])
        self.main_panel.configure(bg=c["panel_bg"])
        self.nav_buttons_frame.configure(bg=c["sidebar_bg"])
        for btn in self.nav_buttons:
            btn.configure(bg=c["sidebar_bg"], fg=c["sidebar_fg"],
                          activebackground=c["sidebar_hover"],
                          activeforeground=c["sidebar_fg"])
        if self.current_key:
            for i, (icon, text, k) in enumerate(self.nav_items):
                btn = self.nav_buttons[i]
                if k == self.current_key:
                    btn.configure(bg=c["sidebar_selected"], fg=c["accent"])
        self.buy_btn.configure(bg="#E65100")
        self.cs_btn.configure(bg=c["accent"])
        self.renew_btn.configure(bg="#0F9D58")
        configure_ttk_styles(self.theme)

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(str(w) + "x" + str(h) + "+" + str((sw - w) // 2) + "+" + str((sh - h) // 2))


def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except:
        try:
            style.theme_use("clam")
        except:
            pass
    app = MainApplication(root)

    def on_close():
        if messagebox.askokcancel("退出", "确定要退出极简办公吗？"):
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
