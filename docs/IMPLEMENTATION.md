# 实现与 scope 契约

## 目录

- `on_actions/fia_on_actions.txt`：向原版 `on_monthly_pulse_country` 附加唯一子 pulse。
- `scripted_effects/fia_state_effects.txt`：地区档案、紧张度、处置、保障、保护国筛选。
- `scripted_effects/fia_country_effects.txt`：跨国请求、任务清理、疲劳、国家概览。
- `scripted_triggers/fia_triggers.txt`：资格与身份检查。
- `diplomatic_plays/fia_plays.txt` / `war_goal_types/fia_war_goals.txt`：原生外交博弈与和平执行。
- `events/fia_events.txt`：8个国家事件。选项效果仍操作已保存并验证的地区。
- `decisions/fia_decisions.txt`：国内复审、干涉说明、撤回保护、撤销所有保障。
- `journal_entries/fia_journals.txt`：永久概览及当前保护承诺。

## 持久状态

| 持有者 | 变量 | 含义 |
| --- | --- | --- |
| State | `fia_case_owner` / `fia_faith` / `fia_tension` | 档案所有者、固定受影响宗教、0—100紧张度 |
| State | `fia_incident` | 重大事件，五年限时 |
| State | `fia_conciliation` / `fia_repression` | 一年限时地方处置状态 |
| State | `fia_patron` | 当前保护国对象 |
| State | `fia_accord_months` | 存在即保障有效，值0—60 |
| State | `fia_offer_cooldown` / `fia_case_cooldown` | 一年候选重试、五年成功履约冷却 |
| Country | `fia_mission_state` / `fia_mission_host` | 承诺绑定地区与原目标国 |
| Country | `fia_mission_age` / `fia_authorized` | 未进入博弈/保障的月龄、一年理由 |
| Country | `fia_play_started` / `fia_war_seen` / `fia_on_accord` | 博弈、战争、保障阶段标记 |
| Country | `fia_request_from` / `fia_request_state` / `fia_request_age` | 目标国唯一请求收件箱 |
| Country | `fia_patron_cooldown` / `fia_fatigue` | 三年干涉冷却、0—100疲劳 |
| Country | `fia_domestic_state` / `fia_domestic_cooldown` | 当前国内事件地区、年度处置冷却 |
| Country | `fia_case_count` / `fia_max_tension` | 月度概览缓存 |

临时 `scope:fia_*` 只在当前效果链或事件内用于选择和显示；跨月、跨事件的身份依赖 `var:*`，不能依赖同名临时 scope 的上次值。

## Pulse 顺序

1. 初始化国家疲劳与永久日志。
2. 对自有地区清理失效保护国、易主档案，必要时播种宗教档案。
3. 更新紧张度、保障计时、年度去激进化与完成处理。
4. 国内事件、重大事件、候选保护国邀请。
5. 重建国家概览缓存。
6. 更新干涉疲劳、检查任务身份及博弈/战争状态。
7. 清理请求收件箱或处理三个月超时。

不同国家 pulse 次序不是外交真相来源。首次加载还没初始化疲劳的国家暂时不是候选；下次候选重试可加入。UI缓存可能有一个月的滞后。

## 和平 scope

战争目标文档规定 `root` 为 holder，`scope:target_country`、`scope:target_state` 为目标。本 Mod 不允许替其他国家添加目标，`on_enforced` 在绑定地区执行 `fia_begin_accord`。

`possible`：新升级的实时门槛。

`valid`：地区仍属于原目标、持有者仍绑定原地区和原国家。限时授权、政策、人口占比、疲劳不得加入此块。

和平执行幂等；重复执行已有保障不会重置计时。地区易主不会把旧保障带给新所有者。`fia_clear_mission` 仅清理仍指回本保护国的收件箱/地区链接，避免误清理另一场危机。

## 兼容边界

没有新增游戏可执行代码、外部联网依赖或原版文件全量覆盖。Python仅用于生成、检查与打包，不参与游戏运行。存在 `kind = custom` 和动态 religion/state scope 等需实机确认的接口；详见 COMPATIBILITY。
