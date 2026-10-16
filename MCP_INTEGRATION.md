# MCP 集成文档（MCP_INTEGRATION）

本文说明「麦门 1024 大厨」如何接入麦当劳官方 MCP，以及每一步的工具调用契约。

## 1. 接入配置

将 `mcp-config.example.json` 复制为你的客户端 MCP 配置（ZCode 中为 `.zcode/mcp.json` 或界面内等价配置），替换 `YOUR_MCP_TOKEN`：

- 服务端点：`https://mcp.mcd.cn`（Streamable HTTP 协议，与官方指南 [M-China/mcd-mcp-server](https://github.com/M-China/mcd-mcp-server) 一致）
- 认证方式：`Authorization: Bearer <MCP Token>`；Token 在麦当劳开放平台 [https://open.mcd.cn/mcp](https://open.mcd.cn/mcp) 登录后于控制台申请
- 限频：每个 Token 每分钟最多 600 次请求，超限返回 429 —— 本 skill 的调用链按「一次拉取、多处复用」设计，单次完整流程 API 调用量远低于限频

## 2. 工具调用矩阵

| # | 工具 | 读/写 | 调用时机 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | `query-nearby-stores` | 只读 | 确定门店 | 先 `searchType=1` 查收藏；报 `600050`（收藏为空）时向用户要「城市+关键词」改走 `searchType=2` |
| 2 | `delivery-query-addresses` / `delivery-query-stores` | 只读 | 外送场景 | beType=2，先地址后门店 |
| 3 | `query-meals` | 只读 | 拉菜单 | 记录 `productCode`、名称、挂牌价；后续下单用它 |
| 4 | `list-nutrition-foods` | 只读 | 拉营养表 | 热量、蛋白质等，是「凑 1024」的数据源 |
| 5 | `calculate-price` | 只读 | 实算价格 | 返回单位为**分**，展示 ÷100；是报价唯一可信源 |
| 6 | `available-coupons` / `query-store-coupons` | 只读 | 券建议 | 麦麦省可领券 + 当前门店可用券，挑出组和最省 |
| 7 | `auto-bind-coupons` | **写** | 领券 | 仅当用户明确说「领券/帮我领」时调用 |
| 8 | `create-order` | **写** | 下单 | 必须先经 `calculate-price` 实算并向用户展示明细，拿到明确确认才执行 |
| 9 | `query-order` | 只读 | 售后 | 用户付完款查单/查配送进度 |

刻意不用的工具：`draw-lottery`（涉及积分扣减，本 skill 默认不碰）、`query-party-*` 系列（生日派对等，与点餐场景无关）。

## 3. 数据流水线

```text
确定场景(到店/外送) ──► query-nearby-stores ──► storeCode(+beCode)
        │
        ▼
query-meals ──► 菜单候选 ─┐
list-nutrition-foods ──► 营养表 ┘
        │ 名称对齐(完全一致 > 互相包含; 对不上剔除)
        ▼
scripts/optimize.py  (kcal≤1024 ∧ price≤budget 的双约束背包)
        │
        ▼
calculate-price ──► 实付总价
available-coupons / query-store-coupons ──► 券建议
        │
        ▼
Programmer Meal 报告(含梗) ──► 用户确认 ──► create-order
```

## 4. 匹配与容错

- **营养数据缺失**：菜单商品在营养表中对不上一律剔除，不参与凑单，报告中注明「营养数据未收录」。严禁编造热量数字。
- **业务错误码**：MCP 返回的 `code`/`message`（如 600050、操作过于频繁）原样透传给用户并给出下一步动作，不吞错误。
- **预算不足**：优化器返回 `feasible=false` 时展示 `fallback`（放宽热量上限的组合）并明确标注，不静默替换。

## 5. 写操作护栏（安全设计）

写操作与用户资金/账户资产相关，遵循「指令内确认」原则：

1. `create-order` 前：展示实算明细 + 等待用户明确肯定答复（「下单」「确认」级别）；
2. `auto-bind-coupons` 前：要求用户明确提出领券诉求；
3. 用户犹豫、修改组合的任何时刻，重新回到只读流程，不残留半成品订单意图。