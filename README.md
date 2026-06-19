# Chaoxing Course Watcher

这是一个用于 **学习通 / 超星课程自动化观看** 的脚本项目。

最开始写这个脚本，是因为一些水课刷课会占用太多重复时间，所以用 vibe coding 的方式搓了一个自动化工具出来。当前文件夹是从根目录中拆分出来的课程观看项目，自动化逻辑复制自根目录的 `main.py`，核心逻辑保持不变。

> 本项目仅供学习交流与自动化技术研究使用，请遵守学校、课程平台及相关服务条款，不要用于任何违规用途。

## Setup

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Run

Use the launcher:

```powershell
.\run_chaoxing.ps1 --course "课程名称关键词" --headless --fast-actions --browser-channel chrome
```

Or run the Python entry directly:

```powershell
python main.py --course "课程名称关键词" --max-chapters 200 --headless --fast-actions --browser-channel chrome
```

Useful checks:

```powershell
python -m py_compile main.py
python main.py --help
```

Credentials and runtime settings should stay in local `.env` or process environment variables.

Do not commit `.env`, logs, screenshots, cookies, tokens, or passwords.
