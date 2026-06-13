# -*- coding: utf-8 -*-
"""
文件管理模块
批量重命名 / 文件夹结构导出 / 重复文件查找
"""

import os
import hashlib
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading


def rename_files(folder, rules, preview=False, progress_callback=None):
    """批量重命名
    rules: {"prefix":"", "suffix":"", "replace_old":"", "replace_new":"", "start_num":1, "padding":2}
    """
    files = sorted([f for f in Path(folder).iterdir() if f.is_file()])
    total = len(files)
    results = []
    
    prefix = rules.get("prefix", "")
    suffix = rules.get("suffix", "")
    rep_old = rules.get("replace_old", "")
    rep_new = rules.get("replace_new", "")
    start = int(rules.get("start_num", 1))
    padding = int(rules.get("padding", 2))
    
    for i, fp in enumerate(files):
        old_name = fp.name
        stem = fp.stem
        ext = fp.suffix
        
        # 应用替换
        if rep_old:
            stem = stem.replace(rep_old, rep_new)
        
        # 应用编号
        num = str(start + i).zfill(padding)
        new_name = prefix + stem + suffix + "_" + num + ext
        
        new_path = fp.parent / new_name
        
        if not preview:
            try:
                fp.rename(new_path)
            except Exception as e:
                results.append({"旧名称": old_name, "新名称": new_name, "状态": "失败: " + str(e)})
                continue
        
        results.append({"旧名称": old_name, "新名称": new_name, "状态": "预览" if preview else "成功"})
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    return results


def export_folder_tree(folder, output_path):
    """导出文件夹结构为TXT"""
    lines = []
    root_name = os.path.basename(folder) or folder
    
    lines.append("文件夹结构: " + root_name)
    lines.append("导出时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    lines.append("=" * 50)
    lines.append("")
    
    total_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk(folder):
        level = root.replace(folder, "").count(os.sep)
        indent = "  " * level
        lines.append(indent + "📁 " + os.path.basename(root) + "/")
        sub_indent = "  " * (level + 1)
        for file in files:
            fp = os.path.join(root, file)
            try:
                size = os.path.getsize(fp)
                total_size += size
                total_files += 1
                size_str = format_size(size)
                lines.append(sub_indent + "📄 " + file + "  (" + size_str + ")")
            except:
                lines.append(sub_indent + "📄 " + file)
    
    lines.append("")
    lines.append("=" * 50)
    lines.append("总计: {} 个文件, {}".format(total_files, format_size(total_size)))
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    return total_files, total_size


def find_duplicates(folder, method="name", progress_callback=None):
    """查找重复文件
    method: "name" 按文件名, "size" 按大小, "md5" 按内容
    """
    from collections import defaultdict
    
    groups = defaultdict(list)
    total = 0
    
    for root, dirs, files in os.walk(folder):
        for file in files:
            fp = os.path.join(root, file)
            try:
                if method == "name":
                    key = file.lower()
                elif method == "size":
                    key = os.path.getsize(fp)
                    total += 1
                else:  # md5
                    key = file_hash(fp)
                
                groups[key].append(fp)
                total += 1
            except:
                continue
    
    # 只保留有重复的组
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    return duplicates


def file_hash(filepath):
    """计算文件 MD5"""
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def format_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return "{:.1f} {}".format(size, unit)
        size /= 1024
    return "{:.1f} TB".format(size)


class FileToolFrame(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.selected_folder = ""
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self.last_output = None
        self._build_ui()

    def _build_ui(self):
        c = self.theme.colors
        tk.Label(self, text="文件管理 — 批量重命名 / 导出结构 / 查找重复",
                 font=("Microsoft YaHei", 11, "bold"),
                 bg=c["panel_bg"], fg=c["fg"], anchor="w").pack(fill="x", pady=(0, 15))

        # 模式
        mf = tk.Frame(self, bg=c["panel_bg"])
        mf.pack(fill="x", pady=(0, 10))
        tk.Label(mf, text="操作：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.mode = tk.StringVar(value="rename")
        for text, val in [("批量重命名", "rename"), ("导出结构", "tree"), ("查找重复", "dup")]:
            tk.Radiobutton(mf, text=text, variable=self.mode, value=val,
                           bg=c["panel_bg"], fg=c["fg"], selectcolor=c["input_bg"],
                           font=("Microsoft YaHei", 9),
                           activebackground=c["panel_bg"], activeforeground=c["fg"],
                           command=self._on_mode_change).pack(side="left", padx=(8, 0))

        # 文件夹选择
        ff = tk.Frame(self, bg=c["panel_bg"])
        ff.pack(fill="x", pady=(0, 5))
        tk.Label(ff, text="选择文件夹：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.folder_label = tk.Label(ff, text="未选择", bg=c["panel_bg"], fg=c["disabled_fg"],
                                      font=("Microsoft YaHei", 9))
        self.folder_label.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.btn_select = tk.Button(ff, text="📁 选择文件夹",
                                    command=self._select_folder,
                                    bg=c["accent"], fg="white",
                                    font=("Microsoft YaHei", 9),
                                    relief="flat", padx=12, pady=3, cursor="hand2")
        self.btn_select.pack(side="right")

        # 参数
        self.param_frame = tk.LabelFrame(self, text="参数设置", bg=c["panel_bg"], fg=c["fg"],
                                          font=("Microsoft YaHei", 9), padx=10, pady=5)
        self.param_frame.pack(fill="x", pady=(0, 10))
        self.param_content = tk.Frame(self.param_frame, bg=c["panel_bg"])
        self.param_content.pack(fill="x")
        self._build_rename_params()

        # 操作
        af = tk.Frame(self, bg=c["panel_bg"])
        af.pack(fill="x", pady=(5, 10))
        self.btn_start = tk.Button(af, text="🚀 开始处理",
                                   command=self._start_process,
                                   bg=c["success"], fg="white",
                                   font=("Microsoft YaHei", 10, "bold"),
                                   relief="flat", padx=20, pady=5,
                                   cursor="hand2", state="disabled")
        self.btn_start.pack(side="left", padx=(0, 10))
        self.btn_open = tk.Button(af, text="📂 打开输出文件夹",
                                  command=lambda: self._open_last(),
                                  bg=c["sidebar_bg"], fg=c["fg"],
                                  font=("Microsoft YaHei", 9),
                                  relief="flat", padx=12, pady=3,
                                  cursor="hand2", state="disabled")
        self.btn_open.pack(side="left")

        # 进度+结果
        pf = tk.Frame(self, bg=c["panel_bg"])
        pf.pack(fill="x", pady=(5, 5))
        self.progress = ttk.Progressbar(pf, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 3))
        self.status_label = tk.Label(pf, textvariable=self.status_var,
                                     bg=c["panel_bg"], fg=c["disabled_fg"], font=("Microsoft YaHei", 8))
        self.status_label.pack(anchor="w")

        rf = tk.LabelFrame(self, text="执行结果", bg=c["panel_bg"], fg=c["fg"],
                            font=("Microsoft YaHei", 9), padx=5, pady=5)
        rf.pack(fill="both", expand=True)
        self.result_text = tk.Text(rf, bg=c["input_bg"], fg=c["fg"],
                                    font=("Consolas", 9), wrap="word",
                                    relief="flat", padx=5, pady=5, state="disabled")
        self.result_text.pack(fill="both", expand=True)

    def _build_rename_params(self):
        self._clear_params()
        c = self.theme.colors
        row = tk.Frame(self.param_content, bg=c["panel_bg"])
        row.pack(fill="x", pady=2)
        tk.Label(row, text="前缀：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.prefix = tk.Entry(row, bg=c["input_bg"], fg=c["fg"],
                                font=("Microsoft YaHei", 9), relief="flat", bd=1, width=10)
        self.prefix.pack(side="left", padx=(5, 20))
        tk.Label(row, text="后缀：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.suffix = tk.Entry(row, bg=c["input_bg"], fg=c["fg"],
                                font=("Microsoft YaHei", 9), relief="flat", bd=1, width=10)
        self.suffix.pack(side="left", padx=(5, 0))

        row2 = tk.Frame(self.param_content, bg=c["panel_bg"])
        row2.pack(fill="x", pady=2)
        tk.Label(row2, text="替换：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.replace_old = tk.Entry(row2, bg=c["input_bg"], fg=c["fg"],
                                     font=("Microsoft YaHei", 9), relief="flat", bd=1, width=8)
        self.replace_old.pack(side="left", padx=(5, 5))
        tk.Label(row2, text="→", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.replace_new = tk.Entry(row2, bg=c["input_bg"], fg=c["fg"],
                                     font=("Microsoft YaHei", 9), relief="flat", bd=1, width=8)
        self.replace_new.pack(side="left", padx=(5, 20))
        tk.Label(row2, text="起始编号：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.start_num = tk.Entry(row2, bg=c["input_bg"], fg=c["fg"],
                                   font=("Microsoft YaHei", 9), relief="flat", bd=1, width=4)
        self.start_num.insert(0, "1")
        self.start_num.pack(side="left", padx=(5, 10))
        tk.Label(row2, text="位数：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.padding = tk.Entry(row2, bg=c["input_bg"], fg=c["fg"],
                                 font=("Microsoft YaHei", 9), relief="flat", bd=1, width=3)
        self.padding.insert(0, "2")
        self.padding.pack(side="left", padx=(5, 0))

    def _build_tree_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="选择文件夹后点击开始，自动生成目录结构TXT",
                 bg=c["panel_bg"], fg=c["disabled_fg"], font=("Microsoft YaHei", 9)).pack(side="left")

    def _build_dup_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="对比方式：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.dup_method = tk.StringVar(value="name")
        ttk.Combobox(self.param_content, textvariable=self.dup_method,
                      values=["按文件名", "按文件大小", "按内容MD5"], state="readonly",
                      width=15).pack(side="left", padx=(5, 0))
        tk.Label(self.param_content, text="（按内容最准确但较慢）",
                 bg=c["panel_bg"], fg=c["disabled_fg"], font=("Microsoft YaHei", 8)).pack(side="left", padx=(5, 0))

    def _clear_params(self):
        for w in self.param_content.winfo_children():
            w.destroy()

    def _on_mode_change(self):
        {
            "rename": self._build_rename_params,
            "tree": self._build_tree_params,
            "dup": self._build_dup_params,
        }.get(self.mode.get(), lambda: None)()

    def _select_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=folder, fg=self.theme.get("fg"))
            self.btn_start.config(state="normal")

    def _start_process(self):
        if not self.selected_folder:
            messagebox.showwarning("提示", "请先选择文件夹")
            return
        self.btn_start.config(state="disabled", text="⏳ 处理中...")
        self.progress_var.set(0)
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.config(state="disabled")
        thread = threading.Thread(target=self._process, daemon=True)
        thread.start()

    def _process(self):
        output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "极简办公_输出")
        os.makedirs(output_dir, exist_ok=True)

        def log(msg):
            self.after(0, lambda: self._append_log(msg))

        def cb(c, t):
            self.after(0, lambda: self.progress_var.set(c / t * 100))

        try:
            mode = self.mode.get()
            folder = self.selected_folder

            if mode == "rename":
                rules = {
                    "prefix": self.prefix.get(),
                    "suffix": self.suffix.get(),
                    "replace_old": self.replace_old.get(),
                    "replace_new": self.replace_new.get(),
                    "start_num": self.start_num.get() or "1",
                    "padding": self.padding.get() or "2",
                }
                results = rename_files(folder, rules, False, cb)
                ok = sum(1 for r in results if r["状态"] == "成功")
                fail = sum(1 for r in results if "失败" in r["状态"])
                log("✅ 重命名完成！成功 {} 个{}".format(ok, "，失败 " + str(fail) if fail else ""))
                for r in results[:15]:
                    log("  {} → {}".format(r["旧名称"], r["新名称"]))
                if len(results) > 15:
                    log("  ... 共 {} 个".format(len(results)))

            elif mode == "tree":
                out = os.path.join(output_dir, "文件夹结构_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt")
                tf, ts = export_folder_tree(folder, out)
                log("✅ 目录结构已导出！")
                log("  输出: " + os.path.basename(out))
                log("  文件数: " + str(tf) + ", 总大小: " + format_size(ts))
                self.last_output = out

            elif mode == "dup":
                method_map = {"按文件名": "name", "按文件大小": "size", "按内容MD5": "md5"}
                method = method_map.get(self.dup_method.get(), "name")
                log("正在扫描（" + self.dup_method.get() + "）...")
                dups = find_duplicates(folder, method, cb)
                if dups:
                    log("✅ 发现 {} 组重复文件：".format(len(dups)))
                    for key, files in list(dups.items())[:20]:
                        log("  🔁 重复组 ({} 个文件):".format(len(files)))
                        for f in files:
                            log("    📄 " + os.path.relpath(f, folder))
                    if len(dups) > 20:
                        log("  ... 共 {} 组".format(len(dups)))
                    # 导出到文件
                    out = os.path.join(output_dir, "重复文件_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".txt")
                    with open(out, "w", encoding="utf-8") as f:
                        f.write("重复文件查找结果\n")
                        f.write("=" * 40 + "\n\n")
                        for key, files in dups.items():
                            f.write("重复组 ({} 个文件):\n".format(len(files)))
                            for fp in files:
                                f.write("  {}\n".format(fp))
                            f.write("\n")
                    log("  详细报告: " + os.path.basename(out))
                    self.last_output = out
                else:
                    log("✅ 未发现重复文件")

            self.after(0, lambda: self.btn_open.config(state="normal"))

        except Exception as e:
            import traceback
            log("❌ 错误: " + str(e))
            log(traceback.format_exc())

        self.progress_var.set(100)
        self.after(0, lambda: self.btn_start.config(state="normal", text="🚀 开始处理"))
        self.after(0, lambda: self.status_var.set("处理完成 ✅"))

    def _append_log(self, text):
        self.result_text.config(state="normal")
        self.result_text.insert("end", text + "\n")
        self.result_text.see("end")
        self.result_text.config(state="disabled")

    def _open_last(self):
        if self.last_output:
            p = self.last_output
            if os.path.isfile(p):
                os.startfile(os.path.dirname(p))
            else:
                os.startfile(p)

    def apply_theme(self):
        try:
            self.result_text.config(bg=self.theme.colors["input_bg"], fg=self.theme.colors["fg"])
        except:
            pass