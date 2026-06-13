# -*- coding: utf-8 -*-
"""
图片处理模块
批量压缩 / 格式转换 / 缩放裁剪
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


def compress_images(files, output_dir, quality=80, progress_callback=None):
    """批量压缩图片"""
    from PIL import Image
    total = len(files)
    results = []
    for i, fp in enumerate(files):
        try:
            img = Image.open(fp)
            ext = Path(fp).suffix.lower()
            out_name = Path(fp).stem + "_压缩" + ext
            out_path = os.path.join(output_dir, out_name)
            if ext in (".jpg", ".jpeg"):
                img.save(out_path, "JPEG", quality=quality, optimize=True)
            elif ext == ".png":
                img.save(out_path, "PNG", optimize=True)
            elif ext == ".webp":
                img.save(out_path, "WEBP", quality=quality)
            else:
                img.save(out_path, quality=quality)
            old_size = os.path.getsize(fp)
            new_size = os.path.getsize(out_path)
            ratio = (1 - new_size / old_size) * 100 if old_size > 0 else 0
            results.append({"文件": os.path.basename(fp), "压缩前": old_size, "压缩后": new_size, "缩小": "{:.1f}%".format(ratio)})
        except Exception as e:
            results.append({"文件": os.path.basename(fp), "错误": str(e)})
        if progress_callback:
            progress_callback(i + 1, total)
    return results


def convert_format(files, output_dir, target_format, progress_callback=None):
    """批量转换图片格式"""
    from PIL import Image
    total = len(files)
    results = []
    for i, fp in enumerate(files):
        try:
            img = Image.open(fp)
            out_name = Path(fp).stem + target_format
            out_path = os.path.join(output_dir, out_name)
            img.save(out_path)
            results.append({"源文件": os.path.basename(fp), "输出": out_name})
        except Exception as e:
            results.append({"源文件": os.path.basename(fp), "错误": str(e)})
        if progress_callback:
            progress_callback(i + 1, total)
    return results


def resize_images(files, output_dir, width, height, keep_ratio=True, progress_callback=None):
    """批量缩放图片"""
    from PIL import Image
    total = len(files)
    results = []
    for i, fp in enumerate(files):
        try:
            img = Image.open(fp)
            if keep_ratio:
                img.thumbnail((width, height), Image.LANCZOS)
            else:
                img = img.resize((width, height), Image.LANCZOS)
            out_name = Path(fp).stem + "_缩放" + Path(fp).suffix
            out_path = os.path.join(output_dir, out_name)
            img.save(out_path)
            results.append({"文件": os.path.basename(fp), "新尺寸": "{}x{}".format(img.width, img.height)})
        except Exception as e:
            results.append({"文件": os.path.basename(fp), "错误": str(e)})
        if progress_callback:
            progress_callback(i + 1, total)
    return results


def _get_files_from_list(file_list):
    """从文件列表中提取图片文件"""
    return [f for f in file_list if Path(f).suffix.lower() in SUPPORTED_FORMATS]


class ImageToolFrame(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.selected_files = []
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self.last_output = None
        self._build_ui()

    def _build_ui(self):
        c = self.theme.colors
        tk.Label(self, text="图片处理 — 批量压缩 / 格式转换 / 缩放",
                 font=("Microsoft YaHei", 11, "bold"),
                 bg=c["panel_bg"], fg=c["fg"], anchor="w").pack(fill="x", pady=(0, 15))

        # 模式
        mode_frame = tk.Frame(self, bg=c["panel_bg"])
        mode_frame.pack(fill="x", pady=(0, 10))
        tk.Label(mode_frame, text="操作：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.mode = tk.StringVar(value="compress")
        for text, val in [("批量压缩", "compress"), ("格式转换", "convert"), ("缩放裁剪", "resize")]:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode, value=val,
                           bg=c["panel_bg"], fg=c["fg"], selectcolor=c["input_bg"],
                           font=("Microsoft YaHei", 9),
                           activebackground=c["panel_bg"], activeforeground=c["fg"],
                           command=self._on_mode_change).pack(side="left", padx=(8, 0))

        # 文件选择
        ff = tk.Frame(self, bg=c["panel_bg"])
        ff.pack(fill="x", pady=(0, 5))
        tk.Label(ff, text="选择图片：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.file_label = tk.Label(ff, text="未选择", bg=c["panel_bg"], fg=c["disabled_fg"],
                                    font=("Microsoft YaHei", 9))
        self.file_label.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.btn_select = tk.Button(ff, text="📁 选择文件",
                                    command=self._select_files,
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
        self._build_compress_params()

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

        # 进度
        pf = tk.Frame(self, bg=c["panel_bg"])
        pf.pack(fill="x", pady=(5, 5))
        self.progress = ttk.Progressbar(pf, variable=self.progress_var, maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 3))
        self.status_label = tk.Label(pf, textvariable=self.status_var,
                                     bg=c["panel_bg"], fg=c["disabled_fg"], font=("Microsoft YaHei", 8))
        self.status_label.pack(anchor="w")

        # 结果
        rf = tk.LabelFrame(self, text="执行结果", bg=c["panel_bg"], fg=c["fg"],
                            font=("Microsoft YaHei", 9), padx=5, pady=5)
        rf.pack(fill="both", expand=True)
        self.result_text = tk.Text(rf, bg=c["input_bg"], fg=c["fg"],
                                    font=("Consolas", 9), wrap="word",
                                    relief="flat", padx=5, pady=5, state="disabled")
        self.result_text.pack(fill="both", expand=True)

    def _build_compress_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="压缩质量：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.quality = tk.Scale(self.param_content, from_=10, to_=100, orient="horizontal",
                                 bg=c["panel_bg"], fg=c["fg"], length=200,
                                 highlightbackground=c["panel_bg"])
        self.quality.set(80)
        self.quality.pack(side="left", padx=(5, 10))
        tk.Label(self.param_content, text="（数值越低文件越小）",
                 bg=c["panel_bg"], fg=c["disabled_fg"], font=("Microsoft YaHei", 8)).pack(side="left")

    def _build_convert_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="目标格式：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.target_fmt = tk.StringVar(value=".png")
        ttk.Combobox(self.param_content, textvariable=self.target_fmt,
                      values=[".png", ".jpg", ".jpeg", ".webp", ".bmp"],
                      state="readonly", width=8).pack(side="left", padx=(5, 0))

    def _build_resize_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="宽度：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.rw = tk.Entry(self.param_content, bg=c["input_bg"], fg=c["fg"],
                            font=("Microsoft YaHei", 9), relief="flat", bd=1, width=6)
        self.rw.insert(0, "1920")
        self.rw.pack(side="left", padx=(5, 15))
        tk.Label(self.param_content, text="高度：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.rh = tk.Entry(self.param_content, bg=c["input_bg"], fg=c["fg"],
                            font=("Microsoft YaHei", 9), relief="flat", bd=1, width=6)
        self.rh.insert(0, "1080")
        self.rh.pack(side="left", padx=(5, 15))
        self.keep_ratio = tk.BooleanVar(value=True)
        tk.Checkbutton(self.param_content, text="保持比例", variable=self.keep_ratio,
                       bg=c["panel_bg"], fg=c["fg"], selectcolor=c["input_bg"],
                       font=("Microsoft YaHei", 9),
                       activebackground=c["panel_bg"]).pack(side="left")

    def _clear_params(self):
        for w in self.param_content.winfo_children():
            w.destroy()

    def _on_mode_change(self):
        {
            "compress": self._build_compress_params,
            "convert": self._build_convert_params,
            "resize": self._build_resize_params,
        }.get(self.mode.get(), lambda: None)()

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = files
            self.file_label.config(text=str(len(files)) + " 个文件", fg=self.theme.get("fg"))
            self.btn_start.config(state="normal")

    def _start_process(self):
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择文件")
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
            files = _get_files_from_list(self.selected_files)
            if not files:
                log("❌ 未找到支持的图片文件")
                return

            log("处理 " + str(len(files)) + " 个文件...")

            if mode == "compress":
                q = self.quality.get()
                results = compress_images(files, output_dir, q, cb)
                log("✅ 压缩完成！")
                for r in results:
                    if "缩小" in r:
                        log("  {}: {} → {} (缩小{})".format(r["文件"], r["压缩前"], r["压缩后"], r["缩小"]))

            elif mode == "convert":
                fmt = self.target_fmt.get()
                results = convert_format(files, output_dir, fmt, cb)
                log("✅ 格式转换完成！共 {} 个文件".format(len(results)))
                for r in results[:10]:
                    log("  {} → {}".format(r["源文件"], r["输出"]))

            elif mode == "resize":
                w = int(self.rw.get() or 1920)
                h = int(self.rh.get() or 1080)
                kr = self.keep_ratio.get()
                results = resize_images(files, output_dir, w, h, kr, cb)
                log("✅ 缩放完成！")
                for r in results[:10]:
                    log("  {} → {}".format(r["文件"], r.get("新尺寸", "")))

            self.last_output = output_dir
            self.after(0, lambda: self.btn_open.config(state="normal"))

        except Exception as e:
            log("❌ 错误: " + str(e))

        self.progress_var.set(100)
        self.after(0, lambda: self.btn_start.config(state="normal", text="🚀 开始处理"))
        self.after(0, lambda: self.status_var.set("处理完成 ✅"))

    def _append_log(self, text):
        self.result_text.config(state="normal")
        self.result_text.insert("end", text + "\n")
        self.result_text.see("end")
        self.result_text.config(state="disabled")

    def _open_last(self):
        if self.last_output and os.path.exists(self.last_output):
            os.startfile(self.last_output)

    def apply_theme(self):
        try:
            self.result_text.config(bg=self.theme.colors["input_bg"], fg=self.theme.colors["fg"])
        except:
            pass