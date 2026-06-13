# -*- coding: utf-8 -*-
"""
媒体下载模块 v1.0
支持平台：抖音/TikTok、快手、小红书、X/Twitter
功能：下载视频（去水印）、下载图片、复制文案
"""

import os
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import threading


# ==================== 核心下载引擎 ====================

def parse_urls(text):
    """从文本中提取所有URL"""
    urls = re.findall(r"https?://[^\s\u4e00-\u9fff\uff00-\uffef\u3000-\u303f]+", text)
    return list(set(urls))


def _get_ydl_opts(output_dir, quality="best", extract_audio=False):
    """获取 yt-dlp 通用参数"""
    if quality == "best":
        format_spec = "bestvideo*+bestaudio/best"
    elif quality == "1080p":
        format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
    elif quality == "720p":
        format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]"
    elif quality == "480p":
        format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]"
    else:
        format_spec = "best"

    opts = {
        "outtmpl": os.path.join(output_dir, "%(title)s_%(id)s.%(ext)s"),
        "format": format_spec,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "ignoreerrors": True,
        "nooverwrites": False,
    }

    if extract_audio:
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    return opts

def download_media(url, output_dir, quality="best", extract_audio=False, progress_callback=None):
    """下载媒体文件（视频/音频）
    返回：(成功标志, 消息, 文件路径列表)
    """
    try:
        from yt_dlp import YoutubeDL

        def progress_hook(d):
            if d["status"] == "downloading":
                try:
                    total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                    downloaded = d.get("downloaded_bytes", 0)
                    if total > 0 and progress_callback:
                        progress_callback(downloaded, total)
                except:
                    pass

        opts = _get_ydl_opts(output_dir, quality, extract_audio)
        opts["progress_hooks"] = [progress_hook]

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return False, "无法解析链接，请检查URL是否正确", []

            title = info.get("title", "未知标题")
            entries = info.get("entries", None)
            if entries is not None:
                total = len(entries)
                downloaded_files = []
                for idx, entry in enumerate(entries):
                    if entry is None:
                        continue
                    try:
                        ydl.download([entry["webpage_url"]])
                        _f = find_file(output_dir, entry)
                        if _f:
                            downloaded_files.append(_f)
                    except:
                        pass
                    if progress_callback:
                        progress_callback(idx + 1, total)
                return True, f"合集下载完成，共 {len(downloaded_files)} 个文件", downloaded_files
            else:
                # 直接 extract_info with download=True 下载并返回信息
                result = ydl.extract_info(url, download=True)
                if result:
                    f = find_file(output_dir, result)
                    title = result.get("title", title)
                    if not f:
                        f = find_file(output_dir, {})
                    files_list = [f] if f else []
                    return (True, f"下载完成: {title}", files_list)
                return True, "下载完成", []

    except Exception as e:
        error_msg = str(e)
        if "Unsupported URL" in error_msg:
            return False, "不支持该链接，请检查平台是否兼容", []
        elif "HTTP Error 403" in error_msg:
            return False, "访问被拒绝(403)，链接可能已失效或需登录", []
        elif "private" in error_msg.lower() or "login" in error_msg.lower():
            return False, "该内容为私密/需要登录才能下载", []
        elif "copyright" in error_msg.lower():
            return False, "该视频受版权保护，无法下载", []
        elif "No video formats found" in error_msg:
            return False, "未找到可下载的视频格式，链接可能失效", []
        elif "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            return False, "连接超时，请检查网络后重试", []
        return False, f"下载失败: {error_msg[:200]}", []


def find_file(output_dir, info=None):
    """找到最近下载的视频文件（取匹配 id 或最新 mp4）"""
    video_id = (info or {}).get("id", "")

    if not os.path.isdir(output_dir):
        return None

    # 精确匹配 video_id（最可靠）
    for f in os.listdir(output_dir):
        fp = os.path.join(output_dir, f)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext not in (".mp4", ".mkv", ".webm", ".mov"):
            continue
        if video_id and video_id in f:
            return fp

    # 取最新修改时间的视频文件
    import time
    now = time.time()
    best = None
    best_age = float("inf")
    for f in os.listdir(output_dir):
        fp = os.path.join(output_dir, f)
        if not os.path.isfile(fp):
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext not in (".mp4", ".mkv", ".webm", ".mov"):
            continue
        age = now - os.path.getmtime(fp)
        if age < best_age:
            best_age = age
            best = fp

    return best

# ==================== 平台检测与URL解析 ====================

PLATFORM_PATTERNS = [
    ("抖音/TikTok", ["douyin.com", "tiktok.com", "iesdouyin.com"]),
    ("快手", ["kuaishou.com", "kwai.com"]),
    ("小红书", ["xiaohongshu.com", "xhslink.com"]),
    ("X/Twitter", ["twitter.com", "x.com"]),
    ("B站", ["bilibili.com", "b23.tv"]),
    ("YouTube", ["youtube.com", "youtu.be"]),
    ("微博", ["weibo.com"]),
]



def preview_url(url):
    """Preview link info without downloading"""
    try:
        from yt_dlp import YoutubeDL
        opts = {"quiet": True, "no_warnings": True, "extract_flat": False, "ignoreerrors": True}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            heights = sorted(set(f.get("height", 0) for f in (info.get("formats") or []) if f.get("height")), reverse=True)
            entries = info.get("entries")
            return {
                "title": info.get("title", ""),
                "duration": info.get("duration", 0),
                "heights": heights,
                "extractor": info.get("extractor", ""),
                "description": (info.get("description") or "")[:200],
                "is_playlist": entries is not None,
                "thumbnail": info.get("thumbnail", ""),
            }
    except Exception as e:
        return {"error": str(e)[:100]}

def detect_platform(url):
    """检测链接对应的平台"""
    url_lower = url.lower()
    for platform, domains in PLATFORM_PATTERNS:
        for domain in domains:
            if domain in url_lower:
                return platform
    return "其他"


# ==================== 文案提取 ====================

def extract_caption(url, timeout=15):
    """提取视频/帖子的文案描述"""
    try:
        from yt_dlp import YoutubeDL
        opts = {
            "quiet": True, "no_warnings": True,
            "extract_flat": True, "ignoreerrors": True,
            "socket_timeout": timeout,
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return False, ""

            title = info.get("title", "")
            description = info.get("description", "") or ""
            caption = title
            if description:
                clean_desc = re.sub(r"https?://\S+", "", description)
                clean_desc = re.sub(r"#\S+", "", clean_desc)
                clean_desc = clean_desc.strip()
                if clean_desc and clean_desc != title:
                    caption = title + "\n" + clean_desc
            return True, caption.strip()
    except Exception as e:
        return False, str(e)


# ==================== 下载图片 ====================

def download_images(url, output_dir, progress_callback=None):
    """从帖子链接下载图片"""
    try:
        from yt_dlp import YoutubeDL
        opts = {
            "quiet": True, "no_warnings": True,
            "extract_flat": False, "ignoreerrors": True,
            "outtmpl": os.path.join(output_dir, "%(id)s_%(page_number)s.%(ext)s"),
        }
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return False, "无法解析链接", []

            entries = info.get("entries")
            if entries:
                downloaded = []
                total = len(entries)
                for idx, entry in enumerate(entries):
                    if entry is None:
                        continue
                    try:
                        ydl.download([entry["webpage_url"]])
                    except:
                        pass
                    if progress_callback:
                        progress_callback(idx + 1, total)
                return True, f"共 {len(downloaded)} 张图片", downloaded

            # 尝试缩略图
            thumbnails = info.get("thumbnails", [])
            if thumbnails:
                best_thumb = max(thumbnails, key=lambda x: x.get("height", 0) * x.get("width", 0) if x.get("height") else 0)
                thumb_url = best_thumb.get("url", "")
                if thumb_url:
                    import requests
                    resp = requests.get(thumb_url, timeout=15)
                    if resp.status_code == 200:
                        ext = Path(thumb_url.split("?")[0]).suffix or ".jpg"
                        fname = info.get("id", "image") + ext
                        fpath = os.path.join(output_dir, fname)
                        with open(fpath, "wb") as f:
                            f.write(resp.content)
                        return True, "封面图下载完成", [fpath]
            return False, "未找到可下载的图片", []
    except Exception as e:
        return False, f"图片下载失败: {str(e)}", []

# ==================== GUI 界面 ====================

class MediaToolFrame(ttk.Frame):
    """预览优先的媒体下载器"""

    def __init__(self, parent, theme):
        super().__init__(parent)
        self.theme = theme
        self.last_output_dir = ""
        self._last_caption = ""
        self._build_ui()

    def _build_ui(self):
        c = self.theme.colors

        tf = tk.Frame(self, bg=c["panel_bg"])
        tf.pack(fill="x", pady=(0, 8))
        tk.Label(tf, text="🌐 跨平台媒体下载器", font=("Microsoft YaHei", 14, "bold"),
                 bg=c["panel_bg"], fg=c["fg"]).pack(anchor="w")
        tk.Label(tf, text="支持抖音/TikTok · 快手 · 小红书 · X/Twitter · B站 · YouTube",
                 font=("Microsoft YaHei", 8), bg=c["panel_bg"], fg="#888888").pack(anchor="w")

        main_area = tk.Frame(self, bg=c["panel_bg"])
        main_area.pack(fill="both", expand=True)

        # === 左列 ===
        left = tk.Frame(main_area, bg=c["panel_bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # 链接输入
        tk.Label(left, text="🔗 粘贴链接：", font=("Microsoft YaHei", 9),
                 bg=c["panel_bg"], fg=c["fg"], anchor="w").pack(fill="x")
        lf = tk.Frame(left, bg=c["panel_bg"])
        lf.pack(fill="x", pady=(0, 6))
        self.url_text = tk.Text(lf, height=2, font=("Microsoft YaHei", 10),
                                bg=c["input_bg"], fg=c["fg"],
                                relief="solid", bd=1, wrap="word")
        self.url_text.pack(fill="both", expand=True, side="left")
        bf = tk.Frame(lf, bg=c["panel_bg"])
        bf.pack(side="right", padx=(4, 0), fill="y")
        tk.Button(bf, text="📋 粘贴", command=self._paste,
                  bg=c["accent"], fg="white", font=("Microsoft YaHei", 9),
                  relief="flat", padx=8, pady=2, cursor="hand2").pack(fill="x")
        tk.Button(bf, text="🔍 解析", command=self._do_preview,
                  bg="#E65100", fg="white", font=("Microsoft YaHei", 9, "bold"),
                  relief="flat", padx=8, pady=2, cursor="hand2").pack(fill="x", pady=(3, 0))

        # === 预览区（可滚动） ===
        self.preview_frame = tk.LabelFrame(left, text="📋 解析结果",
                                            font=("Microsoft YaHei", 9, "bold"),
                                            bg=c["panel_bg"], fg=c["fg"], padx=8, pady=5)
        self.preview_frame.pack(fill="both", expand=True, pady=(0, 6))

        pc = tk.Canvas(self.preview_frame, bg=c["panel_bg"], highlightthickness=0)
        ps = tk.Scrollbar(self.preview_frame, orient="vertical", command=pc.yview)
        self.preview_inner = tk.Frame(pc, bg=c["panel_bg"])
        self.preview_inner.bind('<Configure>', lambda e: pc.configure(scrollregion=pc.bbox('all')))
        pc.create_window((0, 0), window=self.preview_inner, anchor="nw", width=340)
        pc.configure(yscrollcommand=ps.set)
        pc.pack(side="left", fill="both", expand=True)
        ps.pack(side="right", fill="y")

        self.preview_label = tk.Label(self.preview_inner,
            text="👆 点击「解析」查看内容信息\n支持：视频画质/时长/平台/文案预览",
            font=("Microsoft YaHei", 9), bg=c["panel_bg"],
            fg="#888888", anchor="w", justify="left", wraplength=320)
        self.preview_label.pack(fill="x", padx=5, pady=5)

        # === 下载选项（解析成功后展开） ===
        self.opt_frame = tk.LabelFrame(left, text="📥 下载选项",
                                        font=("Microsoft YaHei", 9, "bold"),
                                        bg=c["panel_bg"], fg=c["fg"], padx=10, pady=6)

        # 下载类型（多选框）
        type_frame = tk.Frame(self.opt_frame, bg=c["panel_bg"])
        type_frame.pack(fill="x", pady=2)
        tk.Label(type_frame, text="选择下载：", font=("Microsoft YaHei", 9),
                 bg=c["panel_bg"], fg=c["fg"]).pack(side="left")
        self.dl_types = {}
        for key, label in [("video", "🎬视频"), ("image", "🖼图片"),
                             ("caption", "📝文案"), ("audio", "🎵音频")]:
            var = tk.BooleanVar(value=True)
            self.dl_types[key] = var
            tk.Checkbutton(type_frame, text=label, variable=var,
                          bg=c["panel_bg"], fg=c["fg"], selectcolor=c["input_bg"],
                          font=("Microsoft YaHei", 9)).pack(side="left", padx=2)

        # 画质
        qf = tk.Frame(self.opt_frame, bg=c["panel_bg"])
        qf.pack(fill="x", pady=2)
        tk.Label(qf, text="画质：", font=("Microsoft YaHei", 9),
                 bg=c["panel_bg"], fg=c["fg"]).pack(side="left")
        self.q_var = tk.StringVar(value="最佳画质")
        self.q_menu = ttk.Combobox(qf, textvariable=self.q_var,
                                    values=["最佳画质", "1080p", "720p", "480p"],
                                    state="readonly", width=14, font=("Microsoft YaHei", 9))
        self.q_menu.pack(side="left", padx=5)
        self.q_menu.current(0)

        # 目录
        df = tk.Frame(self.opt_frame, bg=c["panel_bg"])
        df.pack(fill="x", pady=2)
        tk.Label(df, text="目录：", font=("Microsoft YaHei", 9),
                 bg=c["panel_bg"], fg=c["fg"]).pack(side="left")
        self.dir_var = tk.StringVar(value=os.path.join(os.path.expanduser("~"), "Desktop", "极简办公_下载"))
        tk.Entry(df, textvariable=self.dir_var, font=("Microsoft YaHei", 9),
                 bg=c["input_bg"], fg=c["fg"], relief="solid", bd=1).pack(side="left", fill="x", expand=True, padx=(3,4))
        tk.Button(df, text="📂", command=self._choose_dir,
                  bg=c["accent"], fg="white", font=("Microsoft YaHei", 9),
                  relief="flat", padx=6, pady=0, cursor="hand2").pack(side="right")

        # 下载按钮（默认禁用）
        self.btn_dl = tk.Button(left, text="⏳ 请先解析",
                                bg="#888888", fg="white",
                                font=("Microsoft YaHei", 12, "bold"),
                                relief="flat", padx=20, pady=8, cursor="hand2",
                                state="disabled")
        self.btn_dl.pack(fill="x", pady=(3, 3))

        # 进度
        pf = tk.Frame(left, bg=c["panel_bg"])
        pf.pack(fill="x")
        self.progress_var = tk.DoubleVar()
        ttk.Progressbar(pf, variable=self.progress_var, maximum=100).pack(fill="x")
        self.status_var = tk.StringVar(value="🟢 就绪")
        tk.Label(pf, textvariable=self.status_var,
                 font=("Microsoft YaHei", 8), bg=c["panel_bg"], fg="#888888").pack(anchor="w")

        # === 右列：日志 ===
        right = tk.Frame(main_area, bg=c["panel_bg"])
        right.pack(side="right", fill="both", expand=True)

        tk.Label(right, text="📋 下载记录", font=("Microsoft YaHei", 9, "bold"),
                 bg=c["panel_bg"], fg=c["fg"], anchor="w").pack(fill="x")
        rf = tk.Frame(right, bg=c["panel_bg"])
        rf.pack(fill="both", expand=True)
        self.log_text = tk.Text(rf, font=("Microsoft YaHei", 9), bg=c["input_bg"], fg=c["fg"],
                                relief="solid", bd=1, wrap="word", state="disabled")
        self.log_text.pack(fill="both", expand=True, side="left")
        sc = tk.Scrollbar(rf, command=self.log_text.yview)
        sc.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=sc.set)

        # 底部按钮
        af = tk.Frame(right, bg=c["panel_bg"])
        af.pack(fill="x", pady=(5, 0))
        self.btn_open = tk.Button(af, text="📂 打开目录", command=self._open_dir,
                                  bg=c["accent"], fg="white", font=("Microsoft YaHei", 9),
                                  relief="flat", padx=8, pady=3, cursor="hand2", state="disabled")
        self.btn_open.pack(side="left", padx=(0, 4))
        self.btn_copy = tk.Button(af, text="📋 复制文案", command=self._copy_cap,
                                  bg="#0F9D58", fg="white", font=("Microsoft YaHei", 9),
                                  relief="flat", padx=8, pady=3, cursor="hand2", state="disabled")
        self.btn_copy.pack(side="left", padx=(0, 4))
        tk.Button(af, text="🗑️ 清空", command=self._clear_log,
                  bg=c["warning"], fg="white", font=("Microsoft YaHei", 9),
                  relief="flat", padx=8, pady=3, cursor="hand2").pack(side="left")

        self._log("🟢 媒体下载器已就绪\n粘贴链接 → 点击「解析」预览 → 勾选内容 → 下载")


    def _paste(self):
        try:
            t = self.clipboard_get()
            if t:
                self.url_text.delete("1.0", "end")
                self.url_text.insert("1.0", t.strip())
                self._do_preview()
        except:
            pass

    def _choose_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.dir_var.set(d)

    def _log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self.btn_open.config(state="disabled")
        self.btn_copy.config(state="disabled")

    def _open_dir(self):
        d = self.last_output_dir or self.dir_var.get()
        if d and os.path.exists(d):
            os.startfile(d)

    def _copy_cap(self):
        if self._last_caption:
            self.clipboard_clear()
            self.clipboard_append(self._last_caption)
            self._log("✅ 文案已复制到剪贴板")
            self.status_var.set("文案已复制 ✓")
        else:
            messagebox.showinfo("提示", "暂无文案内容")

    def _do_preview(self):
        raw = self.url_text.get("1.0", "end").strip()
        urls = parse_urls(raw)
        if not urls:
            messagebox.showwarning("提示", "未检测到链接")
            return
        url = urls[0]
        platform = detect_platform(url)
        self._log(f"🔍 解析中: {url[:60]}...")
        self.preview_label.config(text="⏳ 解析中，请稍候...", fg="#888888")
        self.status_var.set("解析中...")
        import threading
        threading.Thread(target=self._preview_work, args=(url, platform), daemon=True).start()

    def _preview_work(self, url, platform):
        info = preview_url(url)
        self.after(0, lambda: self._show_preview(info, platform, url))

    def _show_preview(self, info, platform, url):
        c = self.theme.colors
        if not info or "error" in info:
            err = (info or {}).get("error", "未知错误")
            self.preview_label.config(text=f"❌ 解析失败: {err}", fg=c["error"])
            self._log(f"❌ 解析失败: {err}")
            self.status_var.set("解析失败 ❌")
            return

        title = info.get("title", "") or ""
        duration = info.get("duration", 0)
        heights = info.get("heights", [])
        desc = info.get("description", "") or ""

        lines = [f"🌐 平台: {platform}"]
        lines.append(f"📌 标题: {title[:60]}")
        if duration:
            m, s = divmod(int(duration), 60)
            lines.append(f"⏱ 时长: {m}分{s}秒")
        if heights:
            lines.append(f"🎬 画质: {' / '.join(str(h)+'p' for h in heights[:5])}")
        if desc:
            lines.append(f"📝 描述: {desc[:80]}")

        self.preview_label.config(text="\n".join(lines), fg=c["fg"])

        # Show download options
        for child in self.opt_frame.winfo_children():
            child.destroy()
        self._build_dl_options()

        self.opt_frame.pack(fill="x", pady=(0, 6))
        self.btn_dl.config(text="📥 批量下载", bg="#0F9D58", state="normal", command=self._start_dl)

        self._log(f"✅ 解析成功: {title[:50]}")
        self.status_var.set("解析完成 ✓ 请勾选下载内容")

    def _build_dl_options(self):
        """Rebuild download options inside opt_frame"""
        c = self.theme.colors

        type_frame = tk.Frame(self.opt_frame, bg=c["panel_bg"])
        type_frame.pack(fill="x", pady=2)
        tk.Label(type_frame, text="选择下载：", font=("Microsoft YaHei", 9),
                 bg=c["panel_bg"], fg=c["fg"]).pack(side="left")
        self.dl_types = {}
        for key, label in [("video", "🎬视频"), ("image", "🖼图片"),
                            ("caption", "📝文案"), ("audio", "🎵音频")]:
            var = tk.BooleanVar(value=True)
            self.dl_types[key] = var
            tk.Checkbutton(type_frame, text=label, variable=var,
                          bg=c["panel_bg"], fg=c["fg"], selectcolor=c["input_bg"],
                          font=("Microsoft YaHei", 9)).pack(side="left", padx=2)

        qf = tk.Frame(self.opt_frame, bg=c["panel_bg"])
        qf.pack(fill="x", pady=2)
        tk.Label(qf, text="画质：", font=("Microsoft YaHei", 9),
                 bg=c["panel_bg"], fg=c["fg"]).pack(side="left")
        self.q_var = tk.StringVar(value="最佳画质")
        self.q_menu = ttk.Combobox(qf, textvariable=self.q_var,
                                    values=["最佳画质", "1080p", "720p", "480p"],
                                    state="readonly", width=14, font=("Microsoft YaHei", 9))
        self.q_menu.pack(side="left", padx=5)
        self.q_menu.current(0)

    def _start_dl(self):
        raw = self.url_text.get("1.0", "end").strip()
        urls = parse_urls(raw)
        if not urls:
            return
        url = urls[0]
        out_dir = self.dir_var.get().strip()
        if not out_dir:
            out_dir = os.path.join(os.path.expanduser("~"), "Desktop", "极简办公_下载")
        os.makedirs(out_dir, exist_ok=True)

        qm = {"最佳画质": "best", "1080p": "1080p", "720p": "720p", "480p": "480p"}
        quality = qm.get(self.q_var.get(), "best")

        selected = [k for k, v in self.dl_types.items() if v.get()]
        if not selected:
            messagebox.showwarning("提示", "请至少选择一种下载类型")
            return

        self._log(f"\n{'='*40}")
        self._log(f"📥 开始下载 ({len(selected)} 种类型)")
        self._log(f"📂 保存到: {out_dir}")

        self.btn_dl.config(state="disabled", text="⏳ 下载中...")
        self.progress_var.set(0)
        self.status_var.set("下载中...")

        import threading
        threading.Thread(target=self._process,
                        args=(url, out_dir, selected, quality), daemon=True).start()

    def _process(self, url, out_dir, types, quality):
        labels = {"video": "🎬视频", "image": "🖼图片", "caption": "📝文案", "audio": "🎵音频"}
        try:
            for idx, dl_type in enumerate(types):
                label = labels.get(dl_type, dl_type)
                self.after(0, lambda l=label, i=idx+1, t=len(types):
                    self._log(f"\n[{i}/{t}] 📥 {l}..."))
                self.after(0, lambda: self.progress_var.set((idx / len(types)) * 100))

                if dl_type == "caption":
                    self._dl_caption(url, out_dir)
                elif dl_type == "image":
                    self._dl_images(url, out_dir)
                elif dl_type == "audio":
                    self._dl_audio(url, out_dir, quality)
                else:
                    self._dl_video(url, out_dir, quality)

            self.after(0, lambda: self._log(f"\n🎉 全部完成!"))
            self.after(0, lambda: self.status_var.set("全部完成 🎉"))
        except Exception as e:
            self.after(0, lambda: self._log(f"❌ 错误: {str(e)[:100]}"))
            self.after(0, lambda: self.status_var.set("出错 ❌"))
        finally:
            self.after(0, lambda: self.btn_dl.config(state="normal", text="📥 下载"))
            self.after(0, lambda: self.progress_var.set(100))

    def _dl_video(self, url, out_dir, quality):
        def cb(cur, tot):
            if tot > 0:
                self.after(0, lambda: self.progress_var.set(cur / tot * 99))
        ok, msg, files = download_media(url, out_dir, quality, False, cb)
        self.after(0, lambda: self._log(f"{'✅' if ok else '❌'} {msg}"))
        if ok and files:
            self.last_output_dir = out_dir
            self.after(0, lambda: self.btn_open.config(state="normal"))
            for f in files[:3]:
                sz = os.path.getsize(f)/1024/1024 if f and os.path.exists(f) else 0
                self.after(0, lambda f=f: self._log(f"  📄 {os.path.basename(f)[:50]}"))

    def _dl_images(self, url, out_dir):
        def cb(cur, tot):
            if tot > 0:
                self.after(0, lambda: self.progress_var.set(cur/tot*100))
        ok, msg, files = download_images(url, out_dir, cb)
        self.after(0, lambda: self._log(f"{'✅' if ok else '❌'} {msg}"))
        if ok and files:
            self.last_output_dir = out_dir
            self.after(0, lambda: self.btn_open.config(state="normal"))

    def _dl_audio(self, url, out_dir, quality):
        def cb(cur, tot):
            if tot > 0:
                self.after(0, lambda: self.progress_var.set(cur/tot*100))
        ok, msg, files = download_media(url, out_dir, quality, True, cb)
        self.after(0, lambda: self._log(f"{'✅' if ok else '❌'} {msg}"))
        if ok and files:
            self.last_output_dir = out_dir
            self.after(0, lambda: self.btn_open.config(state="normal"))

    def _dl_caption(self, url, out_dir):
        ok, cap = extract_caption(url)
        if ok and cap:
            self._last_caption = cap
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            fp = os.path.join(out_dir, f"文案_{ts}.txt")
            with open(fp, "w", encoding="utf-8") as f:
                f.write(cap)
            self.after(0, lambda: self._log("✅ 文案提取成功"))
            preview = cap[:150] + ("..." if len(cap) > 150 else "")
            self.after(0, lambda: self._log(f"📝 {preview}"))
            self.after(0, lambda: self._log(f"💾 已保存: {os.path.basename(fp)}"))
            self.after(0, lambda: self.btn_copy.config(state="normal"))
            self.last_output_dir = out_dir
            self.after(0, lambda: self.btn_open.config(state="normal"))
        else:
            self.after(0, lambda: self._log(f"❌ 文案提取失败: {cap[:60] if cap else '未知'}"))


    def apply_theme(self):
        c = self.theme.colors
        try:
            self.url_text.config(bg=c["input_bg"], fg=c["fg"])
            self.log_text.config(bg=c["input_bg"], fg=c["fg"])
        except:
            pass
