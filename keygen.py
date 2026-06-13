# -*- coding: utf-8 -*-
"""
极简办公 — 解锁码生成器（只有你可以用）
生成：基于机器码+天数的唯一解锁码
打包成独立 exe，你双击使用
"""

import os
import sys
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime

SECRET_KEY = b"JJBG_2026_@kerr2008#Secret!"

def generate_license(machine_code, days):
    raw = (machine_code + str(days) + "|JJBG_2026").encode("utf-8")
    code = hashlib.sha256(raw + SECRET_KEY).hexdigest()[:24].upper()
    return "-".join([code[i:i+4] for i in range(0, 24, 4)])


class KeygenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("极简办公 - 解锁码生成器")
        self.root.geometry("550x500")
        self.root.configure(bg="#F5F5F5")
        self.root.resizable(False, False)
        
        # 居中
        self.root.update_idletasks()
        w, h = 550, 500
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry("{}x{}+{}+{}".format(w, h, (sw-w)//2, (sh-h)//2))
        
        main = tk.Frame(self.root, bg="#F5F5F5", padx=20, pady=15)
        main.pack(fill="both", expand=True)
        
        # 标题
        tk.Label(main, text="🔑 极简办公 · 解锁码生成器(多设备)", 
                 font=("Microsoft YaHei", 14, "bold"),
                 bg="#F5F5F5", fg="#D93025").pack(pady=(0, 15))
        
        # 机器码
        tk.Label(main, text="用户机器码：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333", anchor="w").pack(fill="x")
        self.entry_machine = tk.Entry(main, font=("Consolas", 11),
                                       bg="#FFF", fg="#333",
                                       relief="solid", bd=1)
        self.entry_machine.pack(fill="x", pady=(0, 10), ipady=3)
        
        # 有效期选择
        tk.Label(main, text="授权期限：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333", anchor="w").pack(fill="x")
        
        days_frame = tk.Frame(main, bg="#F5F5F5")
        days_frame.pack(fill="x", pady=(0, 10))
        
        self.days_var = tk.StringVar(value="7")
        days_opts = [("7天体验", "7"), ("30天标准", "30"), ("365天年卡", "365"), ("永久", "0")]
        for text, val in days_opts:
            rb = tk.Radiobutton(days_frame, text=text, variable=self.days_var, value=val,
                                bg="#F5F5F5", fg="#333", selectcolor="#FFF",
                                font=("Microsoft YaHei", 9),
                                activebackground="#F5F5F5")
            rb.pack(side="left", padx=(0, 10))
        
        # 生成按钮
        btn_frame = tk.Frame(main, bg="#F5F5F5")
        btn_frame.pack(fill="x", pady=(5, 10))
        
        self.btn_gen = tk.Button(btn_frame, text="🚀 生 成 解 锁 码",
                                 command=self._generate,
                                 bg="#D93025", fg="white",
                                 font=("Microsoft YaHei", 12, "bold"),
                                 relief="flat", padx=20, pady=8, cursor="hand2")
        self.btn_gen.pack(side="left", padx=(0, 10))
        
        self.btn_copy = tk.Button(btn_frame, text="📋 复制结果",
                                  command=self._copy_result,
                                  bg="#E8E8E8", fg="#333",
                                  font=("Microsoft YaHei", 9),
                                  relief="flat", padx=12, pady=4, cursor="hand2",
                                  state="disabled")
        self.btn_copy.pack(side="left")
        
        # 结果显示
        tk.Label(main, text="生成结果：", font=("Microsoft YaHei", 9),
                 bg="#F5F5F5", fg="#333", anchor="w").pack(fill="x")
        
        self.result_text = scrolledtext.ScrolledText(main, height=8,
                                                      font=("Consolas", 11),
                                                      bg="#1E1E1E", fg="#4FC3F7",
                                                      relief="flat", bd=2, padx=8, pady=8)
        self.result_text.pack(fill="both", expand=True)
        
        # 底部提示
        tk.Label(main, text="提示：一个解锁码可绑定多台设备，用户在不同电脑输入同一解锁码即可",
                 font=("Microsoft YaHei", 8),
                 bg="#F5F5F5", fg="#999", anchor="w").pack(fill="x", pady=(5, 0))
        
        # 预填充示例
        self.entry_machine.insert(0, "ABCD-1234-EF56-7890")
    
    def _generate(self):
        machine = self.entry_machine.get().strip().upper()
        days = int(self.days_var.get())
        
        if not machine or len(machine) < 10:
            messagebox.showwarning("提示", "请输入有效的机器码（至少10位）")
            return
        
        code = generate_license(machine, days)
        
        days_text = {7:"7天体验", 30:"30天标准", 365:"365天年卡", 0:"永久授权"}
        label = days_text.get(days, str(days) + "天")
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "=" * 42 + "\n")
        self.result_text.insert("end", "  极简办公 · 解锁码\n")
        self.result_text.insert("end", "=" * 42 + "\n\n")
        self.result_text.insert("end", "生成时间: {}\n".format(now))
        self.result_text.insert("end", "机器码:   {}\n".format(machine))
        self.result_text.insert("end", "授权类型: {}\n\n".format(label))
        self.result_text.insert("end", "解锁码:\n")
        self.result_text.insert("end", "  {}\n\n".format(code))
        
        if days == 0:
            self.result_text.insert("end", "说明: 永久有效，重装系统可再次申领")
            self.result_text.insert("end", "\n一个授权码可绑定多台设备\n")
        else:
            self.result_text.insert("end", "说明: 自激活之日起{}内有效\n".format(label))
            self.result_text.insert("end", "说明: 一个授权码可绑定多台设备\n")
        
        self.result_text.insert("end", "=" * 42 + "\n")
        
        self.last_code = code
        self.btn_copy.config(state="normal")
    
    def _copy_result(self):
        if hasattr(self, "last_code"):
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_code)
            messagebox.showinfo("已复制", "解锁码已复制到剪贴板\n可直接 Ctrl+V 发给用户")


def main():
    root = tk.Tk()
    app = KeygenApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()