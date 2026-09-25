# 命名迁移：Agent NetPilot → 云驿（yunyi）

本次是独立命名提交，不修改执行政策、状态机、任务依赖、阈值或审批。没有产品代码，所有运行时兼容规则均为已有实现任务的命名约定，不能宣称已实现。

## 映射

| 旧名 | 新名 |
|---|---|
| Agent NetPilot | 云驿（yunyi） |
| netpilot-foundation | yunyi-foundation |
| netpilot-execution | yunyi-execution |
| netpilot-integration | yunyi-integration |
| netpilot / src/netpilot | yunyi / src/yunyi |
| NETPILOT_* | YUNYI_* |
| ~/.netpilot/ | ~/.yunyi/ |
| netpilot.db | yunyi.db |
| MCP server netpilot | MCP server yunyi |
| netpilot_get_state等八工具 | yunyi_get_state等对应八工具 |

任务局部编号、顺序和勾选状态完全不变。完整标识按前缀转换，例如`netpilot-foundation-1.2`→`yunyi-foundation-1.2`。原先使用局部编号的任务继续使用原编号，不凭空添加或重排。

## 环境变量兼容约定

首次兼容实现中，每次进程启动解析配置时只做一次别名解析：`YUNYI_*`存在则优先，只有不存在时才fallback读取对应的`NETPILOT_*`。新值为空不触发回退，应按原验证规则报错。保留四个后缀：SESSION_ID、DB_PATH、LOG_LEVEL、OFFLINE_MODE。旧名命中只发一次不含值的弃用提示，不回写环境，不改变参数高于环境变量的优先级。

显式DB路径（包括旧名fallback获得的路径）仍按用户配置使用，不能偷偷搬迁。默认路径才是`~/.yunyi/yunyi.db`。本轮未实现fallback读取器，不将该行为标成已完成。

## 一次性旧数据迁移

本次只检查用户目录两个候选位置及仓库spike数据库文件：均未发现，不存在需要迁移的数据，也没有操作用户全局配置。

若其他安装确有旧数据，先停止所有旧daemon、wrapper、MCP和执行器，使SQLite正常关闭；保留旧目录作为备份。两个目录同时存在时必须停下核对，不能覆盖或合并数据库。以下PowerShell步骤只适用于已正常关闭、没有WAL/SHM/journal残留且目标不存在的旧安装；不会由本项目自动运行：

```powershell
$sourceDir = Join-Path $env:USERPROFILE '.netpilot'
$targetDir = Join-Path $env:USERPROFILE '.yunyi'
if (-not (Test-Path -LiteralPath $sourceDir -PathType Container)) { throw 'Legacy directory missing' }
if (Test-Path -LiteralPath $targetDir) { throw 'Destination exists; compare manually' }
if (-not (Test-Path -LiteralPath (Join-Path $sourceDir 'netpilot.db') -PathType Leaf)) { throw 'Legacy database missing' }
if (Test-Path -LiteralPath (Join-Path $sourceDir 'yunyi.db')) { throw 'Mixed database names; compare manually' }
if (Get-ChildItem -LiteralPath $sourceDir -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Linked path requires manual inspection' }
if (Get-ChildItem -LiteralPath $sourceDir -File | Where-Object { $_.Name -match '-(wal|shm|journal)$' }) { throw 'SQLite sidecars remain; close and inspect database first' }
Copy-Item -LiteralPath $sourceDir -Destination $targetDir -Recurse -ErrorAction Stop
Rename-Item -LiteralPath (Join-Path $targetDir 'netpilot.db') -NewName 'yunyi.db' -ErrorAction Stop
```

复制保留config、日志、快照及原始字节；不改变数据库schema、session ID或检查点。复制失败时不要删除旧目录，不直接重试覆盖不完整目标。核验新旧数据库内容hash、SQLite integrity_check和快照清单，再通过新的显式DB路径做只读检查。如果配置或账本含绝对旧路径，保留旧备份可用并逐项核对，不对数据库文件做字符串替换。

验证后将配置中显式旧DB/快照路径改为相应新位置，把环境变量改为新名。不能仅因改名就删除旧目录或宣称跨版本迁移成功。若数据库由未知第三方旧版本产生，应先确认其schema兼容性。

## 已装MCP用户迁移

1. 备份自己的Claude/Codex配置并停止旧server进程。
2. 使用examples中的新模板替换对应条目：Claude的`mcpServers.netpilot`改为`mcpServers.yunyi`，Codex的`mcp_servers.netpilot`改为`mcp_servers.yunyi`。
3. 将启动命令/模块名、环境变量及显式DB路径同步改为新名；避免新旧server同时连接同一账本。
4. 工作流、提示词或权限规则中的八个旧工具名逐一改为对应`yunyi_*`；本次不承诺旧CLI和旧MCP工具别名可运行。
5. 待产品实际安装后重新连接、查询工具列表和会话状态，再验证原有会话数据。当前模板仅表示命名契约，不能作为已安装产品的证据。

## 原始证据保留

`docs/source-design.md`及迁移前已跟踪的`docs/evidence/*`逐字节保留，包括旧spec名称、日志和SHA256。历史名称应通过上表解释，不改写旧实验。新机械结果写入`docs/evidence/yunyi-sdd-mechanical-check.json`；命名完整性结果另存`docs/evidence/yunyi-naming-check.json`。

`.spikes/mcp_probe.py`及对应测试的server标签同步改名，但历史运行日志仍保留旧标签。TDD示例window实现、冻结测试和其验证证据均不改动。本轮依赖复测不调用云模型，不算新增产品行为的TDD。
