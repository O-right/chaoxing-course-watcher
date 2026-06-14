# Chaoxing Course Watcher

This folder is the split-out course watching project. The automation logic is copied unchanged from the root `main.py`.

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

Credentials and runtime settings should stay in local `.env` or process environment variables. Do not commit `.env`, logs, screenshots, cookies, tokens, or passwords.
