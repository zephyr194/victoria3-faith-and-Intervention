# Faith and Intervention · 信仰与干涉

Victoria 3 宗教战争 Mod。首版 **v0.2.0 / experimental**：国内宗教矛盾、外国保护请求、宗教保障战争、五年履约与违约。

**目标版本：1.13 / 1.14。当前只完成脚本结构检查和离线脚本场景测试，未通过游戏本体加载、战争和存档实测。** 不宣称两个版本已经兼容。版本差异与测试清单见 [COMPATIBILITY](docs/COMPATIBILITY.md) 和 [TESTING](docs/TESTING.md)。

## 玩法

1. 具有国教或国家无神论政策的国家，若地区动乱达到15%，且有足够规模的非国教、低接纳人口，开始积累宗教紧张度。
2. 25：国内事件，选择调解、调查或镇压。50：记录重大事件。70：同教且拥有当地利益的外国可能收到保护请求。
3. 保护国提出五年地方保障要求。对方可以接受或拒绝；拒绝给予一年提出外交博弈的窗口，**不会自动宣战**。
4. 在外交视图选择 **“保障宗教权利 / Protect Religious Rights”**，选择日志对应地区。原版决定博弈升级、参战与和平。
5. 战争目标执行后停止当地镇压并开始60个月保障；保护国持续承担监督成本。履约完成才获得信誉，撤销保障则重新触发危机。

保障是**地方行政安排**，通过地方修正、停止镇压和受保护宗教人口的年度去激进化表示；不改变法律接纳、不改变国教、不转移领土、不立即改宗。宗教自治、强制改宗和传教扩张仍是后续设计。

目前每个国家最多承担一项对外保护承诺；每个地区最多绑定一个保护国。教派须与保护国国教完全相同。首版护教压力复用目标地区紧张度，尚无独立的教权派压力模型。

## v0.2 新增：圣地与宗教外交

- 耶路撒冷区域代理的控制权、礼拜限制和战争破坏危机，关联六个宗教。
- 教宗与其他宗教的国家级权威可呼吁克制、号召护教或认可和解。
- 各国选择抗议、救济、承诺或不介入；按实际结果定向增加对应宗教忠诚派/激进派。
- 五年结算上限、旧事件失效检查，以及“恢复圣地通行”原生外交博弈。

地图使用巴勒斯坦地区人口最多的state作代理，**不是精确的耶路撒冷省份占领检测**。影响力收益、期限、操作与边界见 [HOLY_SITES.md](docs/HOLY_SITES.md)。

## 安装

需要 Python 3.10+（开发工具仅用标准库）。在仓库根目录执行：

```sh
python3 tools/build_content.py
python3 tools/validate.py
python3 -m unittest discover -s tests -v
python3 tools/package.py --game-version 1.13
# 或为 1.14 生成相应版本标签的包；标签不是实机兼容认证
python3 tools/package.py --game-version 1.14
```

解压 `dist/faith-and-intervention-0.2.0-vic3-1.13.zip` 中的 `faith_and_intervention/` 与 `faith_and_intervention.mod` 到：

- Windows：`Documents/Paradox Interactive/Victoria 3/mod/`
- macOS：`~/Documents/Paradox Interactive/Victoria 3/mod/`
- Linux：`~/.local/share/Paradox Interactive/Victoria 3/mod/`

通过启动器添加到独立播放集，首次建议使用新存档并只启用本 Mod。若启动器采用新版本地 Mod 导入，可选择包含 `.metadata/metadata.json` 的 `faith_and_intervention/` 目录。解压后的 `faith_and_intervention_docs/` 是随包说明，不必启用。

Mod 在第一个月度国家 pulse 初始化。国内事项通过事件、日志和决议查看；国外任务通过日志及“审议宗教干涉”决议查看目标。该决议只提供操作说明，实际外交博弈从原版外交视图发起。

## 开发

- [DESIGN.md](DESIGN.md)：完整玩法、数值、首版取舍与扩展路线。
- [docs/IMPLEMENTATION.md](docs/IMPLEMENTATION.md)：scope、变量、运行顺序和清理规则。
- [docs/TESTING.md](docs/TESTING.md)：离线测试边界与实机验收步骤。
- [docs/SOURCES.md](docs/SOURCES.md)：脚本依据及版本证据。
- `mod/`：直接装载的游戏内容；无原版文件全量覆盖。
- `balance.json` / `localization.json` / `holy_sites.json` / `tools/holy_content.py`：平衡、圣地与中英文本源；修改后运行 `tools/build_content.py`。
- `tests/script_vm.py`：执行实际 Clausewitz AST 的有限测试解释器，**不是游戏引擎**。

CI 会检查生成文件是否漂移、验证脚本结构、运行场景测试并生成两个版本标签的安装包。
