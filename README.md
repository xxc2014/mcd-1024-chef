# 麦门 1024 大厨 `mcd-1024-chef`

> 1024 程序员节限定 AI Skill —— 把一顿麦当劳优化到 **≤ 1024 kcal**，配一句决定性的程序员梗。

基于大赛提供的麦当劳官方 MCP：不是查表推荐，而是用**实时菜单 + 官方营养数据 + 热量-价格双约束背包算法**，现场为你合成最优组合。

## 解决什么问题

- 「今天吃什么」选择困难：报告即菜单，combo 直出
- 一顿麦门热量爆表：1024 kcal 硬上限，多少热量剩余、预算剩余一目了然
- 优惠券散落各处：自动比对可领券/门店券，告诉你用哪张最省

## 目标用户

- **加班/晚归的程序员**：把热量当成硬预算，1024 kcal 上限防「越忙越爆食」
- **控卡期的麦门信徒**：吃得过瘾又不脱轨，热量剩余、预算剩余全程透明
- **给团队点下午茶的组长**：把「点什么」变成一道可验证的优化题，不再拍脑袋
- **AI Agent / Skill 开发者**：一份可 fork 的 MCP 工程范例——双约束背包、写操作护栏、官方对齐的接入配置

## 核心特性

| 特性 | 说明 |
| --- | --- |
| 双约束背包 | kcal ≤ 1024 且价格 ≤ 预算的动态规划，秒级出最优解 |
| category 打分 | 主食 ×1.3、饮品 ×0.9、甜品/小食 ×0.6 —— 杜绝「3 份甜筒 + 2 杯可乐」式甜品自助钻空子 |
| 实价兜底 | 展示价一律经 MCP `calculate-price` 实算，菜单挂牌价仅用于初筛 |
| 领券建议 | 自动挑最省的券，只建议不代领 |
| 降级兜底 | 预算凑不满 1024 kcal 时自动放宽热量约束并如实标注 |
| 写操作护栏 | 下单/领券/抽奖必须用户明确确认，agent 自主模式不碰钱 |

## 30 秒 Demo

输入：

> 1024 程序员节，帮我凑个 45 块的麦门套餐，到店取

输出：

```
🍔 你的 Programmer Meal · 上海 XYZ 门店（总热量 960/1024 kcal 🟢）
  · 麦辣鸡腿堡 ×1   540 kcal  ¥25.0（主食担当 🧱）
  · 中可乐 ×2       420 kcal   ¥9.0（快乐水）
💰 合计 ¥43（预算 ¥45，还剩 ¥2）
🎫 暂无适合本单的券：「中薯条买一送一」本单没薯条用不上，留到下次加单
 💬 剩余 64 kcal 编译余量，比这个 sprint 留给测试的时间富余多了。
```

## 快速开始

1. **配 MCP**：复制 `mcp-config.example.json` 到你的客户端 MCP 配置，把 `YOUR_MCP_TOKEN` 换成你的 MCP Token（申请入口 [https://open.mcd.cn/mcp](https://open.mcd.cn/mcp)，官方接入指南：[M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server)）。
2. **装 skill**：把 `.agents/skills/mcd-1024-chef/` 整个目录拷贝到你的项目 `.agents/skills/` 下（ZCode / 兼容客户端均可发现）。
3. **触发**：
   - 「1024 程序员节，帮我凑个 40 块的麦门套餐」
   - 「过程序员节，外卖到家，预算 50，我只要 800 卡」
   - 「今天吃什么 求个 ≤1024 kcal 的麦门组合」

## 目录结构

```text
mcd-1024-chef/
├── README.md                 # 本文件
├── CONTEST_DECLARATION.md    # 参赛声明
├── MCP_INTEGRATION.md        # MCP 集成文档（工具矩阵/流水线/容错）
├── mcp-config.example.json   # MCP 配置示例
└── .agents/skills/mcd-1024-chef/
    ├── SKILL.md              # skill 主流程与护栏
    └── scripts/optimize.py   # 双约束背包优化器（纯 Python 标准库）
```

## 声明

原创性与 AI 辅助开发披露见 [CONTEST_DECLARATION.md](./CONTEST_DECLARATION.md)。