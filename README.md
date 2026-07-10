# Chaoxing Course Watcher

一个用于学习 **Playwright 浏览器自动化** 的示例项目，目标场景是学习通 / 超星课程页面的自动化操作。

> 重要说明：本项目仅供个人学习、自动化技术研究和代码参考使用。请遵守学校、课程平台和相关服务条款。不要把它用于违规刷课、绕过平台验证、逃避学习要求或其他不当用途。

## 功能概览

- 使用 Playwright 打开学习通 / 超星登录页。
- 从本地环境变量读取账号、密码和课程关键词。
- 按课程关键词评分选择课程，或使用本地配置的授权课程 URL 直接进入。
- 尝试识别章节目录中的未完成任务点。
- 检测视频、课件、iframe 等学习内容。
- 遇到平台验证码或人工验证时停止或等待人工处理，不做绕过。
- 保存调试截图到本地 `logs/screenshots`，便于排查页面选择器问题。

## 开源前的隐私保护

本仓库不应该包含你的真实账号、密码、cookie、token、截图或日志。

已经配置 `.gitignore` 忽略以下高风险内容：

- `.env` 和其他本地环境变量文件
- `logs/`、截图、运行日志
- cookies、storage state、浏览器会话文件
- token、key、证书、credentials 文件
- Python 缓存、虚拟环境和构建产物

开源前建议再检查一次：

```powershell
git status
git grep -n "CX_PASSWORD\|password\|token\|cookie\|secret\|账号\|密码"
```

如果你曾经把真实密码、cookie 或 token 提交进 Git 历史，仅删除文件不够，需要轮换对应凭据，并清理 Git 历史后再公开仓库。

## 环境要求

- Python 3.10+
- Playwright
- Chromium 或本机 Chrome

安装依赖：

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## 配置方法

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`：

```dotenv
CX_USERNAME=你的账号或手机号
CX_PASSWORD=你的密码
CX_COURSE_KEYWORD=课程名称关键词
CX_COURSE_URL=
```

`.env` 只保存在本地，不要提交到仓库。

## 运行方法

推荐使用 PowerShell 启动脚本：

```powershell
.\run_chaoxing.ps1 --course "课程名称关键词" --browser-channel chrome
```

也可以直接运行 Python 入口：

```powershell
python main.py --course "课程名称关键词" --max-chapters 100 --browser-channel chrome
```

如果需要显示浏览器窗口，确保不要开启 headless：

```powershell
python main.py --course "课程名称关键词" --browser-channel chrome
```

如果你明确要无头模式：

```powershell
python main.py --course "课程名称关键词" --headless --browser-channel chrome
```

如果课程名称匹配存在歧义，请传入更完整的课程名称；已有准确的授权课程 URL 时，也可以从本地环境直接指定：

```powershell
python main.py --course-url $env:CX_COURSE_URL --headless --browser-channel chrome
```

## 常用参数

| 参数 | 说明 |
|---|---|
| `--course` | 课程名称关键词 |
| `--course-url` | 直接打开本地配置的授权课程 URL，并跳过课程名称匹配 |
| `--chapter` | 指定章节关键词，可选 |
| `--max-chapters` | 最多处理的章节数量 |
| `--headless` | 使用无头浏览器模式 |
| `--fast-actions` | 缩短部分等待时间 |
| `--browser-channel chrome` | 使用本机 Chrome |

更多参数：

```powershell
python main.py --help
```

## 验证和排错

语法检查：

```powershell
python -m py_compile main.py
```

查看帮助：

```powershell
python main.py --help
```

常见问题：

| 问题 | 处理方式 |
|---|---|
| 找不到课程或匹配有歧义 | 使用更完整的 `CX_COURSE_KEYWORD` / `--course`；已有准确授权 URL 时使用 `CX_COURSE_URL` / `--course-url` |
| 登录失败 | 检查 `.env` 里的账号和密码；不要把真实信息提交到仓库 |
| 出现验证码 | 手动处理；脚本不会绕过验证码 |
| 找不到视频 | 尝试关闭 headless，观察页面结构是否变化 |
| 页面选择器失效 | 查看 `logs/screenshots` 里的调试截图，并更新 `main.py` 里的 selectors |

## 项目结构

```text
.
├── main.py              # 主程序入口
├── run_chaoxing.ps1     # PowerShell 启动脚本
├── requirements.txt     # Python 依赖
├── .env.example         # 本地配置模板，不含真实凭据
├── .gitignore           # 隐私和运行产物忽略规则
├── tests/               # 课程匹配和关闭页面保护的回归测试
├── docs/                # 状态、任务、架构和决策文档
├── SECURITY.md          # 敏感信息和安全报告说明
└── README.md            # 项目说明
```

## 安全原则

- 不要提交 `.env`。
- 不要提交截图、日志、cookie、token 或浏览器会话文件。
- 不要在 issue、PR、commit message 中粘贴账号密码。
- 如果怀疑凭据泄露，立即修改密码并清理 Git 历史。
- 不要尝试绕过验证码、风控或平台限制。

## 许可证

开源前请自行选择许可证，例如 MIT、Apache-2.0 或 GPL。未添加许可证时，默认不代表他人可以自由复制、修改或分发。
