# Fund Decision Framework（基金决策方法论框架）

一套**只教方法、不给结论**的基金分析框架。它回答"怎么算、怎么核、怎么推理、信号到没到"，**绝不回答"买哪只基金、买多少钱"**。

## 为什么这样设计

市面上大多数开源基金工具止步于数据查询，而真正做"荐基推荐"的工具在国内属于需要牌照的投顾业务。本框架刻意停在结论之前：把可复用、可公开、可复核的**计算方法与推理结构**沉淀下来，最终决策权与风险完全留给使用者。

## 四个模块

| 模块 | 回答的问题 | 文档 | 计算工具 |
|---|---|---|---|
| 同类排行 | 怎么算排名才可比 | `references/ranking.md` | `calc.py rank` |
| 费率核验 | 费率/锁定/摩擦怎么核 | `references/fee-audit.md` | `calc.py fee` |
| 推理链 | 这个决定怎么论证 | `references/reasoning-chain.md` | — |
| 规则闸 | 信号到没到、能不能动 | `references/signal-gates.md` | `calc.py gate` |

## 设计原则

- **无数据、无凭证**：仓库不含任何基金数据、API key、账号或真实持仓。数据由使用者自行接入并核对。
- **同池才可比**：排名必须绑定数据源 / 分类池 / 池大小 / 日期；跨平台只比数值不比名次。
- **反证不可省**：推理链必须同时写正向理由与反证/风险。
- **场外纪律**：15:00 净值截止；收盘核的信号只能用于下一交易日决策。

## 快速开始

```bash
# 同类排名（数据文件为使用者自备的 JSON 数组）
python scripts/calc.py rank --data funds.json --metric m3 --pool-size 1000 --source <数据源> --pool <分类池>

# 赎回费与摩擦核算
python scripts/calc.py fee --amount 100000 --holding-days 20 --tiers tiers.json

# 信号闸判定
python scripts/calc.py gate --turnover 1.55 --breadth-today 0.55 --consecutive-days 2 --limit-up 150 --limit-down 30
```

各子命令 `--help` 有完整参数说明。脚本仅依赖 Python 标准库。

## 安装为 WorkBuddy skill

将整个目录放到 `~/.workbuddy/skills/fund-decision-framework/`，或使用打包好的 zip 导入。

## 免责声明

本内容仅为方法论与数据整理工具，**不构成任何投资建议或买卖推荐**。基金有风险，投资需谨慎。所有数值须由使用者自行核实；任何投资决策及其后果由使用者自行承担。作者不对使用本工具造成的任何损失负责。
