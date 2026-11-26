# Agent-Workflow-Kit 当前状态

## 接入盘点 · 2026-11-19

接入前，main 与已知 origin/main 同在 baaf366，工作区干净。远端为 lslalalatry/Agent-Workflow-Kit。

使用者从 README.md、使用指南.html 或已安装的 skills/project-guardian/SKILL.md 进入。初始化入口是 skills/project-guardian/scripts/init_project.py。两端安装入口是 scripts/sync_global.py。

接入盘点未发现数据库文件或持久化业务服务。

- **初始化实测**：2026-11-19T13:39:57+08:00 · 通过（仓库结构、分支、存储和追踪文档）  <!-- guardian-init -->

## 断点接力锚点

D-001 已同步到决策、产品说明与交付待办。当时用临时仓库运行 11 项回归，覆盖实际提交和向本地裸仓库推送。

D-002 的口令已在 README 和离线指南逐字核对。浏览器实测升级口令复制正确，切回首次接入可继续使用原选项。

D-003 已落地：双盲红队挑刺改为纯手动点名触发，常规功能修改直接快改快验。母版模板、技能手册、README 与离线指南已对齐，双端全局已同步，内嵌脚本语法检查与 11 项回归测试全部通过。

D-004 已落地：新增双轨理论白皮书 docs/THEORETICAL_FOUNDATIONS.md 并在 README.md 接入导读入口，常驻规则保持零膨胀，脱敏核查、安检闸机与 11 项回归测试全部通过。

D-005 已落地：新增通用架构蓝图手册 01a-architecture-blueprint.md、模块化 docs/architecture/ 与 deploy/ 模板及 --with-architecture 初始化选项，双端全局已同步，等待 commit 与 GitHub 推送确认。

下轮修改先看本轮提交及工作区差异。运行 python3 -B -m unittest discover -s tests -v 核对提交和推送行为。
