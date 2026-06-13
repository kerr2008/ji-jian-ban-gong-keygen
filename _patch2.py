path = r'C:\Users\popoz\Documents\赚钱项目咸鱼\极简办公\license.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update pricing in the license dialog (old: 7天 9.9元 | 30天 29.9元 | 永久 99元)
content = content.replace(
    'text=\"7天体验 9.9元 | 30天 29.9元 | 永久 99元\\n付款后发机器码，秒回解锁码\"',
    'text=\"7天体验 9.9元 | 30天 29.9元 | 永久 199元\\n重装系统后可再次申领\\n一个授权码可绑定多台设备\"'
)

# 2. Update the WeChat contact info in the purchase section
content = content.replace(
    '主微信联系购买：kerr2008',
    '微信联系1: kerr2008'
)

# 3. Restructure the QR code section in _show() - replace from "分隔线" through the backup qr block
old_qr_section = '''        # 分隔线
        tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=30, pady=(5, 10))

        # 二维码图片
        if _HAS_PIL:
            qr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "微信二维码.jpg")
            if os.path.exists(qr_path):
                img = Image.open(qr_path)
                max_w = 220
                w0, h0 = img.size
                if w0 > max_w:
                    ratio = max_w / w0
                    img = img.resize((max_w, int(h0 * ratio)), Image.LANCZOS)
                self.qr_photo = ImageTk.PhotoImage(img)
                tk.Label(main, image=self.qr_photo, bg="#F5F5F5").pack(pady=(5, 0))
                tk.Label(main, text="👆 扫码联系卖家购买（主微信）", font=("Microsoft YaHei", 9),
                         bg="#F5F5F5", fg="#1A73E8").pack(pady=(2, 5))
            else:
                tk.Label(main, text="📱 微信联系购买：kerr2008", font=("Microsoft YaHei", 10, "bold"),
                         bg="#F5F5F5", fg="#E65100").pack(pady=(5, 10))
            
            # 备用二维码
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "备用二维码.jpg")
            if os.path.exists(backup_path):
                img2 = Image.open(backup_path)
                max_w2 = 180
                w0, h0 = img2.size
                if w0 > max_w2:
                    ratio = max_w2 / w0
                    img2 = img2.resize((max_w2, int(h0 * ratio)), Image.LANCZOS)
                self.qr_photo2 = ImageTk.PhotoImage(img2)
                tk.Label(main, image=self.qr_photo2, bg="#F5F5F5").pack(pady=(3, 0))
                tk.Label(main, text="备用联系人（扫码加好友）", font=("Microsoft YaHei", 8),
                         bg="#F5F5F5", fg="#888888").pack(pady=(0, 5))
                tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=30, pady=(0, 5))
        else:
            tk.Label(main, text="📱 微信联系购买：kerr2008", font=("Microsoft YaHei", 10, "bold"),
                     bg="#F5F5F5", fg="#E65100").pack(pady=(5, 10))'''

new_qr_section = '''        # 分隔线
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
                     bg="#F5F5F5", fg="#888888").pack(pady=(0, 5))'''

content = content.replace(old_qr_section, new_qr_section)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('license.py QR section updated OK')
