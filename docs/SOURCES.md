# 脚本依据与版本证据

本实现原创；没有复制第三方Mod的事件、平衡数据、美术或原版全量文件。公开源码只用于核对字段和scope用法。没有取得游戏安装目录或本地引擎生成的docs.log。

## 官方与Wiki

- [Paradox 1.12 patch notes](https://steamcommunity.com/games/529340/announcements/detail/518606895910486062)：明确战争目标开始由脚本定义，指向 `war_goal_types.md`；不构成1.13/1.14兼容证明。
- [War goal modding](https://vic3.paradoxwikis.com/War_goal_modding)：`custom` kind、target/contestion、possible/valid、on_enforced与holder scope。
- [On actions](https://vic3.paradoxwikis.com/On_actions)：向原版on-action附加namespaced child。
- [Event modding](https://vic3.paradoxwikis.com/Event_modding)、[Decision modding](https://vic3.paradoxwikis.com/Decision_modding)、[Journal modding](https://vic3.paradoxwikis.com/Journal_modding)：事件取消、AI权重、决议、日志及BOM格式。
- [Scopes](https://vic3.paradoxwikis.com/Scope)、[Triggers](https://vic3.paradoxwikis.com/Trigger)：religion scope、宗教人口比例、state与country迭代器。

## 可重现查阅材料

- [v3_mod_guide_cn](https://github.com/ConsuloEnoch/v3_mod_guide_cn)：本地查阅其Wiki存档；对应文章中一些标注1.8/1.10/1.12，不能假装全部适用最新版本。
- [Vic3TimelineExtended](https://github.com/jakeOmega/Vic3TimelineExtended)：核对公开1.14用例中的state型战争目标、原生外交博弈、日志动态文本、scope与原版解析数据。该项目的功能和测试结果不自动适用于本Mod。

实际开发查阅的提交SHA在下方记录。未来对照本地游戏时应优先使用目标补丁的 `script_docs` / `DumpDataTypes` 输出及实际error.log，而不是继续依赖历史Wiki。

- Wiki存档提交：`87c5e8cd9003e5c06c3b2d3ada1190b17f25c54c`。
- 公开脚本与引擎文档摘录提交：`245f644a45f9830ada675135cff8af3b38ce2cc6`。其中 `docs/engine/triggers_summary.txt`、`effects_summary.txt`、`modifiers_summary.txt` 用来核对词汇与声明scope；这些是第三方仓库保存的生成资料，不是本次运行游戏得到的证据。

### v0.2接口查阅

2026-10-29通过GitHub读取同一公开项目当前的 `docs/engine/on_actions_summary.txt`、`effects_summary.txt`、`triggers_summary.txt`、`triggers_parsed.txt`。核对了全局月度pulse、state_region的state迭代、country宗教比例、宗教过滤人口效果、save_scope_value_as以及教权派类型/势力比较。没有把全国enemy_occupation误当成城市占领，因此明确使用区域代理与破坏程度。
