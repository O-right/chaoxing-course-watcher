"""学习通刷课助手的桌面界面。

只是 main.py 的外壳：把表单里的设置作为环境变量交给子进程运行 main.py，
实时显示日志和进度。登录、看课、完成判定和失败语义全部仍在 main.py 里。

启动：双击 start_ui.bat，或运行 python gui.py。
运行一次 python gui.py --create-shortcuts 可在桌面和开始菜单生成图标。
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import math
import os
import queue
import re
import signal
import struct
import subprocess
import sys
import threading
import time
import tkinter as tk
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import font as tkfont
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from dotenv import dotenv_values
except ImportError:  # 依赖没装时也要弹窗说明，而不是在 pythonw 下静默退出。
    dotenv_values = None


APP_NAME = "学习通刷课助手"
# 窗口和快捷方式共用，任务栏才会把它们当成同一个程序（图标、分组、固定都对得上）。
APP_ID = "O-right.ChaoxingCourseWatcher"

GUI_SCRIPT = Path(__file__).resolve()
ROOT = GUI_SCRIPT.parent
MAIN_SCRIPT = ROOT / "main.py"
ENV_PATH = ROOT / ".env"
ENV_EXAMPLE_PATH = ROOT / ".env.example"
UI_LOG_DIR = ROOT / "logs" / "ui"
DEFAULT_SCREENSHOT_DIR = "logs/screenshots"
ICON_PATH = ROOT / "app.ico"
ICON_SIZES = (16, 24, 32, 48, 64, 256)

BROWSER_CHOICES = (("Chrome", "chrome"), ("Edge", "msedge"), ("内置 Chromium", ""))
PLAYBACK_RATES = ("1.0", "1.25", "1.5", "2.0")
# 勾选"手动过验证码"时给的等待时间；.env 里已有正值就沿用它。
MANUAL_VERIFICATION_SECONDS = 300.0
MAX_CONSOLE_LINES = 4000


# ---------------------------------------------------------------------------
# 设置：表单 <-> .env <-> 子进程环境变量
# ---------------------------------------------------------------------------


@dataclass
class Settings:
    username: str = ""
    password: str = ""
    course_keyword: str = ""
    course_url: str = ""
    chapter_keyword: str = ""
    browser_channel: str = "chrome"
    playback_rate: str = "1.0"
    max_chapters: int = 100
    headless: bool = False
    fast_actions: bool = False
    manual_verification_seconds: float = 0.0


def _truthy(value: Optional[str]) -> bool:
    # 与 main.env_flag 的取值保持一致。
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def settings_from_env(values: Dict[str, Optional[str]]) -> Settings:
    """用 .env 里的值预填表单；读不懂的值回退默认，不报错。"""

    def text(key: str) -> str:
        return str(values.get(key) or "").strip()

    defaults = Settings()
    try:
        max_chapters = int(text("CX_MAX_CHAPTERS") or defaults.max_chapters)
    except ValueError:
        max_chapters = defaults.max_chapters
    try:
        manual_seconds = float(text("CX_MANUAL_VERIFICATION_WAIT_SECONDS") or 0)
    except ValueError:
        manual_seconds = 0.0
    browser_channel = text("CX_BROWSER_CHANNEL") if "CX_BROWSER_CHANNEL" in values else defaults.browser_channel
    return Settings(
        username=text("CX_USERNAME"),
        password=str(values.get("CX_PASSWORD") or ""),
        course_keyword=text("CX_COURSE_KEYWORD"),
        course_url=text("CX_COURSE_URL"),
        chapter_keyword=text("CX_CHAPTER_KEYWORD"),
        browser_channel=browser_channel,
        playback_rate=text("CX_PLAYBACK_RATE") or defaults.playback_rate,
        max_chapters=max(1, max_chapters),
        headless=_truthy(values.get("CX_HEADLESS")),
        fast_actions=_truthy(values.get("CX_FAST_ACTIONS")),
        manual_verification_seconds=max(0.0, manual_seconds),
    )


def parse_form(form: Dict[str, Any], previous_manual_seconds: float = 0.0) -> Settings:
    """把表单输入转换成 Settings；输入不完整时抛出带中文提示的 ValueError。"""
    username = str(form["username"]).strip()
    password = str(form["password"])
    if not username or not password:
        raise ValueError("请填写账号和密码。")
    course_keyword = str(form["course_keyword"]).strip()
    course_url = str(form["course_url"]).strip()
    if not course_keyword and not course_url:
        raise ValueError("请填写课程名称，或者课程链接。")
    if course_url and not re.match(r"https?://", course_url, re.IGNORECASE):
        raise ValueError("课程链接需要以 http:// 或 https:// 开头。")
    try:
        max_chapters = int(str(form["max_chapters"]).strip())
    except ValueError:
        max_chapters = 0
    if max_chapters < 1:
        raise ValueError("任务点上限需要是大于 0 的整数。")
    playback_rate = str(form["playback_rate"]).strip()
    try:
        rate_value = float(playback_rate)
    except ValueError:
        rate_value = 0.0
    if not 0 < rate_value <= 16:
        raise ValueError("倍速需要是 0 到 16 之间的数字。")
    headless = bool(form["headless"])
    manual_seconds = 0.0
    # 无头模式下看不到浏览器，没法手动过验证码，等也白等。
    if form["manual_verification"] and not headless:
        manual_seconds = previous_manual_seconds if previous_manual_seconds > 0 else MANUAL_VERIFICATION_SECONDS
    return Settings(
        username=username,
        password=password,
        course_keyword=course_keyword,
        course_url=course_url,
        chapter_keyword=str(form["chapter_keyword"]).strip(),
        browser_channel=str(form["browser_channel"]),
        playback_rate=playback_rate,
        max_chapters=max_chapters,
        headless=headless,
        fast_actions=bool(form["fast_actions"]),
        manual_verification_seconds=manual_seconds,
    )


def settings_to_env(settings: Settings) -> Dict[str, str]:
    return {
        "CX_USERNAME": settings.username,
        "CX_PASSWORD": settings.password,
        "CX_COURSE_KEYWORD": settings.course_keyword,
        "CX_COURSE_URL": settings.course_url,
        "CX_CHAPTER_KEYWORD": settings.chapter_keyword,
        "CX_BROWSER_CHANNEL": settings.browser_channel,
        "CX_PLAYBACK_RATE": settings.playback_rate,
        "CX_MAX_CHAPTERS": str(settings.max_chapters),
        "CX_HEADLESS": "true" if settings.headless else "false",
        "CX_FAST_ACTIONS": "true" if settings.fast_actions else "false",
        "CX_MANUAL_VERIFICATION_WAIT_SECONDS": f"{settings.manual_verification_seconds:g}",
    }


def build_child_env(base_env: Dict[str, str], settings: Settings) -> Dict[str, str]:
    """子进程环境：表单值全部显式给出。

    main.py 的 load_dotenv() 不覆盖已存在的环境变量，所以空字符串也要显式传——
    否则表单里清空的课程链接会被 .env 里的旧值顶回来。
    """
    env = dict(base_env)
    env.update(settings_to_env(settings))
    # 与 --browser-channel 一致：界面里选了浏览器，就不让 .env 里的可执行文件路径抢先。
    env["CX_BROWSER_EXECUTABLE_PATH"] = ""
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


_ENV_ASSIGNMENT = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")
_PLAIN_VALUE_PUNCTUATION = set("_-.,:/@%+=?&~")


def format_env_value(value: str) -> str:
    """写成 python-dotenv 能原样读回的形式：简单值不加引号，其余用单引号并转义。"""
    if all(ch.isalnum() or ch in _PLAIN_VALUE_PUNCTUATION for ch in value):
        return value
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def env_value_is_storable(value: str) -> bool:
    """有些值 python-dotenv 读不回原样，只能不存：

    - ${...} 在引号里也会被展开，且没有转义写法；
    - 以反斜杠结尾时，收尾的 \\' 会被当成转义引号，吞掉结束引号；
    - 换行会打乱按行更新。
    """
    return "${" not in value and not value.endswith("\\") and "\n" not in value and "\r" not in value


def update_env_text(text: str, updates: Dict[str, str]) -> str:
    """只改 updates 里的键，其余行（注释、别的项目的配置）原样保留。"""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    seen = set()
    for index, line in enumerate(lines):
        match = _ENV_ASSIGNMENT.match(line)
        if match and match.group(1) in updates:
            key = match.group(1)
            lines[index] = f"{key}={format_env_value(updates[key])}"
            seen.add(key)
    missing = [key for key in updates if key not in seen]
    if missing:
        if lines and lines[-1].strip():
            lines.append("")
        lines.append("# 以下由图形界面写入")
        lines.extend(f"{key}={format_env_value(updates[key])}" for key in missing)
    return newline.join(lines) + newline


def save_env_file(path: Path, updates: Dict[str, str], template: Optional[Path] = None) -> List[str]:
    """把能安全保存的键写进 .env，返回因无法安全保存而跳过的键。

    .env 不存在时以 .env.example 为底稿，保留里面的说明注释。
    """
    storable = {key: value for key, value in updates.items() if env_value_is_storable(value)}
    skipped = [key for key in updates if key not in storable]
    if path.exists():
        # 按字节读写，保留原有的换行风格。
        text = path.read_bytes().decode("utf-8")
    elif template is not None and template.exists():
        text = template.read_bytes().decode("utf-8")
    else:
        text = ""
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_bytes(update_env_text(text, storable).encode("utf-8"))
    os.replace(temp_path, path)
    return skipped


def read_env_values(path: Path) -> Dict[str, Optional[str]]:
    if dotenv_values is None or not path.exists():
        return {}
    try:
        return dict(dotenv_values(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ---------------------------------------------------------------------------
# 日志解析：只认 main.py 打印的固定措辞（tests/test_gui.py 会核对它们还在）
# ---------------------------------------------------------------------------

_MUTED_LINE = re.compile(r"^(?:播放进度:|等待 [\d.]+ 秒)")
_ERROR_MARKERS = ("失败", "异常", "超时", "拒绝", "无法", "缺失", "Traceback", "Error")
_WARNING_MARKERS = ("警告", "未找到", "未检测到", "未匹配", "未能", "重试", "可能", "拦截", "暂停", "人工处理", "达到最大")
_SUCCESS_MARKERS = ("成功", "已完成", "播放完成", "流程完成", "流程结束", "已检测到", "已切换")

_TASK_LINE = re.compile(r"开始处理第 (\d+) 个学习任务点")
_VIDEO_LINE = re.compile(r"开始处理当前页第 (\d+)/(\d+) 个视频")
_PROGRESS_LINE = re.compile(r"播放进度: ([\d.]+)/([\d.]+)s \(([\d.]+)%\), 倍速 ([\d.]+)")
_STAGE_MARKERS = (
    ("已打开登录页", "正在登录"),
    ("跳过表单登录", "正在打开课程"),
    ("登录成功", "正在打开课程"),
    ("通过配置的课程 URL 打开课程入口", "正在进入课程"),
    ("课程入口匹配来源", "正在进入课程"),
)


def classify_line(line: str) -> str:
    """给日志行挑颜色：muted / error / warning / success / plain。"""
    if _MUTED_LINE.match(line):
        return "muted"
    if any(marker in line for marker in _ERROR_MARKERS):
        return "error"
    if any(marker in line for marker in _WARNING_MARKERS):
        return "warning"
    if any(marker in line for marker in _SUCCESS_MARKERS):
        return "success"
    return "plain"


def format_clock(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_status_line(line: str) -> Dict[str, Any]:
    """从一行日志里提取界面要显示的状态；与状态无关的行返回空字典。"""
    match = _TASK_LINE.search(line)
    if match:
        return {"stage": "正在学习", "task": int(match.group(1)), "video": None, "video_detail": "", "percent": 0.0}
    match = _VIDEO_LINE.search(line)
    if match:
        return {"video": (int(match.group(1)), int(match.group(2))), "video_detail": "", "percent": 0.0}
    match = _PROGRESS_LINE.search(line)
    if match:
        current, duration, percent, rate = (float(group) for group in match.groups())
        return {
            "percent": min(100.0, percent),
            "video_detail": f"{format_clock(current)} / {format_clock(duration)} · {rate:g}x",
        }
    if "当前视频已播放完成" in line:
        return {"percent": 100.0}
    if "当前学习页未检测到视频" in line:
        return {"video": None, "video_detail": "非视频任务点", "percent": 0.0}
    if "已达到最大章节数" in line:
        return {"hit_cap": True}
    if "检测到平台验证拦截" in line:
        return {"stage": "需要验证", "attention": True}
    for marker, stage in _STAGE_MARKERS:
        if marker in line:
            return {"stage": stage}
    return {}


def summarize_exit(code: int, stopped: bool, hit_cap: bool) -> Tuple[str, str, str]:
    """把退出情况翻译成 (标题, 色调, 说明)。退出码约定见 README「退出码」。"""
    if stopped:
        return "已停止", "muted", "已手动停止。"
    if code == 0:
        return "已完成", "success", "课程任务点已处理完，建议到学习通里再确认一下进度。"
    if hit_cap:
        return "达到上限", "warning", "已处理到任务点上限，课程未必看完，可以调高上限后再运行一次。"
    return "运行失败", "error", "可以看看日志末尾和截图文件夹里的现场。"


# ---------------------------------------------------------------------------
# 子进程
# ---------------------------------------------------------------------------


def child_python() -> str:
    """pythonw 没有控制台输出，子进程改用同目录的 python.exe（配合 CREATE_NO_WINDOW 不弹窗）。"""
    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        console = executable.with_name("python.exe")
        if console.exists():
            return str(console)
    return str(executable)


class ProcessRunner:
    """在后台线程里跑子进程，把输出逐行放进队列，由界面线程定时取走。"""

    def __init__(self) -> None:
        self.process: Optional[subprocess.Popen] = None
        self.events: "queue.Queue[Tuple[str, Any]]" = queue.Queue()

    @property
    def running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def start(self, command: List[str], env: Dict[str, str], cwd: Path) -> None:
        options: Dict[str, Any] = {}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        else:
            options["start_new_session"] = True
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **options,
        )
        self.process = process
        reader = threading.Thread(target=self._read_output, args=(process,), daemon=True)
        reader.start()
        threading.Thread(target=self._wait_exit, args=(process, reader), daemon=True).start()

    def _read_output(self, process: subprocess.Popen) -> None:
        with process.stdout:
            for raw in iter(process.stdout.readline, b""):
                self.events.put(("line", raw.decode("utf-8", errors="replace").rstrip("\r\n")))

    def _wait_exit(self, process: subprocess.Popen, reader: threading.Thread) -> None:
        code = process.wait()
        # 浏览器驱动之类的孙进程可能还握着管道；给读线程一点时间吐完剩余输出，但不无限等。
        reader.join(timeout=3)
        self.events.put(("exit", code))

    def stop(self) -> None:
        process = self.process
        if process is None or process.poll() is not None:
            return
        if os.name == "nt":
            # /T 连带结束 Playwright 驱动和它启动的浏览器，不留孤儿 Chrome。
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            os.killpg(process.pid, signal.SIGTERM)


# ---------------------------------------------------------------------------
# 界面
# ---------------------------------------------------------------------------

PALETTE = {
    "bg": "#F3F4F6",
    "card": "#FFFFFF",
    "field": "#FFFFFF",
    "border": "#E5E7EB",
    "border_strong": "#D1D5DB",
    "text": "#111827",
    "muted": "#6B7280",
    "subtle": "#9CA3AF",
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_pressed": "#1E40AF",
    "accent_disabled": "#BFDBFE",
    "track": "#E5E7EB",
    "success": "#16A34A",
    "warning": "#D97706",
    "error": "#DC2626",
    "error_soft": "#FEF2F2",
    "ghost_hover": "#F3F4F6",
    "tooltip_bg": "#111827",
    "tooltip_text": "#F9FAFB",
    "console_bg": "#0F172A",
    "console_text": "#CBD5E1",
    "console_time": "#475569",
    "console_muted": "#64748B",
    "console_info": "#93C5FD",
    "console_success": "#4ADE80",
    "console_warning": "#FBBF24",
    "console_error": "#F87171",
    "console_thumb": "#334155",
    "console_thumb_hover": "#475569",
}

TONE_COLORS = {
    "idle": PALETTE["muted"],
    "muted": PALETTE["muted"],
    "running": PALETTE["accent"],
    "success": PALETTE["success"],
    "warning": PALETTE["warning"],
    "error": PALETTE["error"],
}

FONT_FAMILIES = ("Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC")


class Tooltip:
    """鼠标停留时显示的说明气泡。"""

    def __init__(self, widget: tk.Widget, text: str, font: tkfont.Font, pad: int) -> None:
        self.widget = widget
        self.text = text
        self.font = font
        self.pad = pad
        self.window: Optional[tk.Toplevel] = None
        self.pending: Optional[str] = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event: Any = None) -> None:
        self._cancel()
        self.pending = self.widget.after(450, self._show)

    def _cancel(self) -> None:
        if self.pending:
            self.widget.after_cancel(self.pending)
            self.pending = None

    def _show(self) -> None:
        self.pending = None
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + self.pad // 2
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self.window,
            text=self.text,
            justify="left",
            wraplength=self.pad * 28,
            bg=PALETTE["tooltip_bg"],
            fg=PALETTE["tooltip_text"],
            font=self.font,
            padx=self.pad,
            pady=self.pad * 2 // 3,
        ).pack()

    def _hide(self, _event: Any = None) -> None:
        self._cancel()
        if self.window is not None:
            self.window.destroy()
            self.window = None


def icon_rows(size: int) -> List[bytes]:
    """画应用图标：蓝色渐变圆角方块 + 白色播放键，按像素覆盖率抗锯齿。返回每行的 RGBA 字节。"""
    margin = size / 16
    half_extent = size / 2 - margin
    radius = half_extent * 0.44
    top, bottom = _rgb("#3B82F6"), _rgb(PALETTE["accent"])
    # 播放键三角形按 32px 设计稿等比缩放，质心落在正中。
    triangle = [(0.375 * size, 0.28 * size), (0.375 * size, 0.72 * size), (0.75 * size, 0.5 * size)]
    edges = []
    for (ax, ay), (bx, by) in zip(triangle, triangle[1:] + triangle[:1]):
        length = math.hypot(bx - ax, by - ay)
        nx, ny = (by - ay) / length, (ax - bx) / length
        if (size / 2 - ax) * nx + (size / 2 - ay) * ny > 0:
            nx, ny = -nx, -ny  # 法线朝外，三角形内部距离为负
        edges.append((ax, ay, nx, ny))
    rows = []
    for py in range(size):
        y = py + 0.5
        t = py / max(1, size - 1)
        base = [round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
        row = bytearray()
        for px in range(size):
            x = px + 0.5
            qx = abs(x - size / 2) - (half_extent - radius)
            qy = abs(y - size / 2) - (half_extent - radius)
            box = math.hypot(max(qx, 0.0), max(qy, 0.0)) + min(max(qx, qy), 0.0) - radius
            alpha = min(1.0, max(0.0, 0.5 - box))
            mark = max((x - ax) * nx + (y - ay) * ny for ax, ay, nx, ny in edges)
            white = min(1.0, max(0.0, 0.5 - mark))
            row.extend(round(channel + (255 - channel) * white) for channel in base)
            row.append(round(alpha * 255))
        rows.append(bytes(row))
    return rows


def icon_png(size: int) -> bytes:
    """把图标编码成 PNG（RGBA），给 Tk 窗口和 .ico 共用。"""
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + row for row in icon_rows(size))
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def icon_ico(sizes: Tuple[int, ...] = ICON_SIZES) -> bytes:
    """多尺寸 .ico（内嵌 PNG），给桌面和开始菜单快捷方式用。"""
    images = [icon_png(size) for size in sizes]
    offset = 6 + 16 * len(images)
    entries = []
    for size, image in zip(sizes, images):
        entries.append(struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(image), offset))
        offset += len(image)
    return struct.pack("<HHH", 0, 1, len(images)) + b"".join(entries) + b"".join(images)


def make_icons(root: tk.Tk) -> List[tk.PhotoImage]:
    """窗口标题栏和任务栏图标，给几种尺寸让系统按缩放挑。"""
    return [tk.PhotoImage(master=root, data=base64.b64encode(icon_png(size)).decode("ascii")) for size in (64, 32, 16)]


def _rgb(color: str) -> Tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def make_checkbox_image(root: tk.Tk, size: int, gap: int, fill: str, border: str,
                        mark: Optional[str], background: str) -> tk.PhotoImage:
    """画一个圆角复选框，右侧留 gap 像素空白当作与文字的间距。4x4 超采样做抗锯齿。"""
    radius = size * 0.22
    border_width = max(1.0, size / 14)
    half_stroke = size * 0.065
    points = [(0.26 * size, 0.52 * size), (0.43 * size, 0.69 * size), (0.75 * size, 0.34 * size)]
    segments = list(zip(points, points[1:]))

    def in_rounded_rect(x: float, y: float, inset: float) -> bool:
        low, high = inset, size - inset
        corner = max(0.0, radius - inset)
        nearest_x = min(max(x, low + corner), high - corner)
        nearest_y = min(max(y, low + corner), high - corner)
        return low <= x <= high and low <= y <= high and (x - nearest_x) ** 2 + (y - nearest_y) ** 2 <= corner**2

    def on_mark(x: float, y: float) -> bool:
        for (ax, ay), (bx, by) in segments:
            dx, dy = bx - ax, by - ay
            t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
            if (x - ax - t * dx) ** 2 + (y - ay - t * dy) ** 2 <= half_stroke**2:
                return True
        return False

    colors = {name: _rgb(value) for name, value in
              (("fill", fill), ("border", border), ("mark", mark or fill), ("background", background))}
    samples = 4
    rows = []
    for py in range(size):
        row = []
        for px in range(size):
            total = [0, 0, 0]
            for sy in range(samples):
                for sx in range(samples):
                    x, y = px + (sx + 0.5) / samples, py + (sy + 0.5) / samples
                    if mark and on_mark(x, y):
                        name = "mark"
                    elif in_rounded_rect(x, y, border_width):
                        name = "fill"
                    elif in_rounded_rect(x, y, 0):
                        name = "border"
                    else:
                        name = "background"
                    for channel in range(3):
                        total[channel] += colors[name][channel]
            row.append("#%02x%02x%02x" % tuple(round(value / samples**2) for value in total))
        row.extend([background] * gap)
        rows.append("{" + " ".join(row) + "}")
    image = tk.PhotoImage(master=root, width=size + gap, height=size)
    image.put(" ".join(rows))
    return image


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.runner = ProcessRunner()
        self.scale = max(1.0, root.winfo_fpixels("1i") / 96)
        self.env_values = read_env_values(ENV_PATH)
        initial = settings_from_env(self.env_values)
        self.previous_manual_seconds = initial.manual_verification_seconds
        self.screenshot_dir = ROOT / (self.env_values.get("CX_SCREENSHOT_DIR") or DEFAULT_SCREENSHOT_DIR)

        self.browser_channels = {label: channel for label, channel in BROWSER_CHOICES}
        if initial.browser_channel not in self.browser_channels.values():
            self.browser_channels[initial.browser_channel] = initial.browser_channel
        browser_label = next(
            label for label, channel in self.browser_channels.items() if channel == initial.browser_channel
        )
        self.vars = {
            "username": tk.StringVar(root, initial.username),
            "password": tk.StringVar(root, initial.password),
            "course_keyword": tk.StringVar(root, initial.course_keyword),
            "course_url": tk.StringVar(root, initial.course_url),
            "chapter_keyword": tk.StringVar(root, initial.chapter_keyword),
            "browser": tk.StringVar(root, browser_label),
            "playback_rate": tk.StringVar(root, initial.playback_rate),
            "max_chapters": tk.StringVar(root, str(initial.max_chapters)),
        }
        self.flags = {
            "headless": tk.BooleanVar(root, initial.headless),
            "fast_actions": tk.BooleanVar(root, initial.fast_actions),
            "manual_verification": tk.BooleanVar(root, initial.manual_verification_seconds > 0),
            "remember": tk.BooleanVar(root, True),
        }

        self.inputs: List[ttk.Widget] = []
        self.started_at: Optional[float] = None
        self.tick_job: Optional[str] = None
        self.stop_requested = False
        self.hit_cap = False
        self.video_position: Optional[Tuple[int, int]] = None
        self.video_detail = ""
        self.log_handle = None

        self._build_fonts()
        self._build_styles()
        self._build_window()
        self._build_layout()
        self.flags["headless"].trace_add("write", self._sync_manual_state)
        self._sync_manual_state()
        self._set_running(False)
        self.detail_label.configure(text="填好左侧信息后点「开始运行」。每次运行的日志都会另存到 logs/ui 文件夹。")
        self._append_console("准备就绪。", "muted")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(80, self._poll_events)

    # ----- 基础 -----

    def px(self, value: float) -> int:
        return int(round(value * self.scale))

    def _build_fonts(self) -> None:
        families = set(tkfont.families(self.root))
        family = next(
            (name for name in FONT_FAMILIES if name in families),
            tkfont.nametofont("TkDefaultFont").actual("family"),
        )
        self.fonts = {
            "base": tkfont.Font(self.root, family=family, size=10),
            "small": tkfont.Font(self.root, family=family, size=9),
            "section": tkfont.Font(self.root, family=family, size=11, weight="bold"),
            "title": tkfont.Font(self.root, family=family, size=15, weight="bold"),
            "metric": tkfont.Font(self.root, family=family, size=14, weight="bold"),
            "button": tkfont.Font(self.root, family=family, size=10, weight="bold"),
            "console": tkfont.Font(self.root, family=family, size=10),
        }
        self.root.option_add("*TCombobox*Listbox.font", self.fonts["base"])

    def _build_styles(self) -> None:
        p = PALETTE
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=p["bg"], foreground=p["text"], font=self.fonts["base"], bordercolor=p["border"])
        style.configure("Field.TLabel", background=p["card"], foreground=p["muted"], font=self.fonts["small"])
        style.configure("Section.TLabel", background=p["card"], foreground=p["text"], font=self.fonts["section"])

        field = {
            "fieldbackground": p["field"],
            "background": p["field"],
            "bordercolor": p["border_strong"],
            "lightcolor": p["field"],
            "darkcolor": p["field"],
            "insertcolor": p["text"],
            "arrowcolor": p["muted"],
            "arrowsize": self.px(12),
            "padding": (self.px(8), self.px(6)),
        }
        field_map = {
            "bordercolor": [("focus", p["accent"])],
            "lightcolor": [("focus", p["accent"])],
            "darkcolor": [("focus", p["accent"])],
            "foreground": [("disabled", p["muted"])],
            "arrowcolor": [("disabled", p["subtle"])],
        }
        for name in ("TEntry", "TSpinbox"):
            style.configure(name, **field)
            style.map(name, **field_map)
        style.configure("TCombobox", **field)
        style.map(
            "TCombobox",
            **field_map,
            fieldbackground=[("readonly", p["field"])],
            selectbackground=[("readonly", p["field"])],
            selectforeground=[("disabled", p["muted"]), ("readonly", p["text"])],
            background=[("active", p["field"])],
        )

        # clam 自带的勾是个 X，这里换成自己画的圆角对勾。
        # 运行中控件会被禁用，但勾选状态仍要看得出来，所以 disabled+selected 单独给浅蓝。
        size, gap = self.px(16), self.px(8)
        self.check_images = {
            name: make_checkbox_image(self.root, size, gap, fill, border, mark, p["card"])
            for name, fill, border, mark in (
                ("off", p["field"], p["border_strong"], None),
                ("off_disabled", p["bg"], p["border"], None),
                ("on", p["accent"], p["accent"], "#FFFFFF"),
                ("on_disabled", p["accent_disabled"], p["accent_disabled"], "#FFFFFF"),
            )
        }
        style.element_create(
            "Card.Checkbutton.indicator",
            "image",
            self.check_images["off"],
            ("disabled", "selected", self.check_images["on_disabled"]),
            ("selected", self.check_images["on"]),
            ("disabled", self.check_images["off_disabled"]),
        )
        style.layout(
            "Card.TCheckbutton",
            [("Checkbutton.padding", {"sticky": "nswe", "children": [
                ("Card.Checkbutton.indicator", {"side": "left", "sticky": ""}),
                ("Checkbutton.label", {"side": "left", "sticky": "nswe"}),
            ]})],
        )
        style.configure("Card.TCheckbutton", background=p["card"], foreground=p["text"], padding=(0, self.px(3)))
        style.map("Card.TCheckbutton", background=[("active", p["card"])], foreground=[("disabled", p["subtle"])])

        def button(name: str, bg: str, fg: str, hover: str, pressed: str, disabled_bg: str, disabled_fg: str,
                   border: Optional[str] = None, font: Optional[tkfont.Font] = None, padding: Tuple[int, int] = (16, 8)) -> None:
            edge = border or bg
            style.configure(
                name,
                background=bg,
                foreground=fg,
                bordercolor=edge,
                lightcolor=bg,
                darkcolor=bg,
                focuscolor=bg,
                focusthickness=0,
                font=font or self.fonts["button"],
                padding=(self.px(padding[0]), self.px(padding[1])),
            )
            states = {"background": [("disabled", disabled_bg), ("pressed", pressed), ("active", hover)]}
            style.map(
                name,
                background=states["background"],
                lightcolor=states["background"],
                darkcolor=states["background"],
                focuscolor=states["background"],
                bordercolor=[("disabled", disabled_bg if border is None else p["border"])],
                foreground=[("disabled", disabled_fg)],
            )

        button("Primary.TButton", p["accent"], "#FFFFFF", p["accent_hover"], p["accent_pressed"],
               p["accent_disabled"], "#FFFFFF", padding=(22, 8))
        button("Danger.TButton", p["card"], p["error"], p["error_soft"], "#FEE2E2", p["card"], p["subtle"],
               border="#FCA5A5", padding=(18, 8))
        button("Ghost.TButton", p["card"], p["muted"], p["ghost_hover"], p["border"], p["card"], p["subtle"],
               border=p["border"], font=self.fonts["small"], padding=(10, 3))

        style.configure(
            "Video.Horizontal.TProgressbar",
            troughcolor=p["track"],
            background=p["accent"],
            bordercolor=p["track"],
            lightcolor=p["accent"],
            darkcolor=p["accent"],
            thickness=self.px(8),
        )
        style.layout(
            "Console.Vertical.TScrollbar",
            [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})],
        )
        style.configure(
            "Console.Vertical.TScrollbar",
            troughcolor=p["console_bg"],
            background=p["console_thumb"],
            bordercolor=p["console_bg"],
            lightcolor=p["console_thumb"],
            darkcolor=p["console_thumb"],
            arrowsize=self.px(10),
            gripcount=0,
        )
        style.map("Console.Vertical.TScrollbar", background=[("active", p["console_thumb_hover"])])

    def _build_window(self) -> None:
        root = self.root
        root.title("学习通刷课助手")
        root.configure(bg=PALETTE["bg"])
        self.icons = make_icons(root)
        root.iconphoto(True, *self.icons)
        screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
        width = min(self.px(1080), screen_w - self.px(40))
        height = min(self.px(740), screen_h - self.px(90))
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2 - self.px(20))
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.minsize(min(self.px(900), width), min(self.px(600), height))

    def _card(self, parent: tk.Widget, padding: int = 18) -> Tuple[tk.Frame, tk.Frame]:
        outer = tk.Frame(parent, bg=PALETTE["card"], highlightthickness=1,
                         highlightbackground=PALETTE["border"], highlightcolor=PALETTE["border"])
        inner = tk.Frame(outer, bg=PALETTE["card"])
        inner.pack(fill="both", expand=True, padx=self.px(padding), pady=self.px(padding))
        return outer, inner

    def _label(self, parent: tk.Widget, text: str, font: str = "base", color: str = "text", **options: Any) -> tk.Label:
        return tk.Label(parent, text=text, font=self.fonts[font], fg=PALETTE[color], bg=parent["bg"], **options)

    # ----- 布局 -----

    def _build_layout(self) -> None:
        p = PALETTE
        header = tk.Frame(self.root, bg=p["card"])
        header.pack(fill="x")
        header_inner = tk.Frame(header, bg=p["card"])
        header_inner.pack(fill="x", padx=self.px(24), pady=(self.px(14), self.px(14)))
        titles = tk.Frame(header_inner, bg=p["card"])
        titles.pack(side="left")
        self._label(titles, "学习通刷课助手", "title").pack(anchor="w")
        self._label(titles, "填好账号和课程，点「开始运行」后会自动登录、打开课程，并逐个看完任务点。",
                    "small", "muted").pack(anchor="w", pady=(self.px(2), 0))
        self.start_button = ttk.Button(header_inner, text="开始运行", style="Primary.TButton", command=self.start,
                                       cursor="hand2")
        self.start_button.pack(side="right")
        self.stop_button = ttk.Button(header_inner, text="停止", style="Danger.TButton", command=self.stop,
                                      cursor="hand2")
        self.stop_button.pack(side="right", padx=(0, self.px(10)))
        tk.Frame(self.root, bg=p["border"], height=1).pack(fill="x")

        body = tk.Frame(self.root, bg=p["bg"])
        body.pack(fill="both", expand=True, padx=self.px(20), pady=self.px(18))
        body.columnconfigure(0, minsize=self.px(372))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        settings_outer, settings_inner = self._card(body)
        settings_outer.grid(row=0, column=0, sticky="nsew", padx=(0, self.px(16)))
        self._build_settings(settings_inner)

        right = tk.Frame(body, bg=p["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        status_outer, status_inner = self._card(right)
        status_outer.grid(row=0, column=0, sticky="ew", pady=(0, self.px(16)))
        self._build_status(status_inner)
        log_outer, log_inner = self._card(right, padding=0)
        log_outer.grid(row=1, column=0, sticky="nsew")
        self._build_console(log_inner)

    def _section(self, parent: tk.Widget, text: str, first: bool = False) -> None:
        ttk.Label(parent, text=text, style="Section.TLabel").pack(
            anchor="w", pady=(0 if first else self.px(16), self.px(8))
        )

    def _row(self, parent: tk.Widget, weights: Tuple[int, ...] = (1,)) -> tk.Frame:
        row = tk.Frame(parent, bg=PALETTE["card"])
        row.pack(fill="x", pady=(0, self.px(10)))
        for column, weight in enumerate(weights):
            row.columnconfigure(column, weight=weight, uniform="cells")
        return row

    def _field(self, row: tk.Frame, column: int, label: str, build: Callable[[tk.Frame], ttk.Widget],
               tooltip: Optional[str] = None) -> Tuple[tk.Frame, ttk.Widget]:
        cell = tk.Frame(row, bg=PALETTE["card"])
        cell.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else self.px(10), 0))
        label_row = tk.Frame(cell, bg=PALETTE["card"])
        label_row.pack(fill="x", pady=(0, self.px(4)))
        caption = ttk.Label(label_row, text=label, style="Field.TLabel")
        caption.pack(side="left")
        widget = build(cell)
        widget.pack(fill="x")
        self.inputs.append(widget)
        if tooltip:
            Tooltip(caption, tooltip, self.fonts["small"], self.px(10))
            Tooltip(widget, tooltip, self.fonts["small"], self.px(10))
        return label_row, widget

    def _entry(self, key: str, placeholder: str = "", **options: Any) -> Callable[[tk.Frame], ttk.Entry]:
        def build(parent: tk.Frame) -> ttk.Entry:
            entry = ttk.Entry(parent, textvariable=self.vars[key], width=8, font=self.fonts["base"], **options)
            if placeholder:
                self._add_placeholder(entry, self.vars[key], placeholder)
            return entry

        return build

    def _add_placeholder(self, entry: ttk.Entry, variable: tk.StringVar, text: str) -> None:
        hint = tk.Label(entry, text=text, font=self.fonts["base"], fg=PALETTE["subtle"], bg=PALETTE["field"],
                        cursor="xterm", padx=0, pady=0)

        def has_focus() -> bool:
            try:
                return self.root.focus_get() is entry
            except KeyError:  # 焦点在下拉框弹出层这类 tkinter 不认识的控件上
                return False

        def refresh(_event: Any = None, *_args: Any) -> None:
            if variable.get() or has_focus():
                hint.place_forget()
            else:
                hint.place(x=self.px(9), rely=0.5, anchor="w")

        hint.bind("<Button-1>", lambda _event: entry.focus_set())
        entry.bind("<FocusIn>", lambda _event: hint.place_forget(), add="+")
        entry.bind("<FocusOut>", refresh, add="+")
        variable.trace_add("write", lambda *_args: refresh())
        refresh()

    def _build_settings(self, parent: tk.Frame) -> None:
        self._section(parent, "账号", first=True)
        row = self._row(parent, (1, 1))
        self._field(row, 0, "账号", self._entry("username", "手机号或学号"))
        password_label_row, self.password_entry = self._field(row, 1, "密码", self._entry("password", show="•"))
        self.password_toggle = self._label(password_label_row, "显示", "small", "accent", cursor="hand2")
        self.password_toggle.pack(side="right")
        self.password_toggle.bind("<Button-1>", self._toggle_password)

        self._section(parent, "课程")
        self._field(self._row(parent), 0, "课程名称", self._entry("course_keyword", "课程标题里的一段，越完整越准"),
                    "按名称在课程列表里匹配。匹配到多门相近的课会停下来，这时请写得更完整，或改填课程链接。")
        self._field(self._row(parent), 0, "课程链接", self._entry("course_url", "可选，填了就不按名称匹配"),
                    "课程页面的完整网址。填了会直接打开这门课，跳过名称匹配。")
        self._field(self._row(parent), 0, "起始章节", self._entry("chapter_keyword", "可选，留空则自动找未完成的"),
                    "从标题包含这段文字的章节开始。留空时会自动找到第一个未完成的任务点。")

        self._section(parent, "运行选项")
        row = self._row(parent, (5, 4, 4))
        browser_values = list(self.browser_channels)
        self._field(row, 0, "浏览器", lambda cell: ttk.Combobox(
            cell, textvariable=self.vars["browser"], values=browser_values, state="readonly", width=8,
            font=self.fonts["base"]))
        rates = list(PLAYBACK_RATES)
        if self.vars["playback_rate"].get() not in rates:
            rates.append(self.vars["playback_rate"].get())
        self._field(row, 1, "倍速", lambda cell: ttk.Combobox(
            cell, textvariable=self.vars["playback_rate"], values=rates, state="readonly", width=4,
            font=self.fonts["base"]),
            "目标播放倍速。平台限制倍速时会按平台实际允许的速度播放。")
        self._field(row, 2, "任务点上限", lambda cell: ttk.Spinbox(
            cell, textvariable=self.vars["max_chapters"], from_=1, to=9999, increment=10, width=4,
            font=self.fonts["base"]),
            "最多连续处理多少个任务点。达到上限会停止并提示，课程不一定看完。")

        checks = tk.Frame(parent, bg=PALETTE["card"])
        checks.pack(fill="x", pady=(self.px(4), 0))
        checks.columnconfigure((0, 1), weight=1, uniform="checks")
        options = (
            ("headless", "后台运行", "不弹出浏览器窗口。第一次用建议先关掉，方便看清登录和选课过程。"),
            ("fast_actions", "快速模式", "缩短点击和页面之间的等待，跑得更快。还没在真实课程上充分验证。"),
            ("manual_verification", "手动过验证码", "遇到验证码时暂停，最多等 5 分钟让你在浏览器里自己完成。需要关闭后台运行。"),
            ("remember", "记住设置", "点开始时把这些设置（包括密码）保存到本地 .env，下次打开自动填好。"),
        )
        for index, (key, text, tip) in enumerate(options):
            check = ttk.Checkbutton(checks, text=text, variable=self.flags[key], style="Card.TCheckbutton",
                                    cursor="hand2")
            check.grid(row=index // 2, column=index % 2, sticky="w", pady=(0, self.px(4)))
            Tooltip(check, tip, self.fonts["small"], self.px(10))
            self.inputs.append(check)
            if key == "manual_verification":
                self.manual_check = check

    def _build_status(self, parent: tk.Frame) -> None:
        metrics = tk.Frame(parent, bg=PALETTE["card"])
        metrics.pack(fill="x")
        metrics.columnconfigure((0, 1, 2), weight=1, uniform="metrics")

        def metric(column: int, caption: str) -> tk.Frame:
            cell = tk.Frame(metrics, bg=PALETTE["card"])
            cell.grid(row=0, column=column, sticky="w")
            self._label(cell, caption, "small", "muted").pack(anchor="w")
            value = tk.Frame(cell, bg=PALETTE["card"])
            value.pack(anchor="w", pady=(self.px(2), 0))
            return value

        status_cell = metric(0, "状态")
        self.status_dot = self._label(status_cell, "●", "base", "muted")
        self.status_dot.pack(side="left", padx=(0, self.px(6)))
        self.status_value = self._label(status_cell, "就绪", "metric")
        self.status_value.pack(side="left")
        self.task_value = self._label(metric(1, "当前任务点"), "—", "metric")
        self.task_value.pack(anchor="w")
        self.elapsed_value = self._label(metric(2, "用时"), "00:00", "metric")
        self.elapsed_value.pack(anchor="w")

        video_row = tk.Frame(parent, bg=PALETTE["card"])
        video_row.pack(fill="x", pady=(self.px(16), self.px(6)))
        self._label(video_row, "当前视频", "small", "muted").pack(side="left")
        self.video_label = self._label(video_row, "—", "small", "muted")
        self.video_label.pack(side="right")
        self.progress = ttk.Progressbar(parent, style="Video.Horizontal.TProgressbar", maximum=100)
        self.progress.pack(fill="x")
        self.detail_label = self._label(parent, "", "small", "muted", anchor="w", justify="left")
        self.detail_label.pack(fill="x", pady=(self.px(10), 0))
        self.detail_label.bind("<Configure>", lambda event: self.detail_label.configure(wraplength=event.width))

    def _build_console(self, parent: tk.Frame) -> None:
        p = PALETTE
        toolbar = tk.Frame(parent, bg=p["card"])
        toolbar.pack(fill="x", padx=self.px(18), pady=(self.px(12), self.px(10)))
        ttk.Label(toolbar, text="运行日志", style="Section.TLabel").pack(side="left")
        for text, command in (
            ("清空", self.clear_console),
            ("日志文件夹", lambda: self._open_folder(UI_LOG_DIR)),
            ("截图文件夹", lambda: self._open_folder(self.screenshot_dir)),
        ):
            ttk.Button(toolbar, text=text, style="Ghost.TButton", command=command, cursor="hand2").pack(
                side="right", padx=(self.px(6), 0)
            )

        frame = tk.Frame(parent, bg=p["console_bg"])
        frame.pack(fill="both", expand=True)
        self.console = tk.Text(
            frame,
            bg=p["console_bg"],
            fg=p["console_text"],
            insertbackground=p["console_text"],
            selectbackground=p["console_thumb_hover"],
            font=self.fonts["console"],
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            wrap="word",
            padx=self.px(14),
            pady=self.px(10),
            spacing1=self.px(2),
            spacing3=self.px(2),
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(frame, orient="vertical", style="Console.Vertical.TScrollbar",
                                  command=self.console.yview)
        self.console.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y", padx=(0, self.px(4)), pady=self.px(4))
        self.console.pack(side="left", fill="both", expand=True)
        # 换行的长日志与正文对齐，而不是缩回时间戳下面。续行用的是续行首字所在标签的 lmargin2，
        # 所以每个标签都要设。
        indent = self.fonts["console"].measure("00:00:00  ")
        for tag, color in (
            ("time", p["console_time"]),
            ("plain", p["console_text"]),
            ("muted", p["console_muted"]),
            ("info", p["console_info"]),
            ("success", p["console_success"]),
            ("warning", p["console_warning"]),
            ("error", p["console_error"]),
        ):
            self.console.tag_configure(tag, foreground=color, lmargin2=indent)

    # ----- 状态 -----

    def _set_running(self, running: bool) -> None:
        for widget in self.inputs:
            widget.state(["disabled"] if running else ["!disabled"])
        self.start_button.state(["disabled"] if running else ["!disabled"])
        self.stop_button.state(["!disabled"] if running else ["disabled"])
        if not running:
            self._sync_manual_state()

    def _sync_manual_state(self, *_args: Any) -> None:
        if self.runner.running:
            return
        self.manual_check.state(["disabled"] if self.flags["headless"].get() else ["!disabled"])

    def _set_status(self, text: str, tone: str) -> None:
        color = TONE_COLORS.get(tone, PALETTE["muted"])
        self.status_dot.configure(fg=color)
        self.status_value.configure(text=text, fg=color if tone in {"success", "warning", "error"} else PALETTE["text"])

    def _refresh_video_label(self) -> None:
        parts = []
        if self.video_position:
            parts.append(f"第 {self.video_position[0]}/{self.video_position[1]} 个")
        if self.video_detail:
            parts.append(self.video_detail)
        self.video_label.configure(text=" · ".join(parts) or "—")

    def _toggle_password(self, _event: Any = None) -> None:
        hidden = str(self.password_entry.cget("show")) != ""
        self.password_entry.configure(show="" if hidden else "•")
        self.password_toggle.configure(text="隐藏" if hidden else "显示")

    def _form_values(self) -> Dict[str, Any]:
        values: Dict[str, Any] = {key: variable.get() for key, variable in self.vars.items()}
        values["browser_channel"] = self.browser_channels.get(values.pop("browser"), "")
        values.update({key: flag.get() for key, flag in self.flags.items()})
        return values

    # ----- 日志 -----

    def _append_console(self, text: str, tag: str) -> None:
        console = self.console
        at_bottom = console.yview()[1] >= 0.999
        console.configure(state="normal")
        console.insert("end", datetime.now().strftime("%H:%M:%S") + "  ", ("time",))
        console.insert("end", text + "\n", (tag,))
        line_count = int(console.index("end-1c").split(".")[0])
        if line_count > MAX_CONSOLE_LINES:
            console.delete("1.0", f"{line_count - MAX_CONSOLE_LINES}.0")
        console.configure(state="disabled")
        if at_bottom:
            console.see("end")

    def _write_log(self, text: str) -> None:
        if self.log_handle is None:
            return
        try:
            self.log_handle.write(f"{datetime.now():%H:%M:%S} {text}\n")
            self.log_handle.flush()
        except OSError:
            self.log_handle = None

    def _ui_line(self, text: str, tag: str = "info") -> None:
        self._append_console(text, tag)
        self._write_log(f"[界面] {text}")

    def clear_console(self) -> None:
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")

    def _open_log_file(self) -> None:
        try:
            UI_LOG_DIR.mkdir(parents=True, exist_ok=True)
            path = UI_LOG_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.log"
            self.log_handle = path.open("w", encoding="utf-8")
        except OSError as exc:
            self.log_handle = None
            self._ui_line(f"无法创建日志文件：{exc}", "warning")

    def _close_log_file(self) -> None:
        if self.log_handle is not None:
            try:
                self.log_handle.close()
            except OSError:
                pass
            self.log_handle = None

    def _open_folder(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError as exc:
            messagebox.showerror("打不开文件夹", str(exc), parent=self.root)

    # ----- 运行控制 -----

    def start(self) -> None:
        if self.runner.running:
            return
        try:
            settings = parse_form(self._form_values(), self.previous_manual_seconds)
        except ValueError as exc:
            messagebox.showwarning("还差一点", str(exc), parent=self.root)
            return

        self.stop_requested = False
        self.hit_cap = False
        self.video_position = None
        self.video_detail = ""
        self.progress["value"] = 0
        self.task_value.configure(text="—")
        self.detail_label.configure(text="", fg=PALETTE["muted"])
        self._refresh_video_label()
        self._open_log_file()

        if self.flags["remember"].get():
            self._remember(settings)
        try:
            self.runner.start([child_python(), "-u", str(MAIN_SCRIPT)], build_child_env(dict(os.environ), settings), ROOT)
        except OSError as exc:
            self._ui_line(f"无法启动 main.py：{exc}", "error")
            self._set_status("启动失败", "error")
            self._close_log_file()
            return

        target = settings.course_keyword or "课程链接"
        browser = "后台运行" if settings.headless else "显示浏览器"
        self._ui_line(f"开始运行：{target} · {self.vars['browser'].get()} · {browser} · 上限 {settings.max_chapters} 个任务点")
        if self.log_handle is not None:
            log_path = Path(self.log_handle.name)
            shown = log_path.relative_to(ROOT) if log_path.is_relative_to(ROOT) else log_path
            self.detail_label.configure(text=f"本次日志：{shown}")
        self.started_at = time.monotonic()
        self._set_running(True)
        self._set_status("正在启动", "running")
        if self.tick_job is not None:
            self.root.after_cancel(self.tick_job)
        self._tick()

    def _remember(self, settings: Settings) -> None:
        try:
            skipped = save_env_file(ENV_PATH, settings_to_env(settings), ENV_EXAMPLE_PATH)
        except (OSError, ValueError) as exc:
            self._ui_line(f"保存设置到 .env 失败，本次仍按界面里的设置运行：{exc}", "warning")
            return
        if settings.manual_verification_seconds > 0:
            self.previous_manual_seconds = settings.manual_verification_seconds
        if skipped:
            self._ui_line(
                f"这些设置含有 ${{、换行或以反斜杠结尾，.env 无法原样保存，只在本次使用：{'、'.join(skipped)}",
                "warning",
            )
        else:
            self._ui_line("设置已保存到 .env", "muted")

    def stop(self) -> None:
        if not self.runner.running:
            return
        if not messagebox.askyesno("停止运行", "确定要停止吗？正在播放的视频进度可能来不及上报。", parent=self.root):
            return
        self.stop_requested = True
        self._set_status("正在停止", "warning")
        self._ui_line("正在停止，并关闭浏览器…", "warning")
        self.stop_button.state(["disabled"])
        threading.Thread(target=self.runner.stop, daemon=True).start()

    def on_close(self) -> None:
        if self.runner.running:
            if not messagebox.askyesno("退出", "还在运行，关闭窗口会同时停止运行。确定退出吗？", parent=self.root):
                return
            self.stop_requested = True
            self.runner.stop()
        self._close_log_file()
        self.root.destroy()

    def _tick(self) -> None:
        self.tick_job = None
        if self.started_at is None:
            return
        self.elapsed_value.configure(text=format_clock(time.monotonic() - self.started_at))
        self.tick_job = self.root.after(1000, self._tick)

    def _poll_events(self) -> None:
        for _ in range(300):
            try:
                kind, payload = self.runner.events.get_nowait()
            except queue.Empty:
                break
            if kind == "line":
                self._handle_line(payload)
            elif kind == "exit":
                self._handle_exit(payload)
        self.root.after(80, self._poll_events)

    def _handle_line(self, line: str) -> None:
        if not line.strip():
            return
        self._append_console(line, classify_line(line))
        self._write_log(line)
        update = parse_status_line(line)
        if not update:
            return
        if "task" in update:
            self.task_value.configure(text=f"第 {update['task']} 个")
        if "video" in update:
            self.video_position = update["video"]
        if "video_detail" in update:
            self.video_detail = update["video_detail"]
        if "percent" in update:
            self.progress["value"] = update["percent"]
        if "stage" in update and not self.stop_requested:
            self._set_status(update["stage"], "warning" if update.get("attention") else "running")
        if update.get("hit_cap"):
            self.hit_cap = True
        if update.get("attention"):
            self._notify()
        self._refresh_video_label()

    def _handle_exit(self, code: int) -> None:
        if self.started_at is not None:
            self.elapsed_value.configure(text=format_clock(time.monotonic() - self.started_at))
        self.started_at = None
        title, tone, detail = summarize_exit(code, self.stop_requested, self.hit_cap)
        self._set_status(title, tone)
        self.detail_label.configure(text=detail, fg=TONE_COLORS.get(tone, PALETTE["muted"]))
        self._ui_line(f"{title}（退出码 {code}）。{detail}", tone if tone != "muted" else "info")
        self._close_log_file()
        self._set_running(False)
        self._notify()

    def _notify(self) -> None:
        """运行结束或需要人工处理时提醒一下：响一声，并让任务栏按钮闪烁。"""
        self.root.bell()
        if os.name == "nt":
            try:
                ctypes.windll.user32.FlashWindow(int(self.root.wm_frame(), 16), True)
            except (AttributeError, OSError, ValueError):
                pass


# ---------------------------------------------------------------------------
# 快捷方式（Windows）
# ---------------------------------------------------------------------------

CLSID_SHELL_LINK = "{00021401-0000-0000-C000-000000000046}"
IID_SHELL_LINK_W = "{000214F9-0000-0000-C000-000000000046}"
IID_PERSIST_FILE = "{0000010B-0000-0000-C000-000000000046}"
IID_PROPERTY_STORE = "{886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99}"
FMTID_APP_USER_MODEL = "{9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3}"  # PKEY_AppUserModel_ID 的 fmtid，pid 为 5


class _Guid(ctypes.Structure):
    _fields_ = [("data1", ctypes.c_ulong), ("data2", ctypes.c_ushort), ("data3", ctypes.c_ushort),
                ("data4", ctypes.c_ubyte * 8)]

    @classmethod
    def parse(cls, text: str) -> "_Guid":
        guid = cls()
        ctypes.oledll.ole32.CLSIDFromString(text, ctypes.byref(guid))
        return guid


class _PropertyKey(ctypes.Structure):
    _fields_ = [("fmtid", _Guid), ("pid", ctypes.c_ulong)]


class _PropVariant(ctypes.Structure):
    # 只用到 VT_LPWSTR；联合体按 64 位下的 16 字节留足空间。
    _fields_ = [("vt", ctypes.c_ushort), ("reserved", ctypes.c_ushort * 3),
                ("pointer", ctypes.c_void_p), ("padding", ctypes.c_void_p)]


def _com_call(obj: ctypes.c_void_p, index: int, argtypes: Tuple[Any, ...], *args: Any, restype: Any = None) -> Any:
    """按虚表序号调用 COM 方法。默认返回类型是 HRESULT，失败时 ctypes 直接抛 OSError。"""
    vtable = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    method = ctypes.WINFUNCTYPE(restype or ctypes.HRESULT, ctypes.c_void_p, *argtypes)(vtable[index])
    return method(obj, *args)


def _query_interface(obj: ctypes.c_void_p, iid: str) -> ctypes.c_void_p:
    result = ctypes.c_void_p()
    _com_call(obj, 0, (ctypes.c_void_p, ctypes.c_void_p), ctypes.byref(_Guid.parse(iid)), ctypes.byref(result))
    return result


def _release(obj: ctypes.c_void_p) -> None:
    _com_call(obj, 2, (), restype=ctypes.c_ulong)


def create_shortcut(path: Path, target: str, arguments: str, working_dir: Path, icon: Path,
                    description: str, app_id: str) -> None:
    """用 IShellLinkW 写 .lnk，并带上 AppUserModelID（WScript.Shell 设不了这一项）。"""
    ole32 = ctypes.windll.ole32
    # 已初始化时返回 S_FALSE，同样要配对 CoUninitialize；线程模型冲突时返回负值，直接沿用现有的。
    initialized = ole32.CoInitializeEx(None, 2) >= 0
    try:
        link = ctypes.c_void_p()
        ctypes.oledll.ole32.CoCreateInstance(ctypes.byref(_Guid.parse(CLSID_SHELL_LINK)), None, 1,
                                             ctypes.byref(_Guid.parse(IID_SHELL_LINK_W)), ctypes.byref(link))
        try:
            text = (ctypes.c_wchar_p,)
            _com_call(link, 20, text, target)  # SetPath
            _com_call(link, 11, text, arguments)  # SetArguments
            _com_call(link, 9, text, str(working_dir))  # SetWorkingDirectory
            _com_call(link, 7, text, description)  # SetDescription
            _com_call(link, 17, (ctypes.c_wchar_p, ctypes.c_int), str(icon), 0)  # SetIconLocation
            store = _query_interface(link, IID_PROPERTY_STORE)
            try:
                value = ctypes.create_unicode_buffer(app_id)
                variant = _PropVariant(vt=31, pointer=ctypes.addressof(value))  # VT_LPWSTR
                key = _PropertyKey(_Guid.parse(FMTID_APP_USER_MODEL), 5)
                _com_call(store, 6, (ctypes.c_void_p, ctypes.c_void_p), ctypes.byref(key), ctypes.byref(variant))
                _com_call(store, 7, ())  # Commit
            finally:
                _release(store)
            persist = _query_interface(link, IID_PERSIST_FILE)
            try:
                _com_call(persist, 6, (ctypes.c_wchar_p, ctypes.c_int), str(path), 1)  # Save
            finally:
                _release(persist)
        finally:
            _release(link)
    finally:
        if initialized:
            ole32.CoUninitialize()


def shortcut_folders() -> List[Path]:
    """桌面和开始菜单的"程序"目录。用系统接口取，桌面被 OneDrive 重定向时也对。"""
    folders = []
    for csidl in (0x0010, 0x0002):  # CSIDL_DESKTOPDIRECTORY, CSIDL_PROGRAMS
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.oledll.shell32.SHGetFolderPathW(None, csidl, None, 0, buffer)
        folders.append(Path(buffer.value))
    return folders


def gui_launcher() -> str:
    """快捷方式用同目录的 pythonw.exe 启动，不多弹一个控制台窗口。"""
    windowed = Path(sys.executable).with_name("pythonw.exe")
    return str(windowed if windowed.exists() else sys.executable)


def install_shortcuts(folders: Optional[List[Path]] = None, icon_path: Optional[Path] = None) -> List[Path]:
    icon_path = icon_path or ICON_PATH
    icon_path.write_bytes(icon_ico())
    links = []
    for folder in folders or shortcut_folders():
        link = folder / f"{APP_NAME}.lnk"
        create_shortcut(link, gui_launcher(), f'"{GUI_SCRIPT}"', ROOT, icon_path, f"打开{APP_NAME}", APP_ID)
        links.append(link)
    return links


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=f"{APP_NAME}的桌面界面")
    parser.add_argument("--create-shortcuts", action="store_true",
                        help="在桌面和开始菜单创建快捷方式后退出（仅 Windows；重复运行会覆盖更新）")
    args = parser.parse_args(argv)
    if args.create_shortcuts:
        if os.name != "nt":
            raise SystemExit("快捷方式只支持 Windows。")
        links = install_shortcuts()
        print("已创建快捷方式：")
        for link in links:
            print(f"  {link}")
        print("以后双击桌面图标，或按 Win 键搜索「学习通」即可打开；打开后在任务栏图标上右键可以固定到任务栏。")
        print("项目文件夹换位置或换了 Python 后，重新运行一次本命令。")
        return
    if os.name == "nt":
        try:
            # 声明高 DPI 感知，否则 125%/150% 缩放下整个窗口会被系统拉伸得发虚。
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except (AttributeError, OSError):
            pass
        try:
            # 让任务栏显示本窗口的图标，而不是归到 python.exe 名下。
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        except (AttributeError, OSError):
            pass
    root = tk.Tk()
    if dotenv_values is None:
        root.withdraw()
        messagebox.showerror("缺少依赖", "没有找到 python-dotenv。请先在项目目录运行：\npython -m pip install -r requirements.txt")
        root.destroy()
        return
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
