# 开源前安全与发布体检报告

体检日期：2026-07-10

## 执行摘要

本次体检覆盖 Python + Playwright 主程序、PowerShell 启动脚本、公开文档、GitHub 配置、当前工作树和完整 Git 历史。

MIT 许可证已经添加；仓库所有者明确接受现有提交历史中的个人邮箱和课程验证信息，不进行历史重写。gitleaks 对 Git 历史和当前目录的专用扫描均未发现秘密。pip-audit 首次发现 `python-dotenv==1.2.1` 存在 Medium 漏洞 `CVE-2026-28684`，升级到首个修复版本 `1.2.2` 后复扫为 0 个已知漏洞。

当前没有未处理的高危或中危自动化体检发现。仓库仍为 Private，下一步由所有者审核 README、审查并合并 Draft PR，最后再手动改为 Public。

本项目使用 Python、Playwright 同步 API 和 PowerShell。已安装的安全审查技能没有专门适用于“Python + Playwright 本地浏览器自动化”的框架参考，因此代码部分依据通用凭据管理、日志最小化、安全默认值和供应链原则审查。

## 审查范围

- 检查 Git 工作树、跟踪文件、忽略规则、许可证和大文件。
- 使用自定义规则扫描完整 Git 历史中的敏感路径、高置信凭据、课程 ID URL 参数和手机号模式。
- 使用 gitleaks 扫描 Git 历史和当前工作目录。
- 使用 pip-audit 检查固定 Python 依赖及其传递依赖。
- 检查 URL、异常、课程候选和页面跳转的终端输出路径。
- 核对 GitHub 仓库可见性、Draft PR、CI、Dependabot 和社区健康文件。
- 运行单元测试、语法检查、CLI 帮助、依赖检查和差异检查。

## 当前发现

### 严重 / 高 / 中

无未处理发现。

### 低：OSR-001 社区健康文件仍不完整

GitHub 社区健康度为 28%，缺少贡献指南、行为准则、Issue 模板和 PR 模板。这些文件不阻止小型个人项目公开，但会降低外部贡献的可预期性。

建议：只有在项目开始接收较多外部贡献时，再补充 `CONTRIBUTING.md`、`CODE_OF_CONDUCT.md` 和最小 Issue/PR 模板。

## 已接受的隐私选择

### PRIV-001 保留现有 Git 历史

旧提交使用非 GitHub noreply 的个人邮箱，历史状态文档和测试也包含具名课程验证数据。仓库所有者已明确接受这些信息公开，不执行会改变提交 SHA 的历史重写。新的开源准备提交继续使用 GitHub noreply 邮箱。

## 已修复问题

### LICENSE-FIX-001 添加 MIT 许可证

- 添加标准 [MIT LICENSE](LICENSE)，版权标识为 `Copyright (c) 2026 O-right`。
- [README.md](README.md#许可证) 已说明使用、修改和分发条件以及无担保条款。

### SEC-FIX-001 终端日志中的私有 URL

- 新增统一 URL 脱敏函数：[main.py](main.py#L43) 和 [main.py](main.py#L64)。
- 页面关闭、元素查找、课程候选、导航异常和下一任务点日志不再输出 URL userinfo、路径、查询参数或片段。
- 回归测试覆盖 HTTP(S)、WebSocket、嵌入式 userinfo、课程 ID 和班级 ID。

### SAFE-FIX-001 公开仓库默认配置

- 课程关键词默认值改为空，必须通过本地配置或命令行明确指定：[main.py](main.py#L76)。
- 未提供课程关键词和课程 URL 时快速失败并给出配置提示：[main.py](main.py#L939)。
- 默认播放倍速改为 `1.0`：[main.py](main.py#L79)。
- 自动确认学习承诺默认关闭：[main.py](main.py#L98)。

### SUPPLY-FIX-001 修复已知依赖漏洞

- pip-audit 首次发现 `python-dotenv==1.2.1` 命中 [CVE-2026-28684 / GHSA-mf9w-mj56-hr94](https://github.com/advisories/GHSA-mf9w-mj56-hr94)。
- 漏洞等级为 Medium，影响是 `set_key` 在跨设备重命名回退时可能跟随符号链接并覆盖任意文件。
- [requirements.txt](requirements.txt) 已升级到首个修复版本 `python-dotenv==1.2.2`。
- pip-audit `2.10.1` 复扫 5 个直接和传递依赖，结果为 0 个已知漏洞。

### SUPPLY-FIX-002 依赖与自动检查

- 固定本机和 CI 验证过的 Python 依赖版本。
- [ci.yml](.github/workflows/ci.yml) 在 Windows 上检查 Python 3.10 / 3.11，使用只读权限和完整 SHA 固定官方 Action。
- [dependabot.yml](.github/dependabot.yml) 每周检查 pip 与 GitHub Actions 更新。

### DOC-FIX-001 中文使用文档

[README.md](README.md) 已提供完整中文说明，包括项目目的、授权边界、快速开始、配置、运行方式、参数、故障排查、验证、隐私安全、MIT 许可证和 Star 引导。

## 已通过检查

- 当前 `.env` 未被 Git 跟踪，并由 `.gitignore` 明确忽略。
- 自定义完整历史扫描未发现敏感路径文件、高置信凭据、课程 ID URL 参数或手机号模式。
- gitleaks `8.30.1` Windows x64 官方 ZIP SHA256 校验通过：`d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`。
- `gitleaks git --redact=100` 扫描 12 个提交，结果为 `no leaks found`。
- `gitleaks dir --redact=100` 扫描当前工作目录，结果为 `no leaks found`。
- pip-audit `2.10.1` 在依赖升级后报告 0 个已知漏洞。
- 当前跟踪文件中没有超过 1 MiB 的文件。
- `python -m pip check` 通过。
- 本地 14 项测试、Python 编译、直接 CLI 和 PowerShell 启动器帮助检查通过。
- GitHub Actions run [29083267002](https://github.com/O-right/chaoxing-course-watcher/actions/runs/29083267002) 在 Python 3.10 和 3.11 上通过。
- README 代码围栏成对，主要发布章节齐全。

## 未运行

- 真实学习通 / 超星完整课程流程：本次开源体检没有运行，也不能由离线测试替代。

## 公开前清单

- [x] 添加 MIT `LICENSE`。
- [x] 确认接受公开现有作者邮箱和历史课程信息。
- [x] 使用 gitleaks 完成 Git 历史和当前目录扫描。
- [x] 使用 pip-audit 完成依赖漏洞扫描并修复发现。
- [x] 推送开源准备分支并确认 GitHub Actions 通过。
- [ ] 所有者审核最终 README。
- [ ] 审查并合并 Draft PR #1。
- [ ] 最后把 GitHub 仓库可见性改为 Public。

## 发布判断

**自动化开源体检通过，等待所有者审核 README。**

许可证、历史隐私选择、秘密扫描、依赖漏洞扫描、本地验证和 CI 均已有明确结果。仓库仍保持 Private；所有者确认 README 后，再审查合并 PR 并手动公开。
