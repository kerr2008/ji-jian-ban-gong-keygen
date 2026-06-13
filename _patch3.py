path = r'C:\Users\popoz\Documents\赚钱项目咸鱼\极简办公\main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import for multi-device functions and get_device_count
# After the existing imports from license
old_import = 'from license import LicenseDialog, is_activated, get_machine_code'
new_import = 'from license import LicenseDialog, is_activated, get_machine_code, get_device_count, add_device_license'
content = content.replace(old_import, new_import)

# 2. Update _show_renew_dialog — complete rewrite
# Find the method from "def _show_renew_dialog" to the blank line before "_show_customer_service"
old_renew = '''    def _show_renew_dialog(self):
        """续费窗口 - 显示二维码供用户扫码续费"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔄 续费授权")
        dialog.geometry("380x540")
        dialog.resizable(False, False)
        dialog.configure(bg="#F5F5F5")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        w, h = 380, 540
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry("{:.0f}x{:.0f}+{:.0f}+{:.0f}".format(w, h, (sw-w)//2, (sh-h)//2))
        
        main = tk.Frame(dialog, bg="#F5F5F5", padx=25, pady=15)
        main.pack(fill="both", expand=True)
        
        tk.Label(main, text="🔄 续费授权", font=("Microsoft YaHei", 16, "bold"),
                 bg="#F5F5F5", fg="#1A73E8").pack(pady=(0, 5))
        tk.Label(main, text="会员享受所有更新，扫码联系续费",
                 font=("Microsoft YaHei", 9), bg="#F5F5F5", fg="#666666").pack(pady=(0, 10))
        
        # 续费价格
        price_frame = tk.Frame(main, bg="#FFF8E1", bd=1, relief="solid", padx=15, pady=8)
        price_frame.pack(fill="x", pady=(0, 10))
        tk.Label(price_frame, text="续费价格", font=("Microsoft YaHei", 10, "bold"),
                 bg="#FFF8E1", fg="#E65100").pack()
        tk.Label(price_frame, text="30天 19.9元 | 永久 69元",
                 font=("Microsoft YaHei", 9), bg="#FFF8E1", fg="#333333").pack()
        
        # 微信二维码
        self._show_qr_code(main, "微信二维码.jpg", "👆 扫码联系续费")
        
        # 备用二维码
        self._show_qr_code(main, "备用二维码.jpg", "备用联系人（扫码加好友）")
        
        tk.Button(main, text="关闭", command=dialog.destroy,
                  bg="#1A73E8", fg="white",
                  font=("Microsoft YaHei", 10), relief="flat",
                  padx=20, pady=4, cursor="hand2").pack(pady=(5, 0))
        
        dialog.wait_window()'''

new_renew = '''    def _show_renew_dialog(self):
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
                 text="7天体验  9.9元  |  30天标准  29.9元\n⏺ 永久授权  199元（重装可再次申领）\n一个授权码可绑定多台电脑使用",
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
        
        dialog.wait_window()'''

content = content.replace(old_renew, new_renew)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('main.py renew dialog updated OK')
