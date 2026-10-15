#!/usr/bin/env python3
"""1024 大厨 · 热量-价格双约束背包优化器。

输入(stdin JSON):
{
  "kcal_cap": 1024,          # 热量上限，默认 1024
  "budget": 40,              # 预算(元)，缺省 = 不限
  "max_qty": 3,              # 单品数量上限，默认 3
  "items": [                 # 候选商品，price 单位=元，kcal 取整数
    {"code": "P1", "name": "板烧鸡腿堡", "price": 26.0, "kcal": 430, "category": "主食"}
  ]
}

输出(JSON): feasible=true 时 combo 为最优组合;
feasible=false 时给出放宽热量上限后的 fallback 供降级展示。

打分: score = "饱腹欲望分"。显式传 score 则完全采用;
否则按 category 内置系数计算 —— 主食 ×1.3、饮品 ×0.9、甜品/小食 ×0.6、其他 ×1.0，
免得优化器交出一桌「3 份甜筒 + 2 杯可乐」的甜品自助。"""

import json
import sys

NO_CHOICE = -1
CATEGORY_MULTIPLIER = {"主食": 1.3, "饮品": 0.9, "甜品": 0.6, "小食": 0.6}
DEFAULT_MULTIPLIER = 1.0


def load_input():
    raw = json.load(sys.stdin)
    items = raw.get("items") or []
    if not items:
        raise SystemExit("items 为空: 需要至少 1 个候选商品")
    for i, it in enumerate(items):
        if "kcal" not in it or "price" not in it:
            raise SystemExit(f"items[{i}] 缺少 kcal 或 price 字段: {it.get('name', '?')}")
        if it["kcal"] < 0 or it["price"] < 0:
            raise SystemExit(f"items[{i}] 的 kcal/price 不能为负")
    return raw, items


def score_of(item):
    if "score" in item:
        return float(item["score"])
    return int(item["kcal"]) * CATEGORY_MULTIPLIER.get(item.get("category"), DEFAULT_MULTIPLIER)


def expand(items, kcal_cap, budget_cents, max_qty):
    """把可复购商品展开成 0/1 实例: 单份装不下的直接淘汰, 减少无效实例。"""
    instances = []
    for item in items:
        kcal = int(item["kcal"])
        price = round(float(item["price"]) * 100)
        score = score_of(item)
        if kcal > kcal_cap or price > budget_cents:
            continue
        for _ in range(max(1, int(max_qty))):
            instances.append({"item": item, "kcal": kcal, "price": price, "score": score})
    return instances


def knapsack(instances, kcal_cap, budget_cents):
    """以热量为维度的 0/1 背包: dp[k] = (最高分, 该分数下的最低价)。
    分数相同取更低价, 保证热量打满时优先省预算。"""
    dp = [None] * (kcal_cap + 1)
    dp[0] = (0.0, 0)
    parents = []
    for inst in instances:
        kc, pr, sc = inst["kcal"], inst["price"], inst["score"]
        prev = dp[:]
        layer = [NO_CHOICE] * (kcal_cap + 1)
        for k in range(kcal_cap, kc - 1, -1):
            base = prev[k - kc]
            if base is None:
                continue
            cand = (base[0] + sc, base[1] + pr)
            cur = dp[k]
            if cur is None or cand[0] > cur[0] + 1e-9 or (abs(cand[0] - cur[0]) <= 1e-9 and cand[1] < cur[1]):
                dp[k] = cand
                layer[k] = len(parents)
        parents.append(layer)
    feasible = [(k, dp[k]) for k in range(kcal_cap + 1) if dp[k] and dp[k][1] <= budget_cents]
    if not feasible:
        return None, parents, instances
    best_k, _ = max(feasible, key=lambda kv: (kv[1][0], -kv[0]))
    return best_k, parents, instances


def reconstruct(k, parents, instances):
    """从后往前回溯选中了哪些实例。"""
    chosen = []
    for i in range(len(parents) - 1, -1, -1):
        if parents[i][k] != NO_CHOICE:
            chosen.append(instances[i])
            k -= instances[i]["kcal"]
    chosen.reverse()
    return chosen


def aggregate(chosen):
    combo, seen = [], {}
    for inst in chosen:
        seen.setdefault(inst["item"]["code"], {"item": inst["item"], "qty": 0})
        seen[inst["item"]["code"]]["qty"] += 1
    for entry in seen.values():
        it, qty = entry["item"], entry["qty"]
        combo.append({
            "code": it["code"], "name": it["name"], "qty": qty,
            "category": it.get("category", "其他"),
            "kcal": int(it["kcal"]) * qty, "price": round(float(it["price"]) * qty, 2),
        })
    return combo


def summarize(combo, items, kcal_cap, budget):
    kcal = sum(c["kcal"] for c in combo)
    price = round(sum(c["price"] for c in combo), 2)
    staples = [it for it in items if it.get("category") == "主食"]
    warnings = []
    if staples and not any(c["category"] == "主食" for c in combo):
        warnings.append("组合未包含主食类商品，建议调高预算或手动补一个堡/卷")
    return {
        "kcal": kcal, "kcal_cap": kcal_cap,
        "kcal_left": kcal_cap - kcal,
        "price": price, "budget": budget, "budget_left": round(budget - price, 2),
        "warnings": warnings, "combo": combo,
    }


def main():
    raw, items = load_input()
    kcal_cap = int(raw.get("kcal_cap", 1024))
    budget = raw.get("budget") if raw.get("budget") is not None else float("inf")
    budget_cents = round(budget * 100) if budget != float("inf") else 2**63 - 1
    max_qty = int(raw.get("max_qty", 3))

    best_k, parents, instances = knapsack(expand(items, kcal_cap, budget_cents, max_qty), kcal_cap, budget_cents)
    if best_k is None:
        relaxed_cap = max(kcal_cap * 4, max((int(it["kcal"]) for it in items), default=0) * max_qty)
        alt_k, alt_parents, alt_inst = knapsack(expand(items, relaxed_cap, budget_cents, max_qty), relaxed_cap, budget_cents)
        if alt_k is None:
            print(json.dumps({"feasible": False, "reason": "预算内无任何可行组合"}, ensure_ascii=False))
            return
        print(json.dumps({"feasible": False, "reason": "预算内凑不满热量上限, 已放宽热量约束",
                          "fallback": summarize(aggregate(reconstruct(alt_k, alt_parents, alt_inst)), items, kcal_cap, budget)},
                         ensure_ascii=False))
        return

    result = summarize(aggregate(reconstruct(best_k, parents, instances)), items, kcal_cap, budget)
    result["feasible"] = True
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()