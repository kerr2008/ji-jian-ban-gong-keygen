"""
Module 2: Excel 工坊
多文件合并、去重、拆分、两列对比
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading


def merge_excel(files, output_path, merge_type='rows'):
    """合并多个 Excel 文件"""
    import pandas as pd
    dfs = []
    for f in files:
        try:
            if f.endswith('.csv'):
                df = pd.read_csv(f)
            else:
                df = pd.read_excel(f, engine='openpyxl')
            df['来源文件'] = os.path.basename(f)
            dfs.append(df)
        except Exception as e:
            raise Exception(f"读取 {os.path.basename(f)} 失败: {e}")
    
    if not dfs:
        raise Exception("没有可合并的文件")
    
    if merge_type == 'rows':
        result = pd.concat(dfs, ignore_index=True)
    elif merge_type == 'columns':
        result = pd.concat(dfs, axis=1, ignore_index=True)
    else:
        result = pd.concat(dfs, ignore_index=True)
    
    result.to_excel(output_path, index=False, engine='openpyxl')
    return result.shape


def dedup_excel(file_path, columns, output_path, keep='first'):
    """Excel 去重"""
    import pandas as pd
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine='openpyxl')
    
    if columns:
        subset = columns if isinstance(columns, list) else [columns]
        before = len(df)
        df = df.drop_duplicates(subset=subset, keep=keep)
        after = len(df)
    else:
        before = len(df)
        df = df.drop_duplicates(keep=keep)
        after = len(df)
    
    df.to_excel(output_path, index=False, engine='openpyxl')
    return before, after


def split_excel(file_path, column, output_dir):
    """按列值拆分 Excel 为多个文件"""
    import pandas as pd
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine='openpyxl')
    
    if column not in df.columns:
        raise Exception(f"列 '{column}' 不存在")
    
    groups = df.groupby(column)
    files_created = []
    
    for name, group in groups:
        safe_name = str(name).replace('/', '_').replace('\\', '_').replace(':', '_')
        out_path = os.path.join(output_dir, f"{safe_name}.xlsx")
        group.to_excel(out_path, index=False, engine='openpyxl')
        files_created.append(out_path)
    
    return files_created


def compare_columns(file_path, col_a, col_b, output_path):
    """比较两列数据，找出差异"""
    import pandas as pd
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine='openpyxl')
    
    if col_a not in df.columns:
        raise Exception(f"列 '{col_a}' 不存在")
    if col_b not in df.columns:
        raise Exception(f"列 '{col_b}' 不存在")
    
    set_a = set(df[col_a].dropna().unique())
    set_b = set(df[col_b].dropna().unique())
    
    only_in_a = list(set_a - set_b)
    only_in_b = list(set_b - set_a)
    in_both = list(set_a & set_b)
    
    result = pd.DataFrame({
        f'仅存在于{col_a}': pd.Series(only_in_a + [''] * (max(len(only_in_b), len(in_both)) - len(only_in_a))),
        f'仅存在于{col_b}': pd.Series(only_in_b + [''] * (max(len(only_in_a), len(in_both)) - len(only_in_b))),
        '共同存在': pd.Series(in_both + [''] * (max(len(only_in_a), len(only_in_b)) - len(in_both))),
    })
    
    result.to_excel(output_path, index=False, engine='openpyxl')
    return len(only_in_a), len(only_in_b), len(in_both)


def quick_summary(file_path, output_path):
    """快速汇总：求和、计数、平均值"""
    import pandas as pd
    if not os.path.exists(file_path):
        raise Exception("文件不存在")
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:
        df = pd.read_excel(file_path, engine='openpyxl')
    
    numeric_cols = df.select_dtypes(include='number').columns
    
    rows = []
    for col in df.columns:
        row = {'列名': col, '数据类型': str(df[col].dtype), '非空数': df[col].count(),
               '唯一值': df[col].nunique()}
        if col in numeric_cols:
            row.update({'求和': df[col].sum(), '平均值': round(df[col].mean(), 2),
                        '最小值': df[col].min(), '最大值': df[col].max()})
        else:
            row.update({'求和': '', '平均值': '', '最小值': '', '最大值': ''})
        rows.append(row)
    
    summary = pd.DataFrame(rows)
    summary['列名'] = summary['列名'].astype(str)
    summary['数据类型'] = summary['数据类型'].astype(str)
    summary['非空数'] = summary['非空数'].astype(str)
    summary['唯一值'] = summary['唯一值'].astype(str)
    for col in ['求和', '平均值', '最小值', '最大值']:
        summary[col] = summary[col].astype(str)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        summary.to_excel(writer, index=False, sheet_name='汇总')
        df.to_excel(writer, index=False, sheet_name='原始数据')
    
    return df.shape


class ExcelToolFrame(ttk.Frame):
    """Excel 工坊 - GUI 界面"""
    
    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.selected_files = []
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self._build_ui()
    
    def _build_ui(self):
        c = self.theme.colors
        
        header = tk.Label(self, text="Excel 文件处理工坊 — 合并 / 去重 / 拆分 / 对比",
                          font=('Microsoft YaHei', 11, 'bold'),
                          bg=c['panel_bg'], fg=c['fg'], anchor='w')
        header.pack(fill='x', pady=(0, 15))
        
        # === 操作选择 ===
        op_frame = tk.Frame(self, bg=c['panel_bg'])
        op_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(op_frame, text="选择操作：", bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        
        self.operation = tk.StringVar(value='merge')
        ops = [('合并文件', 'merge'), ('去重', 'dedup'), ('拆分', 'split'),
               ('对比两列', 'compare'), ('快速汇总', 'summary')]
        for text, val in ops:
            rb = tk.Radiobutton(op_frame, text=text, variable=self.operation, value=val,
                                bg=c['panel_bg'], fg=c['fg'], selectcolor=c['input_bg'],
                                font=('Microsoft YaHei', 9),
                                activebackground=c['panel_bg'], activeforeground=c['fg'],
                                command=self._on_op_change)
            rb.pack(side='left', padx=(5, 0))
        
        # === 文件选择 ===
        file_frame = tk.Frame(self, bg=c['panel_bg'])
        file_frame.pack(fill='x', pady=(0, 10))
        
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
        
        # === 参数设置 ===
        self.param_frame = tk.LabelFrame(self, text="参数设置",
                                          bg=c['panel_bg'], fg=c['fg'],
                                          font=('Microsoft YaHei', 9),
                                          padx=10, pady=5)
        self.param_frame.pack(fill='x', pady=(0, 10))
        
        self.param_content = tk.Frame(self.param_frame, bg=c['panel_bg'])
        self.param_content.pack(fill='x')
        
        self._build_merge_params()
        
        # === 操作按钮 ===
        action_frame = tk.Frame(self, bg=c['panel_bg'])
        action_frame.pack(fill='x', pady=(5, 10))
        
        self.btn_start = tk.Button(action_frame, text="🚀 开始处理",
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
        result_frame = tk.LabelFrame(self, text="执行结果",
                                      bg=c['panel_bg'], fg=c['fg'],
                                      font=('Microsoft YaHei', 9),
                                      padx=5, pady=5)
        result_frame.pack(fill='both', expand=True)
        
        self.result_text = tk.Text(result_frame, bg=c['input_bg'], fg=c['fg'],
                                    font=('Consolas', 9), wrap='word',
                                    relief='flat', padx=5, pady=5,
                                    state='disabled')
        self.result_text.pack(fill='both', expand=True)
    
    def _build_merge_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="合并方式：",
                 bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        self.merge_type = tk.StringVar(value='rows')
        ttk.Combobox(self.param_content, textvariable=self.merge_type,
                      values=['按行合并', '按列合并'], state='readonly',
                      width=12).pack(side='left', padx=(5, 0))
    
    def _build_dedup_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="去重列名(逗号分隔，留空=全部)：",
                 bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        self.dedup_cols = tk.Entry(self.param_content, bg=c['input_bg'], fg=c['fg'],
                                    font=('Microsoft YaHei', 9),
                                    relief='flat', bd=1, width=25)
        self.dedup_cols.pack(side='left', padx=(5, 0))
    
    def _build_split_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="按哪列拆分：",
                 bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        self.split_col = tk.Entry(self.param_content, bg=c['input_bg'], fg=c['fg'],
                                   font=('Microsoft YaHei', 9),
                                   relief='flat', bd=1, width=20)
        self.split_col.pack(side='left', padx=(5, 0))
    
    def _build_compare_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="列A：", bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        self.col_a = tk.Entry(self.param_content, bg=c['input_bg'], fg=c['fg'],
                               font=('Microsoft YaHei', 9), relief='flat', bd=1, width=15)
        self.col_a.pack(side='left', padx=(2, 10))
        tk.Label(self.param_content, text="列B：", bg=c['panel_bg'], fg=c['fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
        self.col_b = tk.Entry(self.param_content, bg=c['input_bg'], fg=c['fg'],
                               font=('Microsoft YaHei', 9), relief='flat', bd=1, width=15)
        self.col_b.pack(side='left', padx=(2, 0))
    
    def _build_summary_params(self):
        self._clear_params()
        c = self.theme.colors
        tk.Label(self.param_content, text="选择一个 Excel 文件后点击开始，自动生成数据汇总报告",
                 bg=c['panel_bg'], fg=c['disabled_fg'],
                 font=('Microsoft YaHei', 9)).pack(side='left')
    
    def _clear_params(self):
        for w in self.param_content.winfo_children():
            w.destroy()
    
    def _on_op_change(self):
        op = self.operation.get()
        builders = {
            'merge': self._build_merge_params,
            'dedup': self._build_dedup_params,
            'split': self._build_split_params,
            'compare': self._build_compare_params,
            'summary': self._build_summary_params,
        }
        builders.get(op, lambda: None)()
        self._update_select_mode()
    
    def _update_select_mode(self):
        op = self.operation.get()
        if op == 'merge':
            self.btn_select.config(text="📁 选择多个文件")
        else:
            self.btn_select.config(text="📁 选择文件")
    
    def _select_files(self):
        op = self.operation.get()
        if op == 'merge':
            files = filedialog.askopenfilenames(
                title="选择 Excel 文件",
                filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("所有文件", "*.*")]
            )
        else:
            f = filedialog.askopenfilename(
                title="选择 Excel 文件",
                filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("所有文件", "*.*")]
            )
            files = (f,) if f else ()
        
        if files:
            self.selected_files = files
            names = [os.path.basename(f) for f in files]
            self.file_label.config(text=f"{len(files)} 个文件: {'; '.join(names[:3])}{'...' if len(names) > 3 else ''}",
                                    fg=self.theme.get('fg'))
            self.btn_start.config(state='normal')
    
    def _start_process(self):
        if not self.selected_files:
            messagebox.showwarning("提示", "请先选择文件")
            return
        self.btn_start.config(state='disabled', text="⏳ 处理中...")
        self.progress_var.set(0)
        self.result_text.config(state='normal')
        self.result_text.delete('1.0', 'end')
        
        thread = threading.Thread(target=self._process, daemon=True)
        thread.start()
    
    def _process(self):
        op = self.operation.get()
        output_dir = os.path.join(os.path.dirname(os.path.abspath('.')), '闲鱼工具箱_输出')
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        def log(msg):
            self.after(0, lambda: self._append_log(msg))
        
        try:
            if op == 'merge':
                merge_type = 'rows' if '行' in self.merge_type.get() else 'columns'
                output = os.path.join(output_dir, f'合并结果_{timestamp}.xlsx')
                shape = merge_excel(self.selected_files, output, merge_type)
                log(f"✅ 合并完成！")
                log(f"   文件数: {len(self.selected_files)}")
                log(f"   结果大小: {shape[0]} 行 × {shape[1]} 列")
                log(f"   输出: {output}")
                self.last_output = output
            
            elif op == 'dedup':
                cols = self.dedup_cols.get().strip()
                col_list = [c.strip() for c in cols.split(',')] if cols else None
                output = os.path.join(output_dir, f'去重结果_{timestamp}.xlsx')
                before, after = dedup_excel(self.selected_files[0], col_list, output)
                log(f"✅ 去重完成！")
                log(f"   去重前: {before} 行")
                log(f"   去重后: {after} 行")
                log(f"   删除: {before - after} 行")
                log(f"   输出: {output}")
                self.last_output = output
            
            elif op == 'split':
                col = self.split_col.get().strip()
                if not col:
                    raise Exception("请输入拆分列名")
                files = split_excel(self.selected_files[0], col, output_dir)
                log(f"✅ 拆分完成！")
                log(f"   生成 {len(files)} 个文件")
                for f in files[:10]:
                    log(f"   📄 {os.path.basename(f)}")
                if len(files) > 10:
                    log(f"   ... 共 {len(files)} 个文件")
                self.last_output = output_dir
            
            elif op == 'compare':
                col_a = self.col_a.get().strip()
                col_b = self.col_b.get().strip()
                if not col_a or not col_b:
                    raise Exception("请输入两列列名")
                output = os.path.join(output_dir, f'对比结果_{timestamp}.xlsx')
                only_a, only_b, both = compare_columns(self.selected_files[0], col_a, col_b, output)
                log(f"✅ 对比完成！")
                log(f"   {col_a} 独有: {only_a} 条")
                log(f"   {col_b} 独有: {only_b} 条")
                log(f"   共同: {both} 条")
                log(f"   输出: {output}")
                self.last_output = output
            
            elif op == 'summary':
                output = os.path.join(output_dir, f'数据汇总_{timestamp}.xlsx')
                shape = quick_summary(self.selected_files[0], output)
                log(f"✅ 汇总完成！")
                log(f"   数据大小: {shape[0]} 行 × {shape[1]} 列")
                log(f"   包含：汇总表 + 原始数据表")
                log(f"   输出: {output}")
                self.last_output = output
            
            self.after(0, lambda: self.btn_open.config(state='normal'))
        
        except Exception as e:
            log(f"❌ 错误: {e}")
        
        self.progress_var.set(100)
        self.after(0, lambda: self.btn_start.config(state='normal', text="🚀 开始处理"))
        self.after(0, lambda: self.status_var.set("处理完成 ✅"))
    
    def _append_log(self, text):
        self.result_text.config(state='normal')
        self.result_text.insert('end', text + '\n')
        self.result_text.see('end')
        self.result_text.config(state='disabled')
    
    def _open_output(self):
        if hasattr(self, 'last_output'):
            path = self.last_output
            if os.path.isfile(path):
                os.startfile(os.path.dirname(path))
            else:
                os.startfile(path)
    
    def apply_theme(self):
        c = self.theme.colors
        try:
            self.result_text.config(bg=c['input_bg'], fg=c['fg'])
        except:
            pass
        for widget in self.winfo_children():
            try:
                if isinstance(widget, (tk.Label, tk.Frame, tk.Checkbutton, tk.Button)):
                    self.theme.apply_to_widget(widget)
            except:
                pass
        # Rebuild param frame
        for w in self.param_content.winfo_children():
            try:
                w.configure(bg=c['panel_bg'])
            except:
                pass
