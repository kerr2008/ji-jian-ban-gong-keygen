path = r'C:\Users\popoz\Documents\赚钱项目咸鱼\极简办公\main.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update _show_customer_service — same QR+wechat layout
old_cs = '''    def _show_customer_service(self):
        """客服窗口 - 显示微信二维码和备用二维码"""
        dialog = tk.Toplevel(self.root)
        dialog.title("💬 联系客服")
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
        
        tk.Label(main, text="💬 联系客服", font=("Microsoft YaHei", 16, "bold"),
                 bg="#F5F5F5", fg="#1A73E8").pack(pady=(0, 5))
        tk.Label(main, text="购买/续费/使用问题 扫码咨询",
                 font=("Microsoft YaHei", 9), bg="#F5F5F5", fg="#666666").pack(pady=(0, 10))
        
        # 微信二维码（主）
        self._show_qr_code(main, "微信二维码.jpg", "📱 主客服微信（扫码添加）")
        
        # 分隔线
        tk.Frame(main, bg="#E0E0E0", height=1).pack(fill="x", padx=10, pady=8)
        
        # 备用二维码
        self._show_qr_code(main, "备用二维码.jpg", "📱 备用客服（扫码添加好友）")
        
        # 微信号文字
        tk.Label(main, text="微信号：kerr2008",
                 font=("Microsoft YaHei", 9, "bold"),
                 bg="#F5F5F5", fg="#E65100").pack(pady=(5, 2))
        tk.Label(main, text="添加时请备注：极简办公",
                 font=("Microsoft YaHei", 8),
                 bg="#F5F5F5", fg="#666666").pack()
        
        tk.Button(main, text="关闭", command=dialog.destroy,
                  bg="#1A73E8", fg="white",
                  font=("Microsoft YaHei", 10), relief="flat",
                  padx=20, pady=4, cursor="hand2").pack(pady=(5, 0))
        
        dialog.wait_window()'''

new_cs = '''    def _show_customer_service(self):
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
        
        dialog.wait_window()'''

content = content.replace(old_cs, new_cs)

# 2. Add _renew_activate and _copy_text helper methods
# Find the position after _show_qr_code method
old_qr_end = '''        except:
            tk.Label(parent, text="📱 微信联系：kerr2008",
                     font=("Microsoft YaHei", 10, "bold"),
                     bg="#F5F5F5", fg="#E65100").pack(pady=(3, 3))

    def _create_nav_button'''

new_qr_end = '''        except:
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
            messagebox.showinfo("成功", "🎉 激活成功！" + msg + "\n\n授权码已绑定此设备\n可继续在其他电脑上使用同一授权码")
            dialog.destroy()
            # 刷新界面
            self._switch_to(self.current_key)
        else:
            messagebox.showerror("失败", "解锁码无效，请检查后重试\n\n如需购买请联系微信：\nkerr2008 或 xin012169")
    
    def _create_nav_button'''

content = content.replace(old_qr_end, new_qr_end)

# 3. Update _show_buy_info pricing
content = content.replace(
    '🪌 永久授权  99元\n\n            "┌───附赠───┐\n            "🎵 购买即赠：\n            "  路 Excel 模板包（50个）\n            "  路 合同模板包（20个）\n            "  路 终身免费升级',
    '🪌 永久授权  199元（重装可再次申领）\n一个授权码可绑定多台电脑\n\n            "┌───附赠───┐\n            "🎵 购买即赠：\n            "  路 Excel 模板包（50个）\n            "  路 合同模板包（20个）\n            "  路 终身免费升级\n            "  路 多设备授权支持'
)

# 4. Update the bottom label
content = content.replace(
    '7天体验 9.9元 | 30天 29.9元 | 永久 99元',
    '7天9.9 | 30天29.9 | 永久199元(多设备)'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('main.py customer service + helpers updated OK')
