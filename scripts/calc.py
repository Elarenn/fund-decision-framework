#!/usr/bin/env python3
"""
纯逻辑计算器：基金决策方法论的三个确定性计算。

无第三方依赖、无网络请求、无内置基金数据/凭证。
所有输入由使用者提供，所有输出为计算方法结果，不构成投资建议。

子命令：
  rank  同类排名百分位（同池、按指标降序、收益与回撤并列）
  fee   赎回费与换仓摩擦成本核算
  gate  入场/卖出信号闸判定

用法示例见各子命令 --help。
"""

import argparse
import json
import sys
from datetime import date


DISCLAIMER = (
    "以上为方法论与数据整理，不构成投资建议；"
    "最终决策与风险由使用者自行承担，数据以自行核实为准。"
)


# ---------------------------------------------------------------------------
# rank: 同类排名
# ---------------------------------------------------------------------------

def compute_rank(data, metric, pool_size, higher_is_better=True):
    """按单一指标在给定池内排名并计算百分位。

    data: [{"code":..., "name":..., "m1":0.1, "m3":0.5, "y1":2.0, "dd":-0.2}, ...]
    metric: 指标键名，如 m1/m3/y1/dd
    pool_size: 分类池总只数（分母），必须 >= 参与排名的样本数
    """
    rows = [r for r in data if isinstance(r.get(metric), (int, float))]
    if not rows:
        raise ValueError("没有可用的指标数据，请检查 --metric 与数据文件。")
    if pool_size < len(rows):
        raise ValueError(
            "池大小 %d 小于样本数 %d；分母不能小于参与排名的数量。"
            % (pool_size, len(rows))
        )

    rows.sort(key=lambda r: r[metric], reverse=higher_is_better)
    result = []
    for rank, row in enumerate(rows, start=1):
        result.append({
            "rank": rank,
            "code": row.get("code", ""),
            "name": row.get("name", ""),
            "value": row[metric],
            "percentile": round(rank / pool_size, 6),
            "percentile_pct": "%.2f%%" % (rank / pool_size * 100),
        })
    return {
        "metric": metric,
        "pool_size": pool_size,
        "direction": "降序(高者靠前)" if higher_is_better else "升序(低者靠前，用于回撤等)",
        "rows": result,
        "note": "跨平台池不可比；排名为过去式，不可线性外推。",
    }


def cmd_rank(args):
    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("数据文件顶层必须是数组。")
    out = compute_rank(data, args.metric, args.pool_size, not args.ascending)
    out["as_of"] = args.as_of or str(date.today())
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n【口径】%s | %s | 池 %d 只 | 截至 %s" % (
        args.source or "未注明数据源", args.pool or "未注明分类池",
        args.pool_size, out["as_of"]))
    print(DISCLAIMER)


# ---------------------------------------------------------------------------
# fee: 赎回费与摩擦
# ---------------------------------------------------------------------------

def redemption_rate(holding_days, tiers):
    """按持有天数匹配赎回费档位。

    tiers: [{"min_days":0, "max_days":7, "rate":0.015}, ...]
    匹配规则：min_days <= holding_days < max_days（max_days 为 None 表示不限）
    """
    for t in tiers:
        lo = t["min_days"]
        hi = t.get("max_days")
        if holding_days >= lo and (hi is None or holding_days < hi):
            return t["rate"]
    raise ValueError("持有 %s 天未匹配到任何赎回费档位，请检查档位表。" % holding_days)


def compute_fee(amount, holding_days, tiers, subscription_rate=0.0,
                transit_days=0, annual_yield=0.0):
    redeem_rate = redemption_rate(holding_days, tiers)
    redeem_fee = amount * redeem_rate
    subscription_fee = amount * subscription_rate
    transit_cost = amount * annual_yield * (transit_days / 365.0)
    total = redeem_fee + subscription_fee + transit_cost
    return {
        "amount": amount,
        "holding_days": holding_days,
        "matched_rate": redeem_rate,
        "redemption_fee": round(redeem_fee, 2),
        "subscription_fee": round(subscription_fee, 2),
        "transit_cost": round(transit_cost, 2),
        "total_friction": round(total, 2),
        "total_friction_pct": "%.4f%%" % (total / amount * 100),
        "note": "场外15:00截止；T+1确认、赎回款T+1/T+2到账；跨公司不能转换。",
    }


DEFAULT_TIERS = [
    {"min_days": 0, "max_days": 7, "rate": 0.015},
    {"min_days": 7, "max_days": 30, "rate": 0.001},
    {"min_days": 30, "max_days": None, "rate": 0.0},
]


def cmd_fee(args):
    tiers = DEFAULT_TIERS
    if args.tiers:
        with open(args.tiers, "r", encoding="utf-8") as f:
            tiers = json.load(f)
    out = compute_fee(
        amount=args.amount,
        holding_days=args.holding_days,
        tiers=tiers,
        subscription_rate=args.subscription_rate,
        transit_days=args.transit_days,
        annual_yield=args.annual_yield,
    )
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if args.tiers is None:
        print("\n注意：使用默认示例档位（<7天1.5%/7-30天0.1%/≥30天0），"
              "实际费率必须按该基金合同或App核对后通过 --tiers 传入。")
    print(DISCLAIMER)


# ---------------------------------------------------------------------------
# gate: 信号闸
# ---------------------------------------------------------------------------

def evaluate_gate(turnover, turnover_min, breadth_today, breadth_min,
                  consecutive_days, limit_up, limit_down, ratio_min):
    checks = []
    turnover_ok = turnover >= turnover_min
    checks.append({
        "signal": "成交额",
        "value": turnover,
        "threshold": turnover_min,
        "pass": turnover_ok,
    })
    breadth_ok = breadth_today > breadth_min
    streak_ok = consecutive_days >= 2
    checks.append({
        "signal": "上涨占比",
        "value": breadth_today,
        "threshold": breadth_min,
        "pass": breadth_ok,
    })
    checks.append({
        "signal": "上涨占比连续2日",
        "days": consecutive_days,
        "pass": streak_ok,
    })
    ratio = (limit_up / limit_down) if limit_down else float("inf")
    ratio_ok = ratio > ratio_min
    checks.append({
        "signal": "涨停/跌停倍数",
        "value": round(ratio, 2) if ratio != float("inf") else "inf",
        "threshold": ratio_min,
        "pass": ratio_ok,
    })
    all_pass = turnover_ok and breadth_ok and streak_ok and ratio_ok
    return {
        "checks": checks,
        "all_pass": all_pass,
        "verdict": "全达标 → 下一交易日可进入决策流程（非买入指令）"
                   if all_pass else "未全达标 → 不进入决策流程",
        "rules": [
            "必须收盘确认，盘中值不算",
            "场外下单：收盘核信号 → 下一交易日15:00前提交",
            "任一失败，连续计数从下一交易日归零重算",
        ],
    }


def default_config():
    return {
        "turnover_min": 1.55,
        "breadth_min": 0.50,
        "consecutive_days": 2,
        "ratio_min": 2.0,
    }


def cmd_gate(args):
    cfg = default_config()
    if args.config:
        with open(args.config, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    out = evaluate_gate(
        turnover=args.turnover,
        turnover_min=cfg["turnover_min"],
        breadth_today=args.breadth_today,
        breadth_min=cfg["breadth_min"],
        consecutive_days=args.consecutive_days,
        limit_up=args.limit_up,
        limit_down=args.limit_down,
        ratio_min=cfg["ratio_min"],
    )
    out["as_of"] = args.as_of or str(date.today())
    out["config"] = cfg
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(DISCLAIMER)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="基金决策方法论计算器（纯逻辑，无网络，无内置数据）")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("rank", help="同类排名百分位")
    r.add_argument("--data", required=True, help="基金数据 JSON 数组文件路径")
    r.add_argument("--metric", required=True, help="指标键名，如 m1/m3/y1/dd")
    r.add_argument("--pool-size", type=int, required=True, help="分类池总只数（分母）")
    r.add_argument("--ascending", action="store_true", help="升序（回撤类低者靠前）")
    r.add_argument("--source", help="数据源名称（写入口径）")
    r.add_argument("--pool", help="分类池名称（写入口径）")
    r.add_argument("--as-of", help="数据截至日期")
    r.set_defaults(func=cmd_rank)

    f = sub.add_parser("fee", help="赎回费与摩擦核算")
    f.add_argument("--amount", type=float, required=True, help="赎回/换仓金额")
    f.add_argument("--holding-days", type=int, required=True, help="持有天数")
    f.add_argument("--tiers", help="赎回费档位 JSON 文件路径（不传则用示例档位）")
    f.add_argument("--subscription-rate", type=float, default=0.0, help="申购费率")
    f.add_argument("--transit-days", type=int, default=0, help="资金在途天数")
    f.add_argument("--annual-yield", type=float, default=0.0, help="年化收益（算在途机会成本）")
    f.set_defaults(func=cmd_fee)

    g = sub.add_parser("gate", help="信号闸判定")
    g.add_argument("--turnover", type=float, required=True, help="当日成交额（万亿）")
    g.add_argument("--breadth-today", type=float, required=True, help="今日上涨占比 0-1")
    g.add_argument("--consecutive-days", type=int, default=1, help="上涨占比连续达标天数")
    g.add_argument("--limit-up", type=int, required=True, help="涨停家数")
    g.add_argument("--limit-down", type=int, required=True, help="跌停家数")
    g.add_argument("--config", help="自定义阈值 JSON 文件路径")
    g.add_argument("--as-of", help="数据截至日期")
    g.set_defaults(func=cmd_gate)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as e:
        print("错误：%s" % e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
