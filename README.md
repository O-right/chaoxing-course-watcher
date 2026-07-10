# Chaoxing Course Watcher

一个基于 Python 和 Playwright 的学习通 / 超星课程自动化项目。

课程中有些操作高度重复：反复进入任务点、切换资源卡片、等待视频播放结束，往往会消耗大量时间和精力。这个项目希望在账号本人授权、课程允许且遵守平台规则的前提下，用浏览器自动化减少这些重复操作，把时间留给真正需要理解和学习的内容。

> 本项目仅供个人学习、Playwright 自动化研究和代码参考。请遵守学校规定、课程要求以及学习通 / 超星的服务条款。项目不会绕过验证码、短信验证、MFA、访问控制或平台风控

## 功能概览

- 从本地 `.env`、环境变量或命令行参数读取运行配置。
- 登录学习通 / 超星，并按课程名称评分选择授权课程。
- 在课程名称存在歧义时停止并输出候选信息，避免误进课程。
- 支持使用本地保存的准确课程 URL 跳过名称匹配。
- 查找章节目录和未完成任务点。
- 处理视频、课件、iframe 和混合资源卡片。
- 尝试恢复暂停、卡住、iframe 重建或视频源暂时不可用等情况。
- 仅在观察到明确完成状态后进入下一任务点。
- 在登录、选课、任务处理、视频播放或导航失败时保存本地调试截图。
- 页面被关闭或崩溃时停止使用失效的页面和视频定位器。

## 使用边界

本项目不会：

- 自动解决或绕过验证码、短信验证、MFA 和人工验证。
- 保证任何课程一定完成，也不会把未经验证的流程宣称为成功。

如果页面出现验证、账号异常或平台限制，请停止脚本并手动处理。

## 环境要求

- Windows 10/11
- Python 3.10 或更高版本
- PowerShell 7（推荐）
- Chromium，或本机安装的 Chrome / Edge

## 快速开始

### 1. 获取代码

```powershell
git clone https://github.com/O-right/chaoxing-course-watcher.git
Set-Location .\chaoxing-course-watcher
```

### 2. 安装依赖和浏览器

```powershell
python -m pip install -r requirements.txt
python -m playwright install chromium
```

如果希望使用本机 Chrome，可以跳过 Chromium 下载，并在运行时传入 `--browser-channel chrome`。

### 3. 创建本地配置

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`，至少填写登录信息和课程名称：

```dotenv
CX_USERNAME=你的账号或手机号
CX_PASSWORD=你的密码
CX_COURSE_KEYWORD=课程名称关键词
```



常用配置：

| 配置项 | 说明 |
|---|---|
| `CX_USERNAME` | 学习通 / 超星账号或手机号 |
| `CX_PASSWORD` | 登录密码 |
| `CX_COURSE_KEYWORD` | 课程名称中的稳定关键词 |
| `CX_COURSE_URL` | 可选；准确的授权课程 URL，设置后跳过名称匹配 |
| `CX_CHAPTER_KEYWORD` | 可选；希望开始处理的章节关键词 |
| `CX_BROWSER_CHANNEL` | 可选；例如 `chrome` 或 `msedge` |
| `CX_HEADLESS` | 是否使用无头模式，首次运行建议设为 `false` |
| `CX_MAX_CHAPTERS` | 单次最多连续处理的任务点数量 |
| `CX_PLAYBACK_RATE` | 尝试设置的播放倍速，实际值可能受平台限制 |
| `CX_AUTO_COMMITMENT` | 是否自动确认学习承诺，默认 `false`；仅在本人阅读并同意后开启 |
| `CX_MANUAL_VERIFICATION_WAIT_SECONDS` | 遇到人工验证时等待手动处理的秒数 |
| `CX_SCREENSHOT_DIR` | 失败截图目录，默认是 `logs/screenshots` |

完整配置示例见 [`.env.example`](.env.example)。

### 4. 运行

推荐使用 PowerShell 启动脚本：

```powershell
.\run_chaoxing.ps1 --course "课程名称关键词" --browser-channel chrome
```

也可以直接运行 Python：

```powershell
python main.py --course "课程名称关键词" --max-chapters 100 --browser-channel chrome
```

首次运行建议使用可见浏览器，便于观察登录、课程匹配和平台验证：

```powershell
python main.py --course "课程名称关键词" --headed --browser-channel chrome
```

确认流程稳定后再考虑无头模式：

```powershell
python main.py --course "课程名称关键词" --headless --browser-channel chrome
```

从指定章节开始：

```powershell
python main.py --course "课程名称关键词" --chapter "章节关键词" --browser-channel chrome
```

如果课程名称匹配有歧义，优先使用更完整的课程名称。已有准确的授权课程 URL 时，可以将 `CX_COURSE_URL` 写入本地 `.env`，然后直接运行：

```powershell
python main.py --headed --browser-channel chrome
```

也支持 `--course-url` 参数，但私有 URL 直接出现在命令行中可能被 shell 历史或进程列表记录，因此更推荐保存在本地 `.env`。

## 常用命令行参数

| 参数 | 说明 |
|---|---|
| `--course` | 课程名称关键词，覆盖 `CX_COURSE_KEYWORD` |
| `--course-url` | 直接打开授权课程 URL，覆盖 `CX_COURSE_URL` |
| `--chapter` | 起始章节关键词 |
| `--max-chapters` | 单次最多连续处理的任务点数量 |
| `--headed` | 使用可见浏览器 |
| `--headless` | 使用无头浏览器 |
| `--fast-actions` | 缩短部分等待时间，仅建议用于已验证的授权测试 |
| `--progress-poll-seconds` | 视频进度轮询间隔 |
| `--courseware-hold-seconds` | 非视频课件的停留时间 |
| `--manual-verification-wait-seconds` | 人工验证等待时间 |
| `--browser-channel` | 使用系统浏览器通道，例如 `chrome` 或 `msedge` |
| `--browser-executable` | 指定浏览器可执行文件路径 |

查看全部参数：

```powershell
python main.py --help
```

## 工作流程

1. 读取本地配置并启动浏览器。
2. 登录学习通 / 超星。
3. 按关键词评分选择课程，或打开已配置的授权课程 URL。
4. 定位指定章节或未完成任务点。
5. 依次处理当前页面中的课件和视频资源。
6. 等待可观察的完成状态。
7. 确认下一任务点可用并验证页面确实发生变化。
8. 达到配置上限，或确认没有未完成任务点后退出。

## 常见问题

| 问题 | 处理方式 |
|---|---|
| 找不到课程 | 使用课程标题中更完整、更稳定的关键词 |
| 匹配到多个相近课程 | 使用完整课程名称，或在本地配置准确的 `CX_COURSE_URL` |
| 登录失败 | 检查本地 `.env` |
| 出现验证码或操作异常 | 使用 `--headed` 手动处理，或停止运行；脚本不会绕过验证 |
| 浏览器意外关闭 | 尝试可见模式、本机 Chrome，并查看终端中的关闭原因 |
| 找不到视频或页面结构变化 | 查看本地 `logs/screenshots`，必要时更新可配置 selector |
| 视频长时间无进度 | 检查网络、播放器状态和平台倍速限制 |

## 验证

```powershell
python -m unittest discover -s tests
python -m py_compile main.py tests\test_closed_page_guards.py tests\test_course_matching.py
python main.py --help
git diff --check
```

本地测试只能验证确定性的匹配和页面关闭保护逻辑。只有在本人授权的真实课程上完成有界运行，才能说明对应线上流程已经验证。

## 隐私与安全

- `.env`、日志、截图、cookie、token、浏览器会话和私有课程 URL 均不应进入 Git。
- 调试截图可能包含姓名、学号、课程信息或其他个人数据，公开前必须检查。
- 项目不会绕过验证码、风控、访问控制等
- 更多说明见 [SECURITY.md](SECURITY.md)。

## 项目结构

```text
.
├── main.py                       # 主程序入口
├── run_chaoxing.ps1              # PowerShell 启动脚本
├── requirements.txt              # Python 依赖
├── LICENSE                       # MIT 开源许可证
├── .env.example                  # 不含真实凭据的配置模板
├── .gitignore                    # 隐私、运行产物和缓存忽略规则
├── .github/                      # CI 与 Dependabot 配置
├── tests/                        # 确定性回归测试
├── docs/                         # 状态、任务、架构、决策和产品范围
├── SECURITY.md                   # 敏感信息与安全报告说明
├── security_best_practices_report.md # 开源前安全与发布体检报告
└── README.md                     # 项目说明
```

## 当前限制

- 学习通 / 超星页面结构可能变化，selector 可能需要更新。
- 播放倍速、视频源和完成状态受课程配置与平台策略影响。
- 自动确认学习承诺默认关闭，只有本人阅读并同意相关内容后才应主动开启。
- 无头浏览器与可见浏览器的页面行为可能不同。
- 项目目前没有针对私人真实课程的 CI。

## 许可证

本项目采用 [MIT License](LICENSE) 开源。你可以使用、复制、修改和分发代码，但需要保留原始版权与许可证声明；软件按“原样”提供，不附带任何担保。

## 支持项目

如果这个项目帮你节省了时间，或者其中的 Playwright 自动化实现对你有参考价值，欢迎点一个 Star。你的支持会让项目更容易被需要的人看到。
