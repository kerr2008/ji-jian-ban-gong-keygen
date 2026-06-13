# -*- coding: utf-8 -*-
"""
信息提取器 v2
提取项：手机号、大写金额、小写金额、银行账号、开户银行、银行行号、日期
预览无限制，显示全部内容
"""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading


# ============ 提取规则 ============

# 大写金额汉字
CN_NUM = r"[零壹贰叁肆伍陆柒捌玖拾佰仟万亿元整角分]"
# 大写金额模式：从"人民币"或开头到"整"或"元正"
PAT_大写金额 = r"(?:人民币|￥|¥)?(" + CN_NUM + r"+[元][零壹贰叁肆伍陆柒捌玖拾佰仟万亿元角分整]*)"
PAT_大写金额 += r"|" + r"(?:人民币|￥|¥)?(" + CN_NUM + r"+[角分][整]?)"

# 小写金额：紧跟在 "￥" "¥" 后面的数字，或在"小写" "合计"等关键词后面
PAT_小写金额 = r"(?:￥|¥|小写|合计|总计|金额)[：:：]?\s*([\d,]+\.\d{2})"
PAT_小写金额 += r"|" + r"(?:￥|¥|小写|合计|总计|金额)[：:：]?\s*([\d,]+)"

# 银行账号：8-20位纯数字，且不是手机号（不以13/14/15/17/18/19开头）
PAT_银行账号 = r"(?<!\d)(?:[1-9]\d{7,19})(?!\d)"
# 排除手机号格式：如果匹配到13/14/15/17/18/19开头的11位，排除
PAT_手机号 = r"(?<!\d)1[3-9]\d{9}(?!\d)"

# 银行行号：12位纯数字（支付系统行号标准长度）
PAT_银行行号 = r"(?<!\d)\d{12}(?!\d)"

# 开户银行：包含 "银行" "支行" "分行" "信用社" 等的行
PAT_开户银行 = r"[^\n，。；]*?(?:银行|支行|分行|信用社|营业部)[^\n，。；]{0,10}"

# 日期
PAT_日期 = r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?"


# ============ 文本提取 ============

def extract_text_from_pdf(filepath):
    from pypdf import PdfReader
    texts = []
    try:
        reader = PdfReader(filepath)
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                texts.append(text)
    except Exception as e:
        return "[PDF解析错误: " + str(e) + "]"
    return "\n".join(texts)


def extract_text_from_docx(filepath):
    from docx import Document
    texts = []
    try:
        doc = Document(filepath)
        for para in doc.paragraphs:
            if para.text.strip():
                texts.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    texts.append(row_text)
    except Exception as e:
        return "[Word解析错误: " + str(e) + "]"
    return "\n".join(texts)


def extract_text_from_txt(filepath):
    encodings = ["utf-8", "gbk", "gb2312", "gb18030", "utf-16"]
    for enc in encodings:
        try:
            with open(filepath, "r", encoding=enc, errors="ignore") as f:
                return f.read()
        except:
            continue
    return "[TXT解析失败]"


# ============ 智能金额匹配 ============

def is_phone_number(num_str):
    """检查是否是手机号"""
    return bool(re.match(r"^1[3-9]\d{9}$", num_str))


def is_date_like(num_str):
    """检查是否像日期(yyyymmdd)"""
    if len(num_str) == 8:
        m = int(num_str[4:6])
        d = int(num_str[6:8])
        if 1 <= m <= 12 and 1 <= d <= 31:
            return True
    return False


CN_DIGITS = {"零":0,"壹":1,"贰":2,"叁":3,"肆":4,"伍":5,"陆":6,"柒":7,"捌":8,"玖":9}
CN_UNITS = {"拾":10,"佰":100,"仟":1000,"万":10000,"亿":100000000}


def chinese_amount_to_number(cn_str):
    """将汉字金额转为数字（粗略）"""
    import re
    # 去掉"人民币" "元整"等
    cn_str = cn_str.replace("人民币","").replace("整","").strip()
    # 简单转换：处理 壹万贰仟叁佰肆拾伍元陆角柒分
    result = 0
    temp = 0
    billion = 0
    for ch in cn_str:
        if ch == "元":
            result += temp
            temp = 0
            break
        elif ch == "角":
            pass  # 忽略角分简化处理
        elif ch == "分":
            pass
        elif ch in CN_DIGITS:
            temp = CN_DIGITS[ch]
        elif ch in CN_UNITS:
            unit = CN_UNITS[ch]
            if ch == "万":
                result += temp
                result *= unit
                temp = 0
            elif ch == "亿":
                billion = (result + temp) * unit
                result = 0
                temp = 0
            else:
                if temp == 0:
                    temp = unit
                else:
                    temp *= unit
                    result += temp
                    temp = 0
    result += temp
    return int(result + billion)


def match_amount_pairs(text):
    """匹配大写金额及其旁边的小写金额"""
    import re
    lines = text.split("\n")
    results = []
    in_pair = []

    for i, line in enumerate(lines):
        # 查找大写金额
        cn_matches = re.findall(PAT_大写金额, line, re.UNICODE)
        # 查找小写金额
        num_matches = re.findall(PAT_小写金额, line)

        if cn_matches:
            for m in cn_matches:
                cn_text = m[0] if m[0] else m[1]
                if cn_text:
                    try:
                        num_val = chinese_amount_to_number(cn_text)
                        results.append({
                            "大写": cn_text,
                            "大写数值": num_val,
                            "所在行": i
                        })
                    except:
                        results.append({"大写": cn_text, "大写数值": "?", "所在行": i})

        # 找行内的小写数字（可能在旁边列）
        if num_matches:
            for m in num_matches:
                num_str = m[0] if m[0] else m[1]
                if num_str and re.search(r"\d", num_str):
                    results.append({"小写": num_str, "所在行": i})

    return results


# ============ 主处理函数 ============

def process_file(filepath, selected_patterns):
    """处理单个文件，返回提取结果"""
    ext = Path(filepath).suffix.lower()

    if ext == ".pdf":
        text = extract_text_from_pdf(filepath)
    elif ext in (".docx", ".doc"):
        text = extract_text_from_docx(filepath)
    elif ext == ".txt":
        text = extract_text_from_txt(filepath)
    else:
        return None, "不支持的文件格式: " + ext

    if not text or text.startswith("[PDF解析错误") or text.startswith("[Word解析错误"):
        return None, text if text else "文件为空"

    results = {}

    # 手机号
    if "手机号" in selected_patterns:
        phones = re.findall(PAT_手机号, text)
        results["手机号"] = list(dict.fromkeys(p.strip() for p in phones if p.strip()))
        # 提取手机号对应的联系人信息
        contacts = []
        lines = text.split("\n")
        for line in lines:
            pm = re.search(PAT_手机号, line)
            if pm:
                phone = pm.group()
                before = line[:pm.start()].strip()
                after_t = line[pm.end():].strip()
                nm = re.search(r"[\u4e00-\u9fff]{2,10}$", before)
                name = nm.group() if nm else ""
                pos = re.search(r"^[\u4e00-\u9fff]{2,8}", after_t)
                position = pos.group() if pos else ""
                if name or position:
                    contacts.append(phone + " | " + name + (" | " + position if position else ""))
        if contacts:
            results["联系人信息"] = list(dict.fromkeys(contacts))


    # 银行账号（排除手机号和日期类数字）
    if "银行账号" in selected_patterns:
        all_nums = re.findall(PAT_银行账号, text)
        accounts = []
        for n in all_nums:
            n = n.strip()
            if 8 <= len(n) <= 20:
                if not is_phone_number(n) and not is_date_like(n):
                    accounts.append(n)
        results["银行账号"] = list(dict.fromkeys(accounts))

    # 银行行号（12位纯数字，且在行号/联行号等关键词附近）
    if "银行行号" in selected_patterns:
        lines = text.split("\n")
        line_nums = []
        for i, line in enumerate(lines):
            if any(kw in line for kw in ["行号", "联行号", "支付系统", "清算行"]):
                nums = re.findall(r"\d{12}", line)
                line_nums.extend(nums)
            else:
                nums = re.findall(r"(?<!\d)\d{12}(?!\d)", line)
                for n in nums:
                    # 12位纯数字且在上下文中像行号
                    if not is_phone_number(n) and not is_date_like(n):
                        line_nums.append(n)
        results["银行行号"] = list(dict.fromkeys(line_nums))

    # 开户银行
    if "开户银行" in selected_patterns:
        banks = re.findall(PAT_开户银行, text)
        unique_banks = []
        seen = set()
        for b in banks:
            b = b.strip()
            # 去重：取前15个字符作为key
            key = b[:15]
            if key not in seen:
                seen.add(key)
                unique_banks.append(b)
        results["开户银行"] = unique_banks

    # 大写金额
    if "大写金额" in selected_patterns:
        cn_matches = re.findall(PAT_大写金额, text)
        cn_list = []
        for m in cn_matches:
            cn_text = m[0] if m[0] else m[1]
            if cn_text:
                cn_list.append(cn_text)
        results["大写金额"] = list(dict.fromkeys(cn_list))

    # 小写金额（金额关键词后的数字）
    if "小写金额" in selected_patterns:
        num_matches = re.findall(PAT_小写金额, text)
        num_list = []
        for m in num_matches:
            num_str = m[0] if m[0] else m[1]
            if num_str:
                num_list.append(num_str)
        results["小写金额"] = list(dict.fromkeys(num_list))

    # 日期
    if "日期" in selected_patterns:
        dates = re.findall(PAT_日期, text)
        results["日期"] = list(dict.fromkeys(d.strip() for d in dates if d.strip()))

    return results, None


def process_folder(folder_path, selected_patterns, progress_callback=None):
    supported = {".pdf", ".docx", ".doc", ".txt"}
    all_results = []

    files = [f for f in Path(folder_path).iterdir()
             if f.suffix.lower() in supported and not f.name.startswith("~")]

    total = len(files)
    if total == 0:
        return [], 0

    for idx, filepath in enumerate(files):
        results, error = process_file(str(filepath), selected_patterns)
        if results:
            row = {"文件名": filepath.name}
            for name in selected_patterns:
                val = results.get(name, [])
                row[name] = "；".join(val[:100])  # 不限数量
                row[name + "_数量"] = len(val)
            row["文件路径"] = str(filepath)
            all_results.append(row)

        if progress_callback:
            progress_callback(idx + 1, total, filepath.name)

    return all_results, total


def export_to_excel(results, output_path):
    import pandas as pd
    if not results:
        return False
    df = pd.DataFrame(results)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="提取结果")
        worksheet = writer.sheets["提取结果"]
        for col_idx, col_name in enumerate(df.columns, 1):
            max_len = max(len(str(col_name)),
                          df[col_name].astype(str).str.len().max() if len(df) > 0 else 10)
            adjusted = min(max_len * 2 + 2, 80)
            col_letter = worksheet.cell(1, col_idx).column_letter
            worksheet.column_dimensions[col_letter].width = adjusted
    return True


# ============ GUI 界面 ============

EXTRACT_PATTERNS_ORDERED = [
    "手机号", "银行账号", "银行行号", "开户银行",
    "大写金额", "小写金额", "日期"
]


class ExtractorFrame(ttk.Frame):
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.selected_folder = ""
        self.selected_files = ()
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self.check_vars = {}
        self.results_data = []
        self.last_output = None
        self._build_ui()

    def _build_ui(self):
        c = self.theme.colors

        header = tk.Label(self, text="文档信息提取器 — 手机号 / 银行账号 / 开户行 / 金额 / 日期",
                          font=("Microsoft YaHei", 11, "bold"),
                          bg=c["panel_bg"], fg=c["fg"], anchor="w")
        header.pack(fill="x", pady=(0, 15))

        # 文件选择
        select_frame = tk.Frame(self, bg=c["panel_bg"])
        select_frame.pack(fill="x", pady=(0, 10))
        tk.Label(select_frame, text="选择文件或文件夹：",
                 bg=c["panel_bg"], fg=c["fg"],
                 font=("Microsoft YaHei", 9)).pack(side="left")
        self.path_label = tk.Label(select_frame, text="未选择",
                                    bg=c["panel_bg"], fg=c["disabled_fg"],
                                    font=("Microsoft YaHei", 9), anchor="w")
        self.path_label.pack(side="left", fill="x", expand=True, padx=(10, 0))
        btn_frame = tk.Frame(select_frame, bg=c["panel_bg"])
        btn_frame.pack(side="right")
        self.btn_select_folder = tk.Button(btn_frame, text="📁 选择文件夹",
                                           command=self._select_folder,
                                           bg=c["accent"], fg="white",
                                           font=("Microsoft YaHei", 9),
                                           relief="flat", padx=12, pady=3, cursor="hand2")
        self.btn_select_folder.pack(side="left", padx=(0, 5))
        self.btn_select_files = tk.Button(btn_frame, text="📄 选择文件",
                                          command=self._select_files,
                                          bg=c["sidebar_bg"], fg=c["fg"],
                                          font=("Microsoft YaHei", 9),
                                          relief="flat", padx=12, pady=3, cursor="hand2")
        self.btn_select_files.pack(side="left")

        # 提取选项
        option_frame = tk.LabelFrame(self, text="提取内容",
                                     bg=c["panel_bg"], fg=c["fg"],
                                     font=("Microsoft YaHei", 9), padx=10, pady=5)
        option_frame.pack(fill="x", pady=(0, 10))
        checkbox_frame = tk.Frame(option_frame, bg=c["panel_bg"])
        checkbox_frame.pack(fill="x")
        cols = [tk.Frame(checkbox_frame, bg=c["panel_bg"]) for _ in range(2)]
        cols[0].pack(side="left", fill="x", expand=True)
        cols[1].pack(side="left", fill="x", expand=True)

        default_checks = ("手机号", "银行账号", "小写金额", "日期")
        for i, name in enumerate(EXTRACT_PATTERNS_ORDERED):
            var = tk.BooleanVar(value=(name in default_checks))
            self.check_vars[name] = var
            col = cols[0 if i < 4 else 1]
            cb = tk.Checkbutton(col, text=name, variable=var,
                                bg=c["panel_bg"], fg=c["fg"],
                                selectcolor=c["input_bg"],
                                font=("Microsoft YaHei", 9),
                                activebackground=c["panel_bg"],
                                activeforeground=c["fg"])
            cb.pack(anchor="w", pady=1)

        # 操作按钮
        action_frame = tk.Frame(self, bg=c["panel_bg"])
        action_frame.pack(fill="x", pady=(5, 10))
        self.btn_start = tk.Button(action_frame, text="🚀 开始提取",
                                   command=self._start_extract,
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

        # 进度条
        progress_frame = tk.Frame(self, bg=c["panel_bg"])
        progress_frame.pack(fill="x", pady=(5, 5))
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                        maximum=100, mode="determinate")
        self.progress.pack(fill="x", pady=(0, 3))
        self.status_label = tk.Label(progress_frame, textvariable=self.status_var,
                                     bg=c["panel_bg"], fg=c["disabled_fg"],
                                     font=("Microsoft YaHei", 8))
        self.status_label.pack(anchor="w")

        # 结果表格（无限制显示）
        result_frame = tk.LabelFrame(self, text="提取结果预览（全部展示）",
                                     bg=c["panel_bg"], fg=c["fg"],
                                     font=("Microsoft YaHei", 9), padx=5, pady=5)
        result_frame.pack(fill="both", expand=True)

        cols = ("文件名",)
        for name in EXTRACT_PATTERNS_ORDERED:
            cols = cols + (name,)

        tree_frame = tk.Frame(result_frame, bg=c["panel_bg"])
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=cols,
                                 show="headings", height=10,
                                 style="light.Treeview")
        for col in cols:
            self.tree.heading(col, text=col)
            if col == "文件名":
                self.tree.column(col, width=200, minwidth=150)
            elif col in ("银行账号", "小写金额"):
                self.tree.column(col, width=250, minwidth=150)
            elif col == "开户银行":
                self.tree.column(col, width=300, minwidth=200)
            else:
                self.tree.column(col, width=200, minwidth=120)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        self.summary_label = tk.Label(self, text="",
                                      bg=c["panel_bg"], fg=c["disabled_fg"],
                                      font=("Microsoft YaHei", 9))
        self.summary_label.pack(fill="x", pady=(5, 0))

    def _select_folder(self):
        folder = filedialog.askdirectory(title="选择包含文件的文件夹")
        if folder:
            self.selected_folder = folder
            self.selected_files = ()
            self.path_label.config(text=folder, fg=self.theme.get("fg"))
            self._update_file_count()
            self.btn_start.config(state="normal")

    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="选择文件",
            filetypes=[("支持的文件", "*.pdf *.docx *.doc *.txt"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = files
            self.selected_folder = ""
            self.path_label.config(text=str(len(files)) + " 个文件已选择", fg=self.theme.get("fg"))
            self.btn_start.config(state="normal")

    def _update_file_count(self):
        if self.selected_folder and os.path.isdir(self.selected_folder):
            supported = {".pdf", ".docx", ".doc", ".txt"}
            count = sum(1 for f in Path(self.selected_folder).iterdir()
                        if f.suffix.lower() in supported and not f.name.startswith("~"))
            self.path_label.config(text=self.selected_folder + " (" + str(count) + " 个文件)")

    def _get_selected_patterns(self):
        return [name for name in EXTRACT_PATTERNS_ORDERED if self.check_vars[name].get()]

    def _start_extract(self):
        patterns = self._get_selected_patterns()
        if not patterns:
            messagebox.showwarning("提示", "请至少选择一种提取内容")
            return
        self.btn_start.config(state="disabled", text="⏳ 处理中...")
        self.progress_var.set(0)
        self.tree.delete(*self.tree.get_children())
        thread = threading.Thread(target=self._process, args=(patterns,), daemon=True)
        thread.start()

    def _process(self, patterns):
        def update_progress(current, total, filename):
            self.progress_var.set(current / total * 100)
            self.status_var.set("处理中 (" + str(current) + "/" + str(total) + "): " + filename)

        if self.selected_folder and os.path.isdir(self.selected_folder):
            results, total = process_folder(self.selected_folder, patterns, update_progress)
        elif self.selected_files:
            results = []
            total = len(self.selected_files)
            for idx, fp in enumerate(self.selected_files):
                r, err = process_file(fp, patterns)
                if r:
                    row = {"文件名": os.path.basename(fp)}
                    for name in patterns:
                        vals = r.get(name, [])
                        row[name] = "；".join(vals)
                        row[name + "_数量"] = len(vals)
                    results.append(row)
                elif err:
                    results.append({"文件名": "[错误] " + os.path.basename(fp)})
                update_progress(idx + 1, total, os.path.basename(fp))
        else:
            return
        self.results_data = results
        self.after(0, lambda: self._update_results(results, patterns))

    def _update_results(self, results, patterns):
        c = self.theme.colors
        self.tree.delete(*self.tree.get_children())
        total_count = 0
        for r in results:
            for p in patterns:
                key = p + "_数量"
                if key in r:
                    total_count += r[key]
        if not results:
            self.summary_label.config(text="未找到匹配内容，请检查文件格式", fg=c["warning"])
        else:
            for r in results:
                values = [r.get("文件名", "")]
                for p in patterns:
                    values.append(r.get(p, ""))
                self.tree.insert("", "end", values=values)
            self.summary_label.config(
                text="✅ 处理完成 | " + str(len(results)) + " 个文件 | 共提取 " + str(total_count) + " 条信息",
                fg=c["success"])
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      "闲鱼工具箱_输出")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(output_dir, "提取结果_" + timestamp + ".xlsx")
            export_to_excel(results, output_path)
            self.last_output = output_path
            self.btn_open.config(state="normal", text="📂 打开: " + os.path.basename(output_path))
        self.btn_start.config(state="normal", text="🚀 开始提取")
        self.progress_var.set(100)
        self.status_var.set("处理完成 ✅")

    def _open_output(self):
        if self.last_output and os.path.exists(self.last_output):
            os.startfile(os.path.dirname(self.last_output))

    def apply_theme(self):
        c = self.theme.colors
        for widget in self.winfo_children():
            try:
                if isinstance(widget, (tk.Label, tk.Frame, tk.Checkbutton, tk.Button)):
                    self.theme.apply_to_widget(widget)
            except:
                pass
