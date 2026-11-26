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

## 渐进式文档检索、原子断言与仓库一致性回归

D-007 补齐四项工程化防漂移能力：1）`tests/test_coherence.py` 自动化校验母版模板同源、`init_project.py` CLI 开关与 `SKILL.md` 一致性及全仓 Markdown 相对链接可达；2）`project-template/docs/tracking/SPEC.md` 术语表强制关联 `Reference` 落点，`modules/_TEMPLATE.md` 与 `API_AND_UI_STATES.md` 要求正常+反例原子断言（`Expectations`），`06-shared-decisions.md` 与 `07-code-review.md` 强制逐字核对 `D-编号`/`F-编号` 原文禁止凭记忆猜阈值；3）`API_AND_UI_STATES.md` 与 `01a-architecture-blueprint.md` 接入 `Browser Baseline`（默认 `Baseline Widely Available`）与 `modern-web-guidance` 协同；4）`skills/project-guardian/scripts/query_docs.py` 提供零第三方依赖的 `search`（紧凑索引）与 `read`（分段章节读取）CLI。

## 原生 Swarm 多工匠协同与分片门禁（方案 A）

D-008 打通 `project-guardian` 与原生 `/swarm` 协同：1）`SKILL.md` 仅在 `/swarm` 激活时路由 `08-swarm-orchestration.md`；2）Coordinator 为 `docs/tracking/` 唯一写者并维护 `swarm_pane` 交付视图，Author 在 `share` 工作区的 `swarm/<worker>` 分支并行开发各自模块及 `modules/*.md`，合回销毁后再派独立 Verifier 完成跨模块审查与默认入口验收；3）`verify_guardrails.py` 兼容过程态次级 worktree 与 `swarm/*` 分支（`--swarm-active`），同时在 `main` 正式提交收口时继续强制零分片残留、单一主干。

D-009 补充 `/swarm` 自动感应触发机制：已接入项目（`project-template/AGENTS.md` §5）在启动 `/swarm` 时自动先读 `08-swarm-orchestration.md`；未接入目录通过全局规则 `COLLABORATION_PRINCIPLES.md` §14 按「轻度（不建档）/ 中度（`--with-decisions`）/ 深度（`--with-architecture` 全套）」任务分级自动判定或单句确认后接入。

D-010 强化三项工程细节：1）`verify_guardrails.py` 在主分支正式收口时硬拦截残留 `git worktree`；2）`scripts/sync_global.py` 双端全局规则均做覆盖前当日备份并支持 `--dry-run`；3）`query_docs.py` 新增 `modules` 模块卡进度总览与 `search --any` OR 匹配。
