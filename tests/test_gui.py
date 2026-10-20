"""图形界面里不依赖窗口的部分：.env 读写、表单校验、子进程环境、日志解析、进程管理、图标与快捷方式。"""
import io
import json
import os
import queue
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import unittest
import zlib
from pathlib import Path

from dotenv import dotenv_values

import gui

REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_SOURCE = (REPO_ROOT / "main.py").read_text(encoding="utf-8")


def valid_form(**overrides):
    form = {
        "username": "13800000000",
        "password": "pw",
        "course_keyword": "大学英语",
        "course_url": "",
        "chapter_keyword": "",
        "browser_channel": "chrome",
        "playback_rate": "1.0",
        "max_chapters": "100",
        "headless": False,
        "fast_actions": False,
        "manual_verification": False,
        "remember": True,
    }
    form.update(overrides)
    return form


class EnvFileTests(unittest.TestCase):
    TRICKY_VALUES = [
        "plain",
        "",
        "a b  c",
        "has#hash",
        "x #像注释",
        "it's",
        'say "hi"',
        "back\\slash",
        "大学英语（二）",
        "a=b?c&d",
        "$HOME",
        "'quoted'",
        "trailing ",
    ]

    def test_values_round_trip_through_python_dotenv(self):
        updates = {f"CX_KEY_{index}": value for index, value in enumerate(self.TRICKY_VALUES)}
        parsed = dotenv_values(stream=io.StringIO(gui.update_env_text("", updates)))
        for key, value in updates.items():
            self.assertEqual(parsed[key], value, key)

    def test_only_touches_managed_keys_and_keeps_crlf(self):
        original = (
            "# 注释\r\nAI_API_KEY=keep-me\r\nCX_USERNAME=old\r\n\r\n#CX_COURSE_URL=\r\nCX_COURSE_URL=stale\r\n"
        )
        updated = gui.update_env_text(original, {"CX_USERNAME": "new", "CX_COURSE_URL": ""})
        self.assertEqual(
            updated,
            "# 注释\r\nAI_API_KEY=keep-me\r\nCX_USERNAME=new\r\n\r\n#CX_COURSE_URL=\r\nCX_COURSE_URL=\r\n",
        )

    def test_updates_duplicates_and_appends_missing_keys(self):
        updated = gui.update_env_text(
            "CX_HEADLESS=true\nexport CX_HEADLESS=true\n",
            {"CX_HEADLESS": "false", "CX_FAST_ACTIONS": "true"},
        )
        self.assertEqual(updated.count("CX_HEADLESS=false"), 2)
        self.assertNotIn("CX_HEADLESS=true", updated)
        self.assertEqual(dotenv_values(stream=io.StringIO(updated))["CX_FAST_ACTIONS"], "true")

    def test_save_keeps_other_secrets_and_skips_unstorable_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_bytes(b"AI_API_KEY=secret\nCX_PASSWORD=old\n")
            skipped = gui.save_env_file(path, {"CX_PASSWORD": "a${b}c", "CX_USERNAME": "user"})
            self.assertEqual(skipped, ["CX_PASSWORD"])
            values = dotenv_values(path)
            self.assertEqual(values["AI_API_KEY"], "secret")
            self.assertEqual(values["CX_PASSWORD"], "old")
            self.assertEqual(values["CX_USERNAME"], "user")
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), [".env"])

    def test_save_starts_from_template_when_env_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            template = Path(tmp) / ".env.example"
            template.write_bytes("# 说明\nCX_USERNAME=\n".encode("utf-8"))
            gui.save_env_file(path, {"CX_USERNAME": "user"}, template)
            self.assertEqual(path.read_bytes().decode("utf-8"), "# 说明\nCX_USERNAME=user\n")

    def test_storable_rejects_interpolation_and_newlines(self):
        self.assertTrue(gui.env_value_is_storable("$HOME and {braces}"))
        for value in ("${HOME}", "ends-with\\", "a\nb", "a\rb"):
            self.assertFalse(gui.env_value_is_storable(value), value)


class SettingsTests(unittest.TestCase):
    def test_defaults_when_env_is_empty(self):
        settings = gui.settings_from_env({})
        self.assertEqual(settings.browser_channel, "chrome")
        self.assertEqual(settings.max_chapters, 100)
        self.assertFalse(settings.headless)
        self.assertFalse(settings.fast_actions)

    def test_reads_env_and_tolerates_bad_numbers(self):
        settings = gui.settings_from_env(
            {
                "CX_BROWSER_CHANNEL": "",
                "CX_MAX_CHAPTERS": "1OO",
                "CX_HEADLESS": "TRUE",
                "CX_FAST_ACTIONS": "on",
                "CX_MANUAL_VERIFICATION_WAIT_SECONDS": "abc",
                "CX_PASSWORD": " pw ",
            }
        )
        self.assertEqual(settings.browser_channel, "")  # 显式留空就是内置 Chromium
        self.assertEqual(settings.max_chapters, 100)
        self.assertTrue(settings.headless)
        self.assertTrue(settings.fast_actions)
        self.assertEqual(settings.manual_verification_seconds, 0.0)
        self.assertEqual(settings.password, " pw ")

    def test_form_rejects_incomplete_input(self):
        for overrides in (
            {"username": " "},
            {"password": ""},
            {"course_keyword": "", "course_url": ""},
            {"course_keyword": "", "course_url": "ftp://example.com/course"},
            {"max_chapters": "0"},
            {"max_chapters": "abc"},
            {"playback_rate": "0"},
            {"playback_rate": "fast"},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                gui.parse_form(valid_form(**overrides))

    def test_course_url_alone_is_enough(self):
        settings = gui.parse_form(valid_form(course_keyword="", course_url=" https://example.com/c "))
        self.assertEqual(settings.course_url, "https://example.com/c")

    def test_manual_verification_needs_a_visible_browser(self):
        self.assertEqual(
            gui.parse_form(valid_form(manual_verification=True)).manual_verification_seconds,
            gui.MANUAL_VERIFICATION_SECONDS,
        )
        self.assertEqual(
            gui.parse_form(valid_form(manual_verification=True), previous_manual_seconds=120).manual_verification_seconds,
            120,
        )
        self.assertEqual(
            gui.parse_form(valid_form(manual_verification=True, headless=True)).manual_verification_seconds,
            0,
        )

    def test_child_env_passes_empty_values_explicitly(self):
        settings = gui.parse_form(valid_form(course_url="", headless=True, fast_actions=True))
        env = gui.build_child_env({"CX_COURSE_URL": "stale", "PATH": "keep"}, settings)
        self.assertEqual(env["CX_COURSE_URL"], "")
        self.assertEqual(env["CX_BROWSER_EXECUTABLE_PATH"], "")
        self.assertEqual(env["CX_HEADLESS"], "true")
        self.assertEqual(env["CX_FAST_ACTIONS"], "true")
        self.assertEqual(env["PATH"], "keep")
        self.assertEqual(env["PYTHONUNBUFFERED"], "1")

    def test_main_reads_every_key_the_ui_sets(self):
        # 界面传的每个 CX_* 都必须是 main.py 真正读取的，否则界面上改了也不生效。
        read_names = set(re.findall(r'(?:env_flag|env_int|env_float|os\.getenv)\(\s*"(CX_[A-Z0-9_]+)"', MAIN_SOURCE))
        ui_names = set(gui.settings_to_env(gui.Settings())) | {"CX_BROWSER_EXECUTABLE_PATH"}
        self.assertEqual(sorted(ui_names - read_names), [])

    def test_form_values_win_over_a_stale_dotenv(self):
        # 端到端核对契约：main.py 的 load_dotenv() 不覆盖已有环境变量，所以界面显式传的值优先。
        # 把 main.py 复制到临时目录，配一份内容过时的 .env，避免读到仓库里真实的 .env。
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copy(REPO_ROOT / "main.py", tmp)
            Path(tmp, ".env").write_bytes(
                b"CX_COURSE_URL=https://stale.example.com/course\n"
                b"CX_HEADLESS=false\n"
                b"CX_BROWSER_EXECUTABLE_PATH=C:/stale/chrome.exe\n"
                b"CX_MAX_CHAPTERS=3\n"
            )
            settings = gui.parse_form(
                valid_form(course_keyword="界面里的课程", max_chapters="7", headless=True,
                           fast_actions=True, browser_channel="msedge")
            )
            probe = (
                "import json, sys, main; sys.argv = ['main.py']; "
                "c = main.build_config_from_args(main.CONFIG); "
                "keys = ('course_keyword', 'course_url', 'max_chapters', 'headless', 'browser_channel', "
                "'browser_executable_path', 'delay_range_seconds'); "
                "print(json.dumps({k: c[k] for k in keys}, ensure_ascii=False))"
            )
            result = subprocess.run(
                [sys.executable, "-c", probe],
                cwd=tmp,
                env=gui.build_child_env(dict(os.environ), settings),
                capture_output=True,
                timeout=60,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        config = json.loads(result.stdout.decode("utf-8").strip().splitlines()[-1])
        self.assertEqual(config["course_keyword"], "界面里的课程")
        self.assertEqual(config["course_url"], "")
        self.assertEqual(config["max_chapters"], 7)
        self.assertTrue(config["headless"])
        self.assertEqual(config["browser_channel"], "msedge")
        self.assertEqual(config["browser_executable_path"], "")
        self.assertEqual(config["delay_range_seconds"], [0.1, 0.3])


class LogParsingTests(unittest.TestCase):
    def test_markers_still_exist_in_main(self):
        # 界面靠这些固定措辞识别进度；main.py 改了措辞时这里会失败，提醒同步修改 gui.py。
        for marker in (
            "开始处理第 {chapter_index} 个学习任务点",
            "开始处理当前页第 {index}/{len(videos)} 个视频",
            "播放进度: {current:.1f}/{duration:.1f}s ",
            "({percent:.1f}%), 倍速 {playback_rate}",
            "当前视频已播放完成",
            "当前学习页未检测到视频",
            "已达到最大章节数",
            "检测到平台验证拦截",
            "已打开登录页",
            "跳过表单登录",
            "登录成功",
            "通过配置的课程 URL 打开课程入口",
            "课程入口匹配来源",
        ):
            self.assertIn(marker, MAIN_SOURCE)

    def test_parses_task_video_and_progress(self):
        self.assertEqual(gui.parse_status_line("开始处理第 7 个学习任务点")["task"], 7)
        self.assertEqual(gui.parse_status_line("开始处理当前页第 2/3 个视频")["video"], (2, 3))
        update = gui.parse_status_line("播放进度: 132.0/292.0s (45.2%), 倍速 1.5, paused=False")
        self.assertAlmostEqual(update["percent"], 45.2)
        self.assertEqual(update["video_detail"], "02:12 / 04:52 · 1.5x")
        self.assertEqual(gui.parse_status_line("当前视频已播放完成")["percent"], 100.0)
        self.assertEqual(gui.parse_status_line("播放进度: 12.0s, 等待视频时长信息..."), {})
        self.assertTrue(gui.parse_status_line("已达到最大章节数 CX_MAX_CHAPTERS=5，流程已停止。")["hit_cap"])
        self.assertEqual(gui.parse_status_line("检测到平台验证拦截 [登录]: 验证码")["stage"], "需要验证")
        self.assertEqual(gui.parse_status_line("登录成功。")["stage"], "正在打开课程")
        self.assertEqual(gui.parse_status_line("已点击: 登录按钮"), {})

    def test_classifies_lines(self):
        for line, expected in {
            "播放进度: 1.0/2.0s (50.0%), 倍速 1.0, paused=False": "muted",
            "等待 2.3 秒...": "muted",
            "点击失败 [登录按钮]: timeout": "error",
            "配置缺失: 课程关键词 为空，请先设置环境变量或配置值。": "error",
            "检测到当前任务可能仍未完成，等待平台状态刷新...": "warning",
            "当前视频已播放完成": "success",
            "登录成功。": "success",
            "已点击: 章节标签": "plain",
        }.items():
            self.assertEqual(gui.classify_line(line), expected, line)

    def test_exit_summary(self):
        self.assertEqual(gui.summarize_exit(0, False, False)[:2], ("已完成", "success"))
        self.assertEqual(gui.summarize_exit(1, False, True)[:2], ("达到上限", "warning"))
        self.assertEqual(gui.summarize_exit(1, False, False)[:2], ("运行失败", "error"))
        self.assertEqual(gui.summarize_exit(1, True, True)[0], "已停止")

    def test_format_clock(self):
        self.assertEqual(gui.format_clock(-5), "00:00")
        self.assertEqual(gui.format_clock(61.9), "01:01")
        self.assertEqual(gui.format_clock(3725), "1:02:05")


class ProcessRunnerTests(unittest.TestCase):
    def collect_until_exit(self, runner, timeout=30):
        lines = []
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                kind, payload = runner.events.get(timeout=0.2)
            except queue.Empty:
                continue
            if kind == "exit":
                return lines, payload
            lines.append(payload)
        self.fail("子进程没有在限定时间内结束")

    def child_env(self):
        return {**os.environ, "PYTHONIOENCODING": "utf-8"}

    def test_streams_output_and_exit_code(self):
        runner = gui.ProcessRunner()
        runner.start(
            [sys.executable, "-c", "print('第一行'); print('second', flush=True); raise SystemExit(3)"],
            self.child_env(),
            REPO_ROOT,
        )
        lines, code = self.collect_until_exit(runner)
        self.assertEqual(lines, ["第一行", "second"])
        self.assertEqual(code, 3)
        self.assertFalse(runner.running)

    @unittest.skipUnless(os.name == "nt", "进程树结束依赖 Windows taskkill")
    def test_stop_ends_the_whole_process_tree(self):
        # 子进程再起一个孙进程，模拟 main.py -> Playwright 驱动 -> 浏览器。
        script = (
            "import subprocess, sys, time; "
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
            "print(child.pid, flush=True); time.sleep(60)"
        )
        runner = gui.ProcessRunner()
        runner.start([sys.executable, "-c", script], self.child_env(), REPO_ROOT)
        kind, grandchild_pid = runner.events.get(timeout=30)
        self.assertEqual(kind, "line")
        runner.stop()
        _, code = self.collect_until_exit(runner)
        self.assertNotEqual(code, 0)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            # tasklist 按系统代码页输出（中文系统是 GBK），只比对 ASCII 的 PID 字节，不解码。
            listing = subprocess.run(
                ["tasklist", "/FI", f"PID eq {int(grandchild_pid)}", "/NH"], capture_output=True
            ).stdout
            if grandchild_pid.encode() not in listing:
                break
            time.sleep(0.2)
        else:
            self.fail("停止后孙进程仍在运行")


def decode_png(test, data):
    """解析 icon_png 的输出，顺带校验签名、CRC 和数据长度，返回 (宽, 高, RGBA 行)。"""
    test.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
    position, chunks = 8, {}
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        body = data[position + 8:position + 8 + length]
        (crc,) = struct.unpack(">I", data[position + 8 + length:position + 12 + length])
        test.assertEqual(crc, zlib.crc32(kind + body) & 0xFFFFFFFF)
        chunks[kind] = chunks.get(kind, b"") + body
        position += 12 + length
    width, height, depth, color_type = struct.unpack(">IIBB", chunks[b"IHDR"][:10])
    test.assertEqual((depth, color_type), (8, 6))
    raw = zlib.decompress(chunks[b"IDAT"])
    stride = 1 + 4 * width
    test.assertEqual(len(raw), stride * height)
    return width, height, [raw[row * stride + 1:(row + 1) * stride] for row in range(height)]


class IconTests(unittest.TestCase):
    def test_png_has_transparent_corners_blue_body_and_white_mark(self):
        for size in (16, 32, 256):
            width, height, rows = decode_png(self, gui.icon_png(size))
            self.assertEqual((width, height), (size, size))

            def pixel(x, y):
                return tuple(rows[y][4 * x:4 * x + 4])

            self.assertEqual(pixel(0, 0)[3], 0)
            self.assertEqual(pixel(size - 1, size - 1)[3], 0)
            red, green, blue, alpha = pixel(int(size * 0.2), size // 2)
            self.assertEqual(alpha, 255)
            self.assertGreater(blue, red + 80)
            self.assertEqual(pixel(int(size * 0.45), size // 2), (255, 255, 255, 255))

    def test_ico_lists_every_size_with_png_payload(self):
        data = gui.icon_ico()
        self.assertEqual(struct.unpack("<HHH", data[:6]), (0, 1, len(gui.ICON_SIZES)))
        for index, size in enumerate(gui.ICON_SIZES):
            width, height, _, _, planes, bits, length, offset = struct.unpack(
                "<BBBBHHII", data[6 + 16 * index:22 + 16 * index]
            )
            self.assertEqual((width, height, planes, bits), (size % 256, size % 256, 1, 32))
            self.assertEqual(decode_png(self, data[offset:offset + length])[:2], (size, size))


@unittest.skipUnless(os.name == "nt", "快捷方式只在 Windows 上创建")
class ShortcutTests(unittest.TestCase):
    def read_back(self, link):
        # 用系统自带的 Shell 接口独立读回，而不是拿同一套 ctypes 代码自证。
        script = (
            "[Console]::OutputEncoding = [Text.Encoding]::UTF8;"
            "$p = $env:SHORTCUT_PATH;"
            "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($p);"
            "$f = (New-Object -ComObject Shell.Application).Namespace((Split-Path $p)).ParseName((Split-Path $p -Leaf));"
            "@{target=$s.TargetPath; args=$s.Arguments; dir=$s.WorkingDirectory; icon=$s.IconLocation;"
            " desc=$s.Description; id=$f.ExtendedProperty('System.AppUserModel.ID')} | ConvertTo-Json"
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            env={**os.environ, "SHORTCUT_PATH": str(link)},
            capture_output=True,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", errors="replace"))
        return json.loads(result.stdout.decode("utf-8-sig"))

    def test_install_writes_icon_and_shortcut_with_app_id(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) / "桌面 测试"  # 中文和空格，确认宽字符路径没问题
            folder.mkdir()
            icon = Path(temp) / "app.ico"
            links = gui.install_shortcuts([folder], icon)
            self.assertEqual(links, [folder / f"{gui.APP_NAME}.lnk"])
            self.assertEqual(icon.read_bytes(), gui.icon_ico())

            info = self.read_back(links[0])
            self.assertTrue(os.path.samefile(info["target"], gui.gui_launcher()))
            self.assertEqual(info["args"], f'"{gui.GUI_SCRIPT}"')
            self.assertTrue(os.path.samefile(info["dir"], gui.ROOT))
            icon_file, icon_index = info["icon"].rsplit(",", 1)
            self.assertTrue(os.path.samefile(icon_file, icon))
            self.assertEqual(icon_index, "0")
            self.assertEqual(info["id"], gui.APP_ID)

    def test_shortcut_folders_exist(self):
        for folder in gui.shortcut_folders():
            self.assertTrue(folder.is_dir(), folder)

    def test_launcher_prefers_windowed_python(self):
        launcher = Path(gui.gui_launcher())
        self.assertTrue(launcher.exists())
        if Path(sys.executable).with_name("pythonw.exe").exists():
            self.assertEqual(launcher.name.lower(), "pythonw.exe")


if __name__ == "__main__":
    unittest.main()
