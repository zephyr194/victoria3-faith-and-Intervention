# 兼容性与证据状态

| 环境 | 当前证据 | 状态 |
| --- | --- | --- |
| Python 3.11+ 本地工具 | 脚本解析、生成、场景测试、安装包检查 | 可离线验证 |
| Victoria 3 1.13 | 使用1.12起的脚本战争目标结构；未运行1.13本体 | 未验证 |
| Victoria 3 1.14 | 对照公开的1.14脚本用例；未运行1.14本体 | 未验证 |
| Multiplayer / hotjoin | 无实机同步测试 | 未验证 |
| 加入旧档 / 跨补丁存档 | 采用月度初始化，但无存档测试 | 未验证 |
| 中英双语游戏UI | UTF-8 BOM、键完整性已静态检查，未截图验收 | 未验证 |

安装包版本标签只修改 `descriptor.mod` 与 `.metadata/metadata.json` 的版本声明，不会把未验证接口变成已兼容接口。源代码保守声明1.13；1.14使用单独打包标签。

不依赖宗教集团 DLC 功能，不读取宗教集团API；但无DLC环境的启动仍应实测。未覆写原版法律、宗教、人口、利益集团、建筑或军队文件；可能与替换原版pulse、删除/重定义宗教及法律、重写外交的Mod冲突。

需要逐版本确认：

1. `kind = custom` 地区战争目标的列表生成、`possible` scope和`on_enforced` scope。
2. `requires_interest_marker`、`has_interest_marker_in_region`在目标补丁下的可见性/含义；1.14地区利益等级可能影响原版前置检查。
3. 原版 `aggressive_diplomatic_plays_permitted` 与 `diplomatic_play_has_no_relations_blockers` 的可用性。
4. 动态宗教比较及 `religion_percent_state = { target = var:fia_faith ... }`。
5. `any_diplomatic_play` 能否在整个战争阶段持续识别该博弈；即使不能，`has_war_with`/`fia_war_seen`须维持任务直到战争结束。
6. journal的动态本地化、目标地区选择，以及custom目标被退让/谈判接受时的执行。
7. 革命是否继承国家任务变量，以及新国家和地区所有者变化后的清理；不能把静态 scope 测试当作革命实测。

确认后按补丁记录版本、DLC、日志、存档、步骤、截图和结果。发现不兼容时增加小范围版本适配，不用复制整个原版外交文件掩盖差异。
