# Agent-Workflow-Kit 产品说明

## 现有入口与数据

使用者从 README.md、使用指南.html 或已安装的 skills/project-guardian/SKILL.md 进入。初始化入口是 skills/project-guardian/scripts/init_project.py。两端安装入口是 scripts/sync_global.py。

接入盘点未发现数据库文件或持久化业务服务。

## 提交与上传的验收条件

D-001 要求 AI 实读本次差异，核对重复实现、复杂分支、依赖与回归风险。阻断问题必须修复并复审。提交时核对最终暂存内容。推送时逐项核对将上传的提交。同一差异沿用本地审查记录。

实现复用已有 Git 钩子、Git 快照与本地记录的原子写入工具。审阅方法借鉴 ECC 的差异审查与具体问题分级。2026-11-19 查询时仓库有 306,702 星，审阅器在 2026-07-26 修复了工具声明格式。[审阅器来源](https://github.com/affaan-m/ECC/blob/6a9f075cd97c139a5f7e84e1e3f2c9ab095adf64/agents/code-reviewer.md)

## 老项目升级入口

D-002 要求 README 提供可直接复制的升级口令。离线指南提供同名独立场景，复制的内容与 README 一致。

## 按需红队与日常快车道

D-003 要求默认关闭双盲红队平行挑刺。新项目首次立项与日常迭代均禁止自动派发红队子任务，仅当用户当轮明确要求红队、辩论或挑刺审查时才执行 `02-dual-redteam-audit.md`。范围明确的常规功能修改跳过阶段 1 至阶段 3 仪式，直接实读实测并更新受影响追踪文档。

## 跨学科理论白皮书与常驻规则分离

D-004 新增独立离线文档 `docs/THEORETICAL_FOUNDATIONS.md`，以「学术理论原名与出处 + 生活化直白解释」双轨结构沉淀脱敏双领域实证样本、七大跨学科理论与工程机制映射表。`README.md` 提供导读链接，常驻 `AGENTS.md` 与 `SKILL.md` 不混入理论长文。

## 通用分域架构蓝图（`--with-architecture`）

D-005 要求 `init_project.py` 支持 `--with-architecture`（对应 `AGENTS.md` 中 `enable_architecture_doc: true`），非覆盖式生成 `docs/architecture/` 分域模板（`README`、`DRAFT`、`ARCHITECTURE`、`DATA_MODEL`、`SECURITY_AND_AUTH`、`API_AND_UI_STATES`、`DEPLOYMENT_AND_QA`、`images/`、`modules/`）与 `deploy/README.md`。`01a-architecture-blueprint.md` 指导 AI 开局先盘点已有数据库与云基础设施，再对齐集中存储、图片对象存储、权限、UI 多态与回滚。`verify_guardrails.py` 在启用 `enable_architecture_doc` 时核查核心架构文档存在，免除纯文档变更对 `STATUS.md` 的强制绑定，同时继续拦截目录内未登记数据库与超大文件。

## 子模块闭环、主线推送策略与增减功能规程

D-006 为多模块长任务建立四项机制：1）`docs/architecture/modules/_TEMPLATE.md` 定义一模块一卡标准格式；2）`AGENTS.md` 新增 `delivery_mode`（`prompt_push_on_done` 默认强提醒 | `auto_push_main_when_clean` 经 `--auto-push` 开启且满足全绿/审查/闸机/无冲突 `rebase` 时自动提交推 `main`）；3）子模块推平后主动发出「🟢 本任务已完结，建议立即新开对话框」信号；4）临近收尾时新增功能先登记进 `DRAFT.md / BACKLOG.md` 不打断当前主线闭环，减功能按锁决策、清入口、保只读历史数据与全量复测四步下线。
