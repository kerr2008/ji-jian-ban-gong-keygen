"""
Module 3: 敏感词过滤与替换
TXT/Word 批量检测敏感词，自定义词库，一键替换
"""

import os
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading


# 内置敏感词库（示例）
BUILTIN_WORDS = [
    # 脏话/不文明用语
    '妈的', '傻逼', '草泥马', '你妈', '艹', 'fuck', 'shit',
    # 政治敏感（基本）
    '法轮功', '台独', '藏独',
    # 广告/营销违禁词
    '最', '第一', '国家级', '唯一', '顶级', '万能', '绝对',
    '全网首发', '世界领先', '全国首家', '销量冠军', '永久',
]

# 默认替换词
DEFAULT_REPLACEMENT = '***'


def load_word_list(filepath=None):
    """加载词库，如果指定文件则从文件加载"""
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return list(BUILTIN_WORDS)
    return list(BUILTIN_WORDS)


def save_word_list(words, filepath):
    """保存词库到文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(words))


def scan_text(text, words):
    """扫描文本中的敏感词，返回匹配结果"""
    text_lower = text.lower()
    results = {}
    for word in words:
        if not word:
            continue
        # 大小写不敏感搜索
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            results[word] = len(matches)
    return results


def replace_sensitive(text, words, replacement=DEFAULT_REPLACEMENT):
    """替换文本中的敏感词"""
    result = text
    stats = {}
    for word in words:
        if not word:
            continue
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        count = len(pattern.findall(result))
        if count > 0:
            result = pattern.sub(replacement, result)
            stats[word] = count
    return result, stats


def process_docx(filepath, words, replacement, output_path, mode='report'):
    """处理 Word 文件"""
    from docx import Document
    doc = Document(filepath)
    total_finds = {}
    
    for para in doc.paragraphs:
        if mode == 'replace':
            new_text, stats = replace_sensitive(para.text, words, replacement)
            if stats:
                para.text = new_text
                for k, v in stats.items():
                    total_finds[k] = total_finds.get(k, 0) + v
        else:
            stats = scan_text(para.text, words)
            for k, v in stats.items():
                total_finds[k] = total_finds.get(k, 0) + v
    
    # Process tables too
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    if mode == 'replace':
                        new_text, stats = replace_sensitive(para.text, words, replacement)
                        if stats:
                            para.text = new_text
                            for k, v in stats.items():
                                total_finds[k] = total_finds.get(k, 0) + v
                    else:
                        stats = scan_text(para.text, words)
                        for k, v in stats.items():
                            total_finds[k] = total_finds.get(k, 0) + v
    
    if mode == 'replace':
        doc.save(output_path)
    return total_finds


def process_txt(filepath, words, replacement, output_path, mode='report'):
    """处理 TXT 文件"""
    encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030']
    text = None
    for enc in encodings:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                text = f.read()
            break
        except:
            continue
    
    if text is None:
        raise Exception(f"无法读取 {filepath}")
    
    if mode == 'replace':
        new_text, stats = replace_sensitive(text, words, replacement)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
    else:
        stats = scan_text(text, words)
    
    return stats


class SensitiveFilterFrame(ttk.Frame):
    """敏感词过滤 - GUI 界面"""
    
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.selected_files = []
        self.custom_words = []
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self._build_ui()
    
    def _build_ui(self):
        c = self.theme.colors
        
        header = tk.Label(self, text="敏感词过滤与替换 — 检测 / 替换 / 报告",
                          font=('Microsoft YaHei', 11, 'bold'),
                          bg=c['panel_bg'], fg=c['fg'], anchor='w')
        header.pack(fill='x', pady=(0, 15))
        
        # === 模式选择 ===
        mode_frame = tk.Frame(self, bg=c['panel_bg'])
        mode_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(mode_frame, text="模式：", bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        
        self.mode = tk.StringVar(value='report')
        for text, val in [('仅检测', 'report'), ('检测并替换', 'replace')]:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.mode, value=val,
                                bg=c['panel_bg'], fg=c['fg'], selectcolor=c['input_bg'],
                                font=('Microsoft YaHei', 9),
                                activebackground=c['panel_bg'], activeforeground=c['fg'])
            rb.pack(side='left', padx=(5, 0))
        
        # === 文件选择 ===
        file_frame = tk.Frame(self, bg=c['panel_bg'])
        file_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(file_frame, text="选择文件：", bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        
        self.file_label = tk.Label(file_frame, text="未选择",
                                    bg=c['panel_bg'], fg=c['disabled_fg'],
                                    font=('Microsoft YaHei', 9))
        self.file_label.pack(side='left', fill='x', expand=True, padx=(10, 0))
        
        self.btn_select = tk.Button(file_frame, text="📁 选择文件",
                                    command=self._select_files,
                                    bg=c['accent'], fg='white',
                                    font=('Microsoft YaHei', 9),
                                    relief='flat', padx=12, pady=3, cursor='hand2')
        self.btn_select.pack(side='right')
        
        # === 替换设置 ===
        replace_frame = tk.Frame(self, bg=c['panel_bg'])
        replace_frame.pack(fill='x', pady=(5, 10))
        
        tk.Label(replace_frame, text="替换为：", bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        
        self.replacement = tk.Entry(replace_frame, bg=c['input_bg'], fg=c['fg'],
                                     font=('Microsoft YaHei', 9),
                                     relief='flat', bd=1, width=10)
        self.replacement.insert(0, DEFAULT_REPLACEMENT)
        self.replacement.pack(side='left', padx=(5, 20))
        
        # === 词库设置 ===
        dict_frame = tk.LabelFrame(self, text="敏感词库",
                                    bg=c['panel_bg'], fg=c['fg'],
                                    font=('Microsoft YaHei', 9),
                                    padx=5, pady=5)
        dict_frame.pack(fill='x', pady=(0, 10))
        
        dict_inner = tk.Frame(dict_frame, bg=c['panel_bg'])
        dict_inner.pack(fill='x')
        
        self.dict_text = tk.Text(dict_inner, height=5,
                                  bg=c['input_bg'], fg=c['fg'],
                                  font=('Consolas', 9),
                                  relief='flat', bd=1, padx=3, pady=3)
        self.dict_text.insert('1.0', '\n'.join(BUILTIN_WORDS))
        self.dict_text.pack(fill='x', pady=(0, 5))
        
        btn_row = tk.Frame(dict_inner, bg=c['panel_bg'])
        btn_row.pack(fill='x')
        
        tk.Label(btn_row, text="每行一个词，编辑后自动保存",
                 bg=c['panel_bg'], fg=c['disabled_fg'],
                 font=('Microsoft YaHei', 8)).pack(side='left')
        
        self.btn_reset = tk.Button(btn_row, text="↺ 重置为默认词库",
                                   command=self._reset_dict,
                                   bg=c['sidebar_bg'], fg=c['fg'],
                                   font=('Microsoft YaHei', 8),
                                   relief='flat', padx=8, pady=1, cursor='hand2')
        self.btn_reset.pack(side='right')
        
        # === 操作按钮 ===
        action_frame = tk.Frame(self, bg=c['panel_bg'])
        action_frame.pack(fill='x', pady=(5, 10))
        
        self.btn_start = tk.Button(action_frame, text="🔍 开始检测",
                                    command=self._start_process,
                                    bg=c['success'], fg='white',
                                    font=('Microsoft YaHei', 10, 'bold'),
                                    relief='flat', padx=20, pady=5,
                                    cursor='hand2', state='disabled')
        self.btn_start.pack(side='left', padx=(0, 10))
        
        self.btn_open = tk.Button(action_frame, text="📂 打开输出文件夹",
                                   command=self._open_output,
                                   bg=c['sidebar_bg'], fg=c['fg'],
                                   font=('Microsoft YaHei', 9),
                                   relief='flat', padx=12, pady=3,
                                   cursor='hand2', state='disabled')
        self.btn_open.pack(side='left')
        
        # === 进度 ===
        progress_frame = tk.Frame(self, bg=c['panel_bg'])
        progress_frame.pack(fill='x', pady=(5, 5))
        
        self.progress = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                         maximum=100, mode='determinate')
        self.progress.pack(fill='x', pady=(0, 3))
        
        self.status_label = tk.Label(progress_frame, textvariable=self.status_var,
                                      bg=c['panel_bg'], fg=c['disabled_fg'],
                                      font=('Microsoft YaHei', 8))
        self.status_label.pack(anchor='w')
        
        # === 结果 ===
        result_frame = tk.LabelFrame(self, text="检测结果",
                                      bg=c['panel_bg'], fg=c['fg'],
                                      font=('Microsoft YaHei', 9),
                                      padx=5, pady=5)
        result_frame.pack(fill='both', expand=True)
        
        columns = ('敏感词', '出现次数')
        tree_frame = tk.Frame(result_frame, bg=c['panel_bg'])
        tree_frame.pack(fill='both', expand=True)
        
        self.tree = ttk.Treeview(tree_frame, columns=columns,
                                  show='headings', height=8)
        self.tree.heading('敏感词', text='敏感词')
        self.tree.heading('出现次数', text='出现次数')
        self.tree.column('敏感词', width=200)
        self.tree.column('出现次数', width=100, anchor='center')
        
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
    
    def _select_files(self):
        files = filedialog.askopenfilenames(
            title="选择 TXT 或 Word 文件",
            filetypes=[("文本/Word", "*.txt *.docx"), ("所有文件", "*.*")]
        )
        if files:
            self.selected_files = files
            names = [os.path.basename(f) for f in files]
            self.file_label.config(text=f"{len(files)} 个文件: {'; '.join(names[:3])}{'...' if len(names) > 3 else ''}",
                                    fg=self.theme.get('fg'))
            self.btn_start.config(state='normal', text="🔍 开始检测")
    
    def _reset_dict(self):
        self.dict_text.delete('1.0', 'end')
        self.dict_text.insert('1.0', '\n'.join(BUILTIN_WORDS))
    
    def _get_words(self):
        text = self.dict_text.get('1.0', 'end').strip()
        return [line.strip() for line in text.split('\n') if line.strip()]
    
    def _start_process(self):
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择文件")
            return
        
        words = self._get_words()
        if not words:
            messagebox.showwarning("提示", "词库为空")
            return
        
        self.btn_start.config(state='disabled', text="⏳ 处理中...")
        self.progress_var.set(0)
        self.tree.delete(*self.tree.get_children())
        
        thread = threading.Thread(target=self._process, args=(words,), daemon=True)
        thread.start()
    
    def _process(self, words):
        mode = self.mode.get()
        replacement = self.replacement.get().strip() or DEFAULT_REPLACEMENT
        output_dir = os.path.join(os.path.dirname(os.path.abspath('.')), '闲鱼工具箱_输出')
        os.makedirs(output_dir, exist_ok=True)
        
        all_stats = {}
        total = len(self.selected_files)
        
        for idx, fp in enumerate(self.selected_files):
            ext = Path(fp).suffix.lower()
            self.after(0, lambda i=idx, t=total, f=os.path.basename(fp):
                       self.progress_var.set((i + 1) / t * 100) or
                       self.status_var.set(f"处理中 ({i+1}/{t}): {f}"))
            
            try:
                if ext in ('.docx', '.doc'):
                    output = os.path.join(output_dir, f"filtered_{os.path.basename(fp)}") if mode == 'replace' else None
                    stats = process_docx(fp, words, replacement, output, mode)
                elif ext == '.txt':
                    output = os.path.join(output_dir, f"filtered_{os.path.basename(fp)}") if mode == 'replace' else None
                    stats = process_txt(fp, words, replacement, output, mode)
                else:
                    continue
                
                for k, v in stats.items():
                    all_stats[k] = all_stats.get(k, 0) + v
            except Exception as e:
                self.after(0, lambda e=e: self._append_result(f"[错误] {os.path.basename(fp)}: {e}"))
        
        # 汇总报告
        report_path = os.path.join(output_dir, f'敏感词报告_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"敏感词检测报告\n")
            f.write(f"检测时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"检测文件: {total} 个\n")
            f.write(f"操作模式: {'检测并替换' if mode == 'replace' else '仅检测'}\n")
            f.write("=" * 40 + "\n")
            if all_stats:
                sorted_stats = sorted(all_stats.items(), key=lambda x: x[1], reverse=True)
                for word, count in sorted_stats:
                    f.write(f"{word}: {count} 次\n")
                f.write(f"\n总计: {sum(all_stats.values())} 次匹配\n")
            else:
                f.write("未发现敏感词 ✅\n")
        
        self.last_output = output_dir
        
        # 更新 UI
        self.after(0, lambda: self._update_results(all_stats, report_path))
    
    def _update_results(self, stats, report_path):
        self.tree.delete(*self.tree.get_children())
        
        if stats:
            sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
            for word, count in sorted_stats:
                self.tree.insert('', 'end', values=(word, count))
            self.status_var.set(f"检测完成: {sum(stats.values())} 次匹配, {len(stats)} 个敏感词")
        else:
            self.status_var.set("检测完成: 未发现敏感词 ✅")
        
        self._append_result(f"\n📄 报告已保存: {os.path.basename(report_path)}")
        self.btn_start.config(state='normal', text="🔍 开始检测")
        self.btn_open.config(state='normal')
        self.progress_var.set(100)
    
    def _append_result(self, text):
        pass  # Results shown in tree
    
    def _open_output(self):
        if hasattr(self, 'last_output'):
            os.startfile(self.last_output)
    
    def apply_theme(self):
        c = self.theme.colors
        try:
            self.dict_text.config(bg=c['input_bg'], fg=c['fg'])
        except:
            pass
        for widget in self.winfo_children():
            try:
                if isinstance(widget, (tk.Label, tk.Frame, tk.Checkbutton, tk.Button)):
                    self.theme.apply_to_widget(widget)
            except:
                pass
