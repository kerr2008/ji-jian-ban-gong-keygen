"""
闲鱼工具箱 - 主题管理（深色/浅色模式）
"""

import tkinter as tk
from tkinter import ttk

# 浅色主题颜色
LIGHT_COLORS = {
    'bg': '#F5F5F5',
    'fg': '#333333',
    'sidebar_bg': '#FFFFFF',
    'sidebar_fg': '#333333',
    'sidebar_hover': '#E8F0FE',
    'sidebar_selected': '#D2E3FC',
    'accent': '#1A73E8',
    'accent_hover': '#1557B0',
    'panel_bg': '#FFFFFF',
    'panel_fg': '#333333',
    'border': '#E0E0E0',
    'success': '#0F9D58',
    'warning': '#F9AB00',
    'error': '#D93025',
    'progress_bg': '#E0E0E0',
    'progress_fill': '#1A73E8',
    'disabled_bg': '#F0F0F0',
    'disabled_fg': '#999999',
    'input_bg': '#FFFFFF',
    'input_fg': '#333333',
    'input_border': '#CCCCCC',
    'scrollbar': '#C0C0C0',
    'hover_bg': '#E8F0FE',
    'link': '#1A73E8',
}

# 深色主题颜色
DARK_COLORS = {
    'bg': '#1E1E1E',
    'fg': '#E0E0E0',
    'sidebar_bg': '#252526',
    'sidebar_fg': '#CCCCCC',
    'sidebar_hover': '#2D2D2D',
    'sidebar_selected': '#37373D',
    'accent': '#4FC3F7',
    'accent_hover': '#29B6F6',
    'panel_bg': '#2D2D2D',
    'panel_fg': '#E0E0E0',
    'border': '#404040',
    'success': '#81C784',
    'warning': '#FFD54F',
    'error': '#E57373',
    'progress_bg': '#404040',
    'progress_fill': '#4FC3F7',
    'disabled_bg': '#333333',
    'disabled_fg': '#666666',
    'input_bg': '#3C3C3C',
    'input_fg': '#E0E0E0',
    'input_border': '#555555',
    'scrollbar': '#555555',
    'hover_bg': '#2D2D2D',
    'link': '#4FC3F7',
}


class ThemeManager:
    """管理深色/浅色主题切换"""
    
    def __init__(self):
        self.is_dark = False
        self.colors = dict(LIGHT_COLORS)
    
    def toggle(self):
        """切换主题"""
        self.is_dark = not self.is_dark
        self.colors = dict(DARK_COLORS if self.is_dark else LIGHT_COLORS)
        return self.colors
    
    def get(self, key):
        return self.colors.get(key, '')
    
    def apply_to_widget(self, widget, widget_type='label'):
        """应用主题到单个组件"""
        c = self.colors
        try:
            if widget_type == 'label':
                widget.configure(bg=c['panel_bg'], fg=c['fg'])
            elif widget_type == 'frame':
                widget.configure(bg=c['panel_bg'])
            elif widget_type == 'sidebar_frame':
                widget.configure(bg=c['sidebar_bg'])
            elif widget_type == 'button':
                widget.configure(bg=c['accent'], fg='#FFFFFF', 
                                 activebackground=c['accent_hover'],
                                 activeforeground='#FFFFFF')
            elif widget_type == 'entry':
                widget.configure(bg=c['input_bg'], fg=c['input_fg'],
                                 insertbackground=c['fg'])
            elif widget_type == 'text':
                widget.configure(bg=c['input_bg'], fg=c['input_fg'],
                                 insertbackground=c['fg'])
            elif widget_type == 'checkbutton':
                widget.configure(bg=c['panel_bg'], fg=c['fg'],
                                 selectcolor=c['input_bg'])
            elif widget_type == 'listbox':
                widget.configure(bg=c['input_bg'], fg=c['input_fg'])
            elif widget_type == 'canvas':
                widget.configure(bg=c['panel_bg'])
        except:
            pass
    
    def apply_to_all(self, root, sidebar_frame, main_panel):
        """应用主题到所有主要组件"""
        c = self.colors
        root.configure(bg=c['bg'])
        sidebar_frame.configure(bg=c['sidebar_bg'])
        main_panel.configure(bg=c['panel_bg'])


def configure_ttk_styles(theme, style=None):
    """配置 ttk 组件的样式"""
    if style is None:
        style = ttk.Style()
    
    c = theme.colors
    prefix = 'dark' if theme.is_dark else 'light'
    
    # Treeview
    style.configure(f'{prefix}.Treeview',
                    background=c['input_bg'],
                    foreground=c['fg'],
                    fieldbackground=c['input_bg'],
                    borderwidth=0)
    style.configure(f'{prefix}.Treeview.Heading',
                    background=c['sidebar_bg'],
                    foreground=c['fg'],
                    borderwidth=1,
                    relief='solid')
    style.map(f'{prefix}.Treeview',
              background=[('selected', c['accent'])],
              foreground=[('selected', '#FFFFFF')])
    
    # Progress bar
    style.configure(f'{prefix}.Horizontal.TProgressbar',
                    background=c['progress_fill'],
                    troughcolor=c['progress_bg'],
                    borderwidth=0,
                    thickness=8)
    
    # LabelFrame
    style.configure(f'{prefix}.TLabelframe',
                    background=c['panel_bg'],
                    foreground=c['fg'],
                    bordercolor=c['border'])
    style.configure(f'{prefix}.TLabelframe.Label',
                    background=c['panel_bg'],
                    foreground=c['fg'])
    
    # Combobox
    style.configure(f'{prefix}.TCombobox',
                    fieldbackground=c['input_bg'],
                    background=c['input_bg'],
                    foreground=c['fg'],
                    arrowcolor=c['fg'])
    
    return style
