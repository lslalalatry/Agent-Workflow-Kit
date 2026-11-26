# 架构知识库导览（Architecture Vault）

> 本目录采用模块化文档结构（兼容 Obsidian、VS Code 与任意编辑器），将系统技术设计按关注点拆分为独立契约，避免单份规格说明书膨胀失控。
> - 日常进度、阻塞与接力锚点见 [../tracking/STATUS.md](../tracking/STATUS.md) 与 [../tracking/TODO.md](../tracking/TODO.md)。
> - 正式需求真源与公式契约见 [../tracking/SPEC.md](../tracking/SPEC.md)（涉计算见 `FORMULA.md`）。

## 目录结构说明

| 文档 / 目录 | 唯一职责 | 更新时机 |
| :--- | :--- | :--- |
| [DRAFT.md](./DRAFT.md) | 未定稿构想、多方案比选、待澄清问题缓冲区 | 讨论过程中随时记录；拍板后清理或归档 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 存量基础设施盘点、系统分层拓扑、集中存储与图片/媒体存储方案 | 立项定稿及重大架构调整时 |
| [DATA_MODEL.md](./DATA_MODEL.md) | 集中库 Schema 规划、实体关系、幂等键、状态机与迁移契约 | 表结构或状态机变更前 |
| [SECURITY_AND_AUTH.md](./SECURITY_AND_AUTH.md) | 角色权限矩阵（RBAC）、数据行级隔离与密钥安全边界 | 涉及账号、权限或外部鉴权时 |
| [API_AND_UI_STATES.md](./API_AND_UI_STATES.md) | 接口响应规范、错误码表与列表/详情多态接入清单 | 新增/变更接口或页面状态时 |
| [DEPLOYMENT_AND_QA.md](./DEPLOYMENT_AND_QA.md) | 环境配置矩阵、部署检查、监控告警、备份还原演练与回滚入口 | 联调上线、改配置或变更部署脚本时 |
| `modules/` | 复杂系统的子模块专项说明书（**一模块一 `.md` 卡**，复制 `modules/_TEMPLATE.md` 使用；做完即推 `main` 并新开窗口） | 新增/调整/下线子模块时 |
| `images/` | 纯架构图、原型截图等轻量文档插图（**严禁放入业务数据图或 `> 50MB` 大文件**） | 补充架构或界面说明时 |
