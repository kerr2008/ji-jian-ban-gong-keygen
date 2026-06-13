# -*- coding: utf-8 -*-
"""
PDF 工具模块
功能：PDF转Word、PDF转Excel（提取表格）、PDF拆分
依赖：pypdf, reportlab（均为内置，无需额外安装）
"""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading


# ============ PDF 转 Word ============

def pdf_to_word(pdf_path, output_path, progress_callback=None):
    """PDF 转 Word：使用 pdfplumber 提取文本（中文友好）写入 docx"""
    import pdfplumber
    from docx import Document
    from docx.shared import Pt, Inches, Cm
    from docx.oxml.ns import qn


    doc = Document()

    # 设置默认字体为宋体，更兼容中文
    style = doc.styles["Normal"]
    font = style.font
    font.name = "宋体"
    font.size = Pt(10.5)
    # 同时设置中文字体（解决Word中乱码问题）
    rpr = style.element.rPr
    if rpr is None:
        rpr = style.element.get_or_add_rPr()
    rFonts = rpr.find(qn('w:rFonts'))
    if rFonts is None:
        from lxml import etree
        rFonts = etree.SubElement(rpr, qn('w:rFonts'))
    rFonts.set(qn('w:eastAsia'), '宋体')

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            # 提取文字
            text = page.extract_text()
            if text and text.strip():
                p = doc.add_paragraph(text.strip())
                for run in p.runs:
                    run.font.name = '宋体'
                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

            # 提取表格
            tables = page.extract_tables()
            for table_data in tables:
                if not table_data:
                    continue
                table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                table.style = "Table Grid"
                for r_idx, row_data in enumerate(table_data):
                    for c_idx, cell_text in enumerate(row_data):
                        if c_idx < len(table.row_cells(r_idx)):
                            cell = table.row_cells(r_idx)[c_idx]
                            cell.text = str(cell_text or "")
                            for paragraph in cell.paragraphs:
                                for run in paragraph.runs:
                                    run.font.name = '宋体'
                                    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                doc.add_paragraph("")  # 表格后空行

            if progress_callback:
                progress_callback(i + 1, total)

    doc.save(output_path)
    return True


# ============ PDF 转 Excel（提取表格） ============

def pdf_to_excel(pdf_path, output_path, progress_callback=None):
    """PDF 转 Excel：尝试提取页面的表格/行列结构数据"""
    from pypdf import PdfReader
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "提取数据"

    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    row_idx = 1

    for page_num, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text or not text.strip():
            continue

        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试按多个空格或制表符拆分为列
            parts = re.split(r"\s{2,}|\t", line)
            # 如果拆不开，保持为一整行
            for col_idx, part in enumerate(parts):
                cell = ws.cell(row=row_idx, column=col_idx + 1, value=part.strip())
                cell.alignment = Alignment(wrap_text=True)
            row_idx += 1

        # 分隔不同页面
        if page_num < total - 1:
            ws.cell(row=row_idx, column=1, value="--- 第 " + str(page_num + 2) + " 页 ---")
            ws.cell(row=row_idx, column=1).font = Font(bold=True, color="999999")
            row_idx += 1

        if progress_callback:
            progress_callback(page_num + 1, total)

    # 自动调整列宽
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted = min(max_length + 2, 60)
        ws.column_dimensions[col_letter].width = adjusted

    wb.save(output_path)
    return True


# ============ PDF 拆分 ============

def split_pdf(pdf_path, output_dir, mode="all", pages=None, progress_callback=None):
    """PDF 拆分：按页/按范围/每N页一组"""
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(pdf_path)
    total = len(reader.pages)

    files_created = []
    base_name = Path(pdf_path).stem

    if mode == "all":
        # 每页单独一个文件
        for i in range(total):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            out_path = os.path.join(output_dir, base_name + "_第" + str(i + 1) + "页.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            files_created.append(out_path)
            if progress_callback:
                progress_callback(i + 1, total)

    elif mode == "range" and pages:
        # 拆分为指定范围：如 "1-3,5-7"
        ranges = parse_page_ranges(pages, total)
        for idx, (start, end) in enumerate(ranges):
            writer = PdfWriter()
            for p in range(start - 1, end):
                writer.add_page(reader.pages[p])
            out_path = os.path.join(output_dir, base_name + "_第" + str(start) + "-" + str(end) + "页.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            files_created.append(out_path)
            if progress_callback:
                progress_callback(idx + 1, len(ranges))

    elif mode == "every_n":
        # 每N页一组
        n = pages if isinstance(pages, int) else 2
        group_count = (total + n - 1) // n
        for g in range(group_count):
            writer = PdfWriter()
            start = g * n
            end = min(start + n, total)
            for p in range(start, end):
                writer.add_page(reader.pages[p])
            out_path = os.path.join(output_dir, base_name + "_第" + str(g + 1) + "组_第" +
                                     str(start + 1) + "-" + str(end) + "页.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
            files_created.append(out_path)
            if progress_callback:
                progress_callback(g + 1, group_count)

    return files_created


def parse_page_ranges(range_str, total_pages):
    """解析页码范围如 '1-3,5,7-9'"""
    ranges = []
    for part in range_str.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-")
            s, e = int(a.strip()), int(b.strip())
            if s < 1:
                s = 1
            if e > total_pages:
                e = total_pages
            if s <= e:
                ranges.append((s, e))
        else:
            p = int(part)
            if 1 <= p <= total_pages:
                ranges.append((p, p))
    return ranges


# ============ GUI 界面 ============

def _get_output_dir():
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "闲鱼工具箱_输出")
    os.makedirs(d, exist_ok=True)
    return d


class PdfToolsFrame(ttk.Frame):
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

        header = tk.Label(self, text="PDF 工具箱 — 转 Word / 转 Excel / 拆分",
                          font=("Microsoft YaHei", 11, "bold"),
                          bg=c["panel_bg"], fg=c["fg"], anchor="w")
        header.pack(fill="x", pady=(0, 15))

        # 模式选择
        mode_frame = tk.Frame(self, bg=c["panel_bg"])
        mode_frame.pack(fill="x", pady=(0, 10))
        tk.Label(mode_frame, text="操作：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")

        self.mode = tk.StringVar(value="t_word")
        modes = [("PDF → Word", "t_word"), ("PDF → Excel", "t_excel"), ("PDF 拆分", "split")]
        for text, val in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode, value=val,
                                bg=c["panel_bg"], fg=c["fg"], selectcolor=c["input_bg"],
                                font=("Microsoft YaHei", 9),
                                activebackground=c["panel_bg"], activeforeground=c["fg"],
                                command=self._on_mode_change)
            rb.pack(side="left", padx=(8, 0))

        # 文件选择
        file_frame = tk.Frame(self, bg=c["panel_bg"])
        file_frame.pack(fill="x", pady=(0, 5))
        tk.Label(file_frame, text="选择 PDF 文件：", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.file_label = tk.Label(file_frame, text="未选择",
                                    bg=c["panel_bg"], fg=c["disabled_fg"],
                                    font=("Microsoft YaHei", 9))
        self.file_label.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.btn_select = tk.Button(file_frame, text="📁 选择文件",
                                    command=self._select_files,
                                    bg=c["accent"], fg="white",
                                    font=("Microsoft YaHei", 9),
                                    relief="flat", padx=12, pady=3, cursor="hand2")
        self.btn_select.pack(side="right")

        # 参数设置
        self.param_frame = tk.LabelFrame(self, text="参数设置",
                                          bg=c["panel_bg"], fg=c["fg"],
                                          font=("Microsoft YaHei", 9), padx=10, pady=5)
        self.param_frame.pack(fill="x", pady=(0, 10))
        self.param_content = tk.Frame(self.param_frame, bg=c["panel_bg"])
        self.param_content.pack(fill="x")
        self._build_default_params()

        # 操作
        action_frame = tk.Frame(self, bg=c["panel_bg"])
        action_frame.pack(fill="x", pady=(5, 10))
        self.btn_start = tk.Button(action_frame, text="🚀 开始处理",
                                   command=self._start_process,
                                   bg=c["success"], fg="white",
                                   font=("Microsoft YaHei", 10, "bold"),
                                   relief="flat", padx=20, pady=5,
                                   cursor="hand2", state="disabled")
        self.btn_start.pack(side="left", padx=(0, 10))
        self.btn_open = tk.Button(action_frame, text="📂 打开输出文件夹",
                                  command=self._open_output,
                                  bg=c["sidebar_bg"], fg=c["fg"],
                                  font=("Microsoft YaHei", 9),
                                  relief="flat", padx=12, pady=3,
                                  cursor="hand2", state="disabled")
        self.btn_open.pack(side="left")

        # 进度
        progress_frame = tk.Frame(self, bg=c["panel_bg"])
        progress_frame.pack(fill="x", pady=(5, 5))
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                        maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 3))
        self.status_label = tk.Label(progress_frame, textvariable=self.status_var,
                                     bg=c["panel_bg"], fg=c["disabled_fg"],
                                     font=("Microsoft YaHei", 8))
        self.status_label.pack(anchor="w")

        # 结果
        result_frame = tk.LabelFrame(self, text="执行结果",
                                      bg=c["panel_bg"], fg=c["fg"],
                                      font=("Microsoft YaHei", 9), padx=5, pady=5)
        result_frame.pack(fill="both", expand=True)
        self.result_text = tk.Text(result_frame, bg=c["input_bg"], fg=c["fg"],
                                   font=("Consolas", 9), wrap="word",
                                   relief="flat", padx=5, pady=5, state="disabled")
        self.result_text.pack(fill="both", expand=True)

    def _build_default_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="转换模式：将 PDF 中的文本内容提取到 Word 文档中",
                 bg=c["panel_bg"], fg=c["disabled_fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")

    def _build_split_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="拆分方式：",
                 bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")

        self.split_mode = tk.StringVar(value="all")
        sm = ttk.Combobox(self.param_content, textvariable=self.split_mode,
                          values=["每页拆一个", "每N页一组", "指定页码范围"], state="readonly",
                          width=15)
        sm.pack(side="left", padx=(5, 10))
        sm.bind("<<ComboboxSelected>>", self._on_split_mode_change)

        tk.Label(self.param_content, text="", bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.split_param = tk.Entry(self.param_content, bg=c["input_bg"], fg=c["fg"],
                                    font=("Microsoft YaHei", 9),
                                    relief="flat", bd=1, width=20)
        self.split_param.insert(0, "2")
        self.split_param.pack(side="left", padx=(5, 0))

        self.split_hint = tk.Label(self.param_content,
                                    text="（每组页数）",
                                    bg=c["panel_bg"], fg=c["disabled_fg"],
                                    font=("Microsoft YaHei", 8))
        self.split_hint.pack(side="left", padx=(5, 0))

    def _on_split_mode_change(self, event=None):
        mode = self.split_mode.get()
        if mode == "每页拆一个":
            self.split_param.config(state="disabled")
            self.split_hint.config(text="（自动每页一个文件）")
        elif mode == "每N页一组":
            self.split_param.config(state="normal")
            self.split_param.delete(0, "end")
            self.split_param.insert(0, "2")
            self.split_hint.config(text="（每组页数）")
        elif mode == "指定页码范围":
            self.split_param.config(state="normal")
            self.split_param.delete(0, "end")
            self.split_param.insert(0, "1-3,5,7-9")
            self.split_hint.config(text="（如 1-3,5,7-9）")

    def _clear_params(self):
        for w in self.param_content.winfo_children():
            w.destroy()

    def _on_mode_change(self):
        mode = self.mode.get()
        if mode == "split":
            self._build_split_params()
        else:
            self._build_default_params()

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="选择 PDF 文件",
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = files
            names = [os.path.basename(f) for f in files]
            self.file_label.config(
                text=str(len(files)) + " 个文件: " + "; ".join(names[:3]) + ("..." if len(names) > 3 else ""),
                fg=self.theme.get("fg"))
            self.btn_start.config(state="normal")

    def _start_process(self):
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择 PDF 文件")
            return
        self.btn_start.config(state="disabled", text="⏳ 处理中...")
        self.progress_var.set(0)
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.config(state="disabled")
        thread = threading.Thread(target=self._process, daemon=True)
        thread.start()

    def _process(self):
        mode = self.mode.get()
        output_dir = _get_output_dir()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_files = len(self.selected_files)

        def log(msg):
            self.after(0, lambda: self._append_log(msg))

        try:
            for fi, fp in enumerate(self.selected_files):
                base = Path(fp).stem
                log("(" + str(fi + 1) + "/" + str(total_files) + ") 处理: " + os.path.basename(fp))

                def make_progress(file_idx):
                    def cb(current, total):
                        pct = (file_idx / total_files + current / total / total_files) * 100
                        self.after(0, lambda: self.progress_var.set(pct))
                    return cb

                if mode == "t_word":
                    out = os.path.join(output_dir, base + "_转Word_" + ts + ".docx")
                    pdf_to_word(fp, out, make_progress(fi))
                    log("  ✅ 已转 Word: " + os.path.basename(out))
                    self.last_output = out

                elif mode == "t_excel":
                    out = os.path.join(output_dir, base + "_转Excel_" + ts + ".xlsx")
                    pdf_to_excel(fp, out, make_progress(fi))
                    log("  ✅ 已转 Excel: " + os.path.basename(out))
                    self.last_output = out

                elif mode == "split":
                    sub_dir = os.path.join(output_dir, base + "_拆分_" + ts)
                    os.makedirs(sub_dir, exist_ok=True)
                    sm = self.split_mode.get() if hasattr(self, "split_mode") else "all"

                    if sm == "每页拆一个":
                        files = split_pdf(fp, sub_dir, "all", progress_callback=make_progress(fi))
                    elif sm == "每N页一组":
                        n = int(self.split_param.get().strip() or "2")
                        files = split_pdf(fp, sub_dir, "every_n", n, make_progress(fi))
                    elif sm == "指定页码范围":
                        r = self.split_param.get().strip() or "1-3"
                        files = split_pdf(fp, sub_dir, "range", r, make_progress(fi))
                    else:
                        files = split_pdf(fp, sub_dir, "all", progress_callback=make_progress(fi))

                    log("  ✅ 拆分为 " + str(len(files)) + " 个文件")
                    for f in files[:5]:
                        log("    📄 " + os.path.basename(f))
                    if len(files) > 5:
                        log("    ... 共 " + str(len(files)) + " 个文件")
                    self.last_output = sub_dir

            log("\n🎉 全部处理完成！")
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

    def _open_output(self):
        if self.last_output:
            path = self.last_output
            if os.path.isfile(path):
                os.startfile(os.path.dirname(path))
            else:
                os.startfile(path)

    def apply_theme(self):
        c = self.theme.colors
        try:
            self.result_text.config(bg=c["input_bg"], fg=c["fg"])
        except:
            pass
        for widget in self.winfo_children():
            try:
                if isinstance(widget, (tk.Label, tk.Frame, tk.Checkbutton, tk.Button)):
                    self.theme.apply_to_widget(widget)
            except:
                pass

