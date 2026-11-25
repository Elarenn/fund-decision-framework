---
name: fund-decision-framework
description: 基金决策方法论框架——只教"怎么算、怎么核、怎么推理、信号是否达标"，绝不输出"买哪只基金、买多少钱"的确定性荐基结论。当用户需要对场外基金做同类排行榜核算、费率与摩擦成本核验、买卖推理链构建、入场/卖出规则闸判断，或希望把这套方法固化为可复用流程时使用。本 skill 不含任何数据源凭证或真实持仓数据，数据由使用者自行接入。This skill should be used when a user asks how to rank funds within one peer group, audit fee/lock-up/friction, build an explicit buy/sell reasoning chain, or check entry/exit signal gates — it deliberately stops before naming a specific fund to buy or an amount to invest.
agent_created: true
---

# Fund Decision Framework

## Overview

Provide a reusable, data-source-agnostic methodology for evaluating open-end (场外) funds. The skill has exactly four capabilities: compute same-peer rankings, audit fees/lock-up/friction, structure an explicit reasoning chain, and check signal gates. It deliberately stops before any buy/sell verdict — it never names "which fund to buy" or "how much to invest."

This is a **methodology package**, not a data feed and not an advisory service. It contains algorithms, checklists, and templates only. All data comes from sources the user connects themselves.

## Hard Boundaries (apply to every response)

- **Never output a definitive "buy code X with amount Y" conclusion.** Output computed values, comparison tables, confidence levels, and the reasoning chain. The final decision always remains with the user.
- **Never bundle credentials, account IDs, API keys, or harvested datasets.** This skill ships no data. Data must be supplied by the user's own connected sources and cited with source + pool size + date.
- **Never promise returns or use promotional wording** ("稳赚/必涨/全仓/稳赚不赔").
- **Never fabricate a fund code.** Any code shown must be traced to a user-supplied or user-verified source; when unverified, say so explicitly.
- **Always end with the disclaimer** in the output template below.

## When to use

Trigger this skill when the request is about *how to decide*, not *what to buy*:

- "同类基金排名怎么算 / 不同平台排名对不上"
- "这只基金费率、锁定期、赎回费怎么核"
- "帮我理一下买/卖/持有的推理逻辑"
- "入场信号到没到 / 三信号怎么看"
- "短债换仓的摩擦成本怎么算"
- "把这个筛选/判断流程固化下来"

Do not trigger for: general market news, price predictions, tax/legal advice, or a direct "tell me which fund to buy" demand — in that case, explain the boundary and offer the framework instead.

## The Four Modules

| Module  | Question it answers | Load                            | Deterministic tool     |
| ------- | ------------------- | ------------------------------- | ---------------------- |
| 1. 同类排行 | "怎么算排名才可比"          | `references/ranking.md`         | `scripts/calc.py rank` |
| 2. 费率核验 | "费率/锁定/摩擦怎么核"       | `references/fee-audit.md`       | `scripts/calc.py fee`  |
| 3. 推理链  | "这个决定怎么论证"          | `references/reasoning-chain.md` | —                      |
| 4. 规则闸  | "信号到没到、能不能动"        | `references/signal-gates.md`    | `scripts/calc.py gate` |

## Workflow

1. Identify which of the four modules the request needs. Load only the corresponding reference file(s) — do not read all four by default.
2. Obtain data **only** from user-supplied or user-connected sources. State the source, its classification pool, and the as-of date before computing any ranking.
3. Run `scripts/calc.py` for deterministic computation where applicable. Never compute rankings or fee tiers by memory when the script can do it.
4. Present results as a **comparison / calculation table**, with source, pool size, and date attached to every number.
5. Apply the reasoning-chain template to show *how* a conclusion would be reached — including counter-evidence and failure conditions. Stop short of the verdict.
6. Append the disclaimer.

## Data source convention

- State the source and its peer-group pool before any percentile ranking; a rank without a denominator is meaningless.
- Cross-platform ranks are **not comparable** (different classification pools, A/C share handling). Compare absolute values and percentiles, never raw ranks from different sources.
- Treat any ranking as a snapshot of the past, not a forecast.

## Output template

```
【口径】数据源 / 分类池 / 池大小 / 截至日期
【计算】<表格：数值 + 百分位 + 摩擦成本>
【推理】现状事实 → 数据证据 → 为何考虑 → 反证/风险 → 摩擦 → 置信度与失效条件
【信号】各闸状态（达标 / 未达标 / 待确认）
【边界】以上为方法论与数据整理，不构成投资建议；最终决策与风险由使用者自行承担，数据以自行核实为准。
```

## Resources

- `references/ranking.md` — same-peer ranking methodology, comparable metrics, pitfall list, required fields.
- `references/fee-audit.md` — subscription/redemption fee tiers, three-layer lock-up verification, credit-risk look-through, friction formula.
- `references/reasoning-chain.md` — six-part reasoning template, sell-gate three questions, sizing principles, Buffett frame with critical analysis.
- `references/signal-gates.md` — entry signal gate, exit gate, session-deadline rule, signal reset rule.
- `scripts/calc.py` — pure-logic calculator for ranking percentile, fee/friction, and signal gates. Standard library only, no network calls, no embedded data.
