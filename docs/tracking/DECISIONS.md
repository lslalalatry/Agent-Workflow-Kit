# Agent-Workflow-Kit 决策记录

## D-001 · 2026-11-19 · 生效

用户要求 AI 在提交和上传前审查待交付改动。修复阻断项后复审。上传时可复用匹配的记录。新接入项目通过初始化安装两个 Git 钩子。

<!-- guardian-decision D-001 affects=BACKLOG.md,SPEC.md,STATUS.md,TODO.md -->

## D-002 · 2026-11-19 · 生效

README 和离线使用指南分别列出首次接入和已接入项目升级。两处采用同一句升级口令，落实 D-001 的两项本地检查。

<!-- guardian-decision D-002 affects=SPEC.md,STATUS.md -->

## D-003 · 2026-11-23 · 生效

用户要求将双盲红队平行挑刺改为纯手动点名触发。新项目首次立项与日常功能迭代均禁止自动运行红队辩论，仅当用户当轮明确开口要求红队、辩论或挑刺时才调用。范围明确的常规功能修改直接快改快验并同步受影响文档，禁止启动繁琐立项仪式。改动同步至本机双端全局目录与 GitHub 远端。

<!-- guardian-decision D-003 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-004 · 2026-11-24 · 生效

用户批准采用「学术理论原名与出处 + 生活化直白解释」双轨写法，将两类长周期项目的脱敏实证病灶与七大跨学科理论溯源写入独立离线白皮书 `docs/THEORETICAL_FOUNDATIONS.md`，在 `README.md` 增加导读入口并保持常驻 `AGENTS.md` 与 `SKILL.md` 零膨胀，同步推送至 GitHub 远端。

<!-- guardian-decision D-004 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-005 · 2026-11-26 · 生效

用户参考外部模块化项目框架，要求将 `project-guardian` 升级为通用架构治理技能：每次新项目或重大架构启动前，支持先盘点已有数据库与基础设施并落盘完整通用架构蓝图（集中存储、图片对象存储、数据模型、权限与凭据、接口与 UI 多态清单、`DRAFT.md` 草稿缓冲区、QA 部署与回滚），新增 `--with-architecture` 与 `references/01a-architecture-blueprint.md`，并同步至双端全局技能目录。

<!-- guardian-decision D-005 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-006 · 2026-11-26 · 生效

用户确认两项主线闭环与范围治理策略：1）新增 `delivery_mode` 配置项及 `--auto-push` 初始化选项（`auto_push_main_when_clean` 在测试全绿、代码审查、安检闸机与无冲突 `rebase` 全部通过后自动提交推送 `main`；默认 `prompt_push_on_done` 在结尾输出强提醒卡），并在子模块完结推平后主动提示“可以新开对话框”；2）一子模块一卡（`modules/_TEMPLATE.md`），临近收尾时的新功能需求默认先登记入 `DRAFT.md / BACKLOG.md` 待当前推完 `main` 后新开窗口处理，减功能按四步软下线清理代码、保留只读历史并登记决策。同步全局规则、模板、指南并推送 GitHub。

<!-- guardian-decision D-006 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-007 · 2026-11-26 · 生效

用户批准结合 `GoogleChrome/modern-web-guidance-src` 设计思想同时落地四项强化：1）新增 `tests/test_coherence.py`，机械回归校验 `project-template` 与打包副本一致、`init_project.py` 全量 CLI 开关在 `SKILL.md` 文档齐全以及全仓内部 Markdown 相对链接无死链；2）`SPEC.md` 术语表增加 `代码/表落点（Reference）` 列，模块设计卡与 `API_AND_UI_STATES.md` 升级为带正常+反例的原子验收断言（`Expectations`），并在 `06-shared-decisions.md` 与 `07-code-review.md` 严禁凭长对话压缩记忆猜测约束/阈值、强制逐字核对 `D-编号`/`F-编号` 原文；3）在 `API_AND_UI_STATES.md` 与 `01a-architecture-blueprint.md` 增加 `Browser Baseline`（默认 `Baseline Widely Available`）策略位及 `modern-web-guidance`（`search -> retrieve`）原生前端协同指引；4）新增零第三方依赖脚本 `skills/project-guardian/scripts/query_docs.py`（`search` 紧凑索引 + `read` 章节/行号分段读取），供多模块大项目渐进式按需查询。

<!-- guardian-decision D-007 affects=BACKLOG.md,SPEC.md,STATUS.md -->
