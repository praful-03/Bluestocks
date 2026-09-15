"""
fund_performance_analytics.py
==============================
Day 3 - Fund Performance Analytics for the Bluestock MF Capstone.

This script:
  1. Loads NAV history, performance metrics, and benchmark data from bluestock_mf.db
  2. Computes rolling returns (1M, 3M, 6M, 12M) from raw NAV
  3. Analyses drawdowns (max drawdown, underwater periods)
  4. Compares fund returns vs benchmark indices
  5. Ranks funds on risk-adjusted metrics (Sharpe, Sortino, Alpha)
  6. Generates publication-quality charts saved to reports/charts/
  7. Writes a comprehensive text report -> reports/day3_fund_performance_report.txt
"""

import os
import sqlite3
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "bluestock_mf.db")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
CHARTS_DIR  = os.path.join(REPORTS_DIR, "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

PALETTE = {
    "Large Cap":      "#2196F3",
    "Mid Cap":        "#FF9800",
    "Small Cap":      "#F44336",
    "ELSS":           "#9C27B0",
    "Flexi Cap":      "#00BCD4",
    "Index":          "#607D8B",
    "Index/ETF":      "#78909C",
    "Liquid":         "#4CAF50",
    "Gilt":           "#8BC34A",
    "Short Duration": "#CDDC39",
    "Value":          "#FF5722",
    "Large & Mid Cap":"#3F51B5",
}
DARK_BG   = "#0D1117"
CARD_BG   = "#161B22"
TEXT_COL  = "#C9D1D9"
ACCENT    = "#58A6FF"
GRID_COL  = "#21262D"

plt.rcParams.update({
    "figure.facecolor":  DARK_BG,
    "axes.facecolor":    CARD_BG,
    "axes.edgecolor":    GRID_COL,
    "axes.labelcolor":   TEXT_COL,
    "xtick.color":       TEXT_COL,
    "ytick.color":       TEXT_COL,
    "text.color":        TEXT_COL,
    "grid.color":        GRID_COL,
    "grid.linewidth":    0.5,
    "legend.facecolor":  CARD_BG,
    "legend.edgecolor":  GRID_COL,
    "font.family":       "DejaVu Sans",
    "font.size":         9,
})

SEP = "=" * 72

WINDOWS = {"1M": 21, "3M": 63, "6M": 126, "12M": 252}

BENCH_MAP = {
    "Large Cap":      "NIFTY100",
    "Index":          "NIFTY50",
    "Index/ETF":      "NIFTY50",
    "Flexi Cap":      "NIFTY500",
    "Mid Cap":        "NIFTY_MIDCAP150",
    "Large & Mid Cap":"NIFTY_MIDCAP150",
    "Small Cap":      "NIFTY500",
    "Value":          "NIFTY500",
    "ELSS":           "NIFTY500",
    "Liquid":         "CRISIL_LIQUID",
    "Gilt":           "CRISIL_GILT",
    "Short Duration": "CRISIL_LIQUID",
}


def load_data():
    print(f"\n{SEP}\n  LOADING DATA FROM DATABASE\n{SEP}")
    conn = sqlite3.connect(DB_PATH)
    funds = pd.read_sql("SELECT * FROM dim_fund", conn)
    funds["launch_date"] = pd.to_datetime(funds["launch_date"], errors="coerce")
    nav = pd.read_sql("SELECT amfi_code, nav_date, nav, daily_return FROM fact_nav", conn)
    nav["nav_date"] = pd.to_datetime(nav["nav_date"])
    nav = nav.sort_values(["amfi_code", "nav_date"]).reset_index(drop=True)
    perf = pd.read_sql("SELECT * FROM fact_performance", conn)
    bench = pd.read_sql("SELECT date, index_name, close_value FROM fact_benchmark", conn)
    bench["date"] = pd.to_datetime(bench["date"])
    bench = bench.sort_values(["index_name", "date"]).reset_index(drop=True)
    aum = pd.read_sql("SELECT * FROM fact_aum", conn)
    aum["date"] = pd.to_datetime(aum["date"])
    conn.close()
    print(f"  dim_fund          : {len(funds):,} funds")
    print(f"  fact_nav          : {len(nav):,} rows  |  {nav['amfi_code'].nunique()} schemes")
    print(f"  fact_performance  : {len(perf):,} rows")
    print(f"  fact_benchmark    : {len(bench):,} rows  |  {bench['index_name'].nunique()} indices")
    print(f"  fact_aum          : {len(aum):,} rows")
    return dict(funds=funds, nav=nav, perf=perf, bench=bench, aum=aum)


def compute_rolling_returns(nav):
    print(f"\n{SEP}\n  STEP 1 - ROLLING RETURNS\n{SEP}")
    frames = []
    for code, grp in nav.groupby("amfi_code"):
        grp = grp.sort_values("nav_date").copy()
        for label, w in WINDOWS.items():
            grp[f"roll_{label}"] = grp["nav"].pct_change(periods=w) * 100
        frames.append(grp)
    result = pd.concat(frames, ignore_index=True)
    print(f"  Rolling returns computed for {result['amfi_code'].nunique()} funds")
    return result


def compute_drawdowns(nav):
    print(f"\n{SEP}\n  STEP 2 - DRAWDOWN ANALYSIS\n{SEP}")
    frames = []
    for code, grp in nav.groupby("amfi_code"):
        grp = grp.sort_values("nav_date").copy()
        rolling_max = grp["nav"].cummax()
        grp["drawdown_pct"] = (grp["nav"] - rolling_max) / rolling_max * 100
        frames.append(grp)
    result = pd.concat(frames, ignore_index=True)
    summary = result.groupby("amfi_code").agg(max_dd=("drawdown_pct", "min")).reset_index()
    print(f"  Max drawdown range: {summary['max_dd'].min():.2f}% to {summary['max_dd'].max():.2f}%")
    return result


def compute_benchmark_comparison(funds, nav, bench, perf):
    print(f"\n{SEP}\n  STEP 3 - BENCHMARK COMPARISON\n{SEP}")
    bench_pivot = bench.pivot(index="date", columns="index_name", values="close_value").ffill()
    results = []
    for _, fund_row in funds.iterrows():
        code = fund_row["amfi_code"]
        sub  = fund_row["sub_category"]
        idx  = BENCH_MAP.get(sub)
        if idx not in bench_pivot.columns:
            continue
        fund_nav = nav[nav["amfi_code"] == code].sort_values("nav_date")
        if len(fund_nav) < 252:
            continue
        start = fund_nav["nav_date"].min()
        end   = fund_nav["nav_date"].max()
        bench_series = bench_pivot.loc[
            (bench_pivot.index >= start) & (bench_pivot.index <= end), idx
        ].dropna()
        fund_series = fund_nav.set_index("nav_date")["nav"]
        fund_3y = fund_series.iloc[-1] / fund_series.iloc[-min(len(fund_series), 756)] - 1
        if len(bench_series) >= 756:
            bench_3y = bench_series.iloc[-1] / bench_series.iloc[-756] - 1
        elif len(bench_series) >= 2:
            bench_3y = bench_series.iloc[-1] / bench_series.iloc[0] - 1
        else:
            bench_3y = float("nan")
        perf_row = perf[perf["amfi_code"] == code]
        sharpe  = perf_row["sharpe_ratio"].values[0] if len(perf_row) else float("nan")
        alpha   = perf_row["alpha"].values[0] if len(perf_row) else float("nan")
        ret_1y  = perf_row["return_1yr_pct"].values[0] if len(perf_row) else float("nan")
        ret_3y  = perf_row["return_3yr_pct"].values[0] if len(perf_row) else float("nan")
        results.append({
            "amfi_code":      code,
            "scheme_name":    fund_row["scheme_name"],
            "fund_house":     fund_row["fund_house"],
            "sub_category":   sub,
            "benchmark":      idx,
            "fund_3y_pct":    round(fund_3y * 100, 2),
            "bench_3y_pct":   round(bench_3y * 100, 2) if not (bench_3y != bench_3y) else float("nan"),
            "return_1yr_pct": ret_1y,
            "return_3yr_pct": ret_3y,
            "sharpe_ratio":   sharpe,
            "alpha":          alpha,
        })
    df = pd.DataFrame(results)
    df["excess_return_pct"] = df["fund_3y_pct"] - df["bench_3y_pct"]
    beats_bench = (df["excess_return_pct"] > 0).sum()
    print(f"  {beats_bench}/{len(df)} funds beat their benchmark over 3 years")
    return df


def build_rankings(perf, funds, bench_cmp):
    print(f"\n{SEP}\n  STEP 4 - PERFORMANCE RANKINGS\n{SEP}")
    # Merge with dim_fund to get proper Equity/Debt category (fact_performance.category stores sub_category)
    merged = perf.merge(
        funds[["amfi_code", "category", "sub_category", "risk_category", "plan"]],
        on="amfi_code", how="left", suffixes=("_perf", "")
    )
    # Drop the perf category column and use dim_fund's category
    if "category_perf" in merged.columns:
        merged = merged.drop(columns=["category_perf"])

    top_sharpe = (
        merged[merged["category"] == "Equity"]
        .sort_values("sharpe_ratio", ascending=False)
        .head(10)[["scheme_name", "fund_house", "sub_category",
                   "return_1yr_pct", "return_3yr_pct", "sharpe_ratio",
                   "sortino_ratio", "alpha", "max_drawdown_pct"]]
    )
    top_3y = (
        merged[merged["category"] == "Equity"]
        .sort_values("return_3yr_pct", ascending=False)
        .head(10)[["scheme_name", "fund_house", "sub_category",
                   "return_1yr_pct", "return_3yr_pct", "sharpe_ratio", "alpha"]]
    )
    best_per_cat = (
        merged.sort_values("sharpe_ratio", ascending=False)
        .groupby("sub_category").first().reset_index()
        [["sub_category", "scheme_name", "return_3yr_pct", "sharpe_ratio", "alpha"]]
    )
    cat_avg = (
        merged.groupby("sub_category")
        .agg(avg_1y=("return_1yr_pct", "mean"), avg_3y=("return_3yr_pct", "mean"),
             avg_sharpe=("sharpe_ratio", "mean"), avg_alpha=("alpha", "mean"),
             num_funds=("amfi_code", "count"))
        .reset_index().sort_values("avg_3y", ascending=False)
    )
    for name, df in [("Top 10 by Sharpe (Equity)", top_sharpe),
                     ("Top 10 by 3Y Return (Equity)", top_3y),
                     ("Best per Category", best_per_cat),
                     ("Category Averages", cat_avg)]:
        print(f"\n  -- {name} --")
        print(df.to_string(index=False))
    return dict(top_sharpe=top_sharpe, top_3y=top_3y,
                best_per_cat=best_per_cat, cat_avg=cat_avg, merged=merged)


def _save(fig, name):
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Chart saved: {path}")
    return path


def chart_nav_growth(nav, funds):
    sub_cats_shown = ["Large Cap", "Mid Cap", "Small Cap", "ELSS"]
    fig, axes = plt.subplots(2, 2, figsize=(16, 9), sharex=False)
    fig.suptitle("NAV Growth (Rebased to 100 at Jan 2022)", fontsize=14,
                 color=TEXT_COL, fontweight="bold", y=0.98)
    for ax, sub_cat in zip(axes.flat, sub_cats_shown):
        codes = funds[funds["sub_category"] == sub_cat]["amfi_code"].tolist()
        for code in codes:
            grp = nav[nav["amfi_code"] == code].sort_values("nav_date")
            if grp.empty:
                continue
            rebased = grp["nav"] / grp["nav"].iloc[0] * 100
            label = funds[funds["amfi_code"] == code]["scheme_name"].values[0]
            label = label[:35] + "..." if len(label) > 35 else label
            ax.plot(grp["nav_date"], rebased, linewidth=1.2, alpha=0.85, label=label)
        ax.set_title(sub_cat, color=ACCENT, fontsize=10, fontweight="bold")
        ax.set_ylabel("Indexed Value", fontsize=8)
        ax.axhline(100, color="#555", linewidth=0.6, linestyle="--")
        ax.grid(True, axis="y")
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
        ax.legend(fontsize=6, loc="upper left", framealpha=0.6)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=7)
    fig.tight_layout()
    return _save(fig, "01_nav_growth.png")


def chart_rolling_returns_heatmap(nav_rolling, funds):
    latest = (
        nav_rolling[nav_rolling["roll_12M"].notna()]
        .sort_values("nav_date").groupby("amfi_code").last().reset_index()
        [["amfi_code", "roll_12M"]]
    )
    latest = latest.merge(funds[["amfi_code", "scheme_name", "sub_category"]], on="amfi_code")
    latest = latest.sort_values("roll_12M", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 12))
    fig.suptitle("Latest 12-Month Rolling Return by Fund", fontsize=13,
                 color=TEXT_COL, fontweight="bold")
    colors = ["#F44336" if v < 0 else "#4CAF50" for v in latest["roll_12M"]]
    bars = ax.barh(range(len(latest)), latest["roll_12M"], color=colors, alpha=0.85)
    ax.set_yticks(range(len(latest)))
    labels = [
        f"{row.scheme_name[:32]}..." if len(row.scheme_name) > 32 else row.scheme_name
        for row in latest.itertuples()
    ]
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("12-Month Rolling Return (%)", fontsize=9)
    ax.axvline(0, color=TEXT_COL, linewidth=0.8)
    ax.grid(True, axis="x", alpha=0.4)
    for bar, val in zip(bars, latest["roll_12M"]):
        ax.text(
            val + (0.3 if val >= 0 else -0.3), bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", ha="left" if val >= 0 else "right", fontsize=6.5
        )
    fig.tight_layout()
    return _save(fig, "02_rolling_returns_heatmap.png")


def chart_sharpe_vs_return(perf, funds):
    merged = perf.merge(funds[["amfi_code", "category", "sub_category"]], on="amfi_code", suffixes=("_perf", ""))
    if "category_perf" in merged.columns:
        merged = merged.drop(columns=["category_perf"])
    equity = merged[merged["category"] == "Equity"].dropna(subset=["sharpe_ratio", "return_3yr_pct"])
    fig, ax = plt.subplots(figsize=(11, 7))
    fig.suptitle("Risk-Adjusted Return: Sharpe Ratio vs 3-Year CAGR (Equity Funds)",
                 fontsize=12, color=TEXT_COL, fontweight="bold")
    for sub_cat, grp in equity.groupby("sub_category"):
        color = PALETTE.get(sub_cat, "#AAAAAA")
        ax.scatter(grp["return_3yr_pct"], grp["sharpe_ratio"],
                   color=color, label=sub_cat, s=80, alpha=0.9, zorder=3)
    ax.set_xlabel("3-Year CAGR (%)", fontsize=10)
    ax.set_ylabel("Sharpe Ratio", fontsize=10)
    ax.axhline(1.0, color="#555", linewidth=0.7, linestyle="--")
    ax.axvline(equity["return_3yr_pct"].median(), color="#555", linewidth=0.7, linestyle="--")
    ax.legend(fontsize=8, framealpha=0.7)
    ax.grid(True, alpha=0.3)
    top = equity.nlargest(5, "sharpe_ratio")
    for _, row in top.iterrows():
        label = row["scheme_name"][:25] + "..."
        ax.annotate(label, (row["return_3yr_pct"], row["sharpe_ratio"]),
                    textcoords="offset points", xytext=(6, 4),
                    fontsize=6.5, color=TEXT_COL, alpha=0.9)
    fig.tight_layout()
    return _save(fig, "03_sharpe_vs_return.png")


def chart_drawdown(nav_dd, funds, perf):
    top8_codes = perf.nlargest(8, "aum_crore")["amfi_code"].tolist()
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.suptitle("Drawdown Chart - Top 8 Funds by AUM", fontsize=13, color=TEXT_COL, fontweight="bold")
    colors = plt.cm.tab10.colors
    for i, code in enumerate(top8_codes):
        grp = nav_dd[nav_dd["amfi_code"] == code].sort_values("nav_date")
        label = funds[funds["amfi_code"] == code]["scheme_name"].values[0]
        label = label[:30] + "..." if len(label) > 30 else label
        ax.plot(grp["nav_date"], grp["drawdown_pct"],
                linewidth=1.1, alpha=0.85, label=label, color=colors[i % 10])
    ax.axhline(0, color=TEXT_COL, linewidth=0.7)
    ax.set_ylabel("Drawdown (%)", fontsize=9)
    ax.set_xlabel("Date", fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7, ncol=2, framealpha=0.7, loc="lower left")
    fig.tight_layout()
    return _save(fig, "04_drawdown_chart.png")


def chart_category_returns(cat_avg):
    cats  = cat_avg.sort_values("avg_3y", ascending=True)
    x     = np.arange(len(cats))
    width = 0.38
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle("Average Returns by Fund Sub-Category", fontsize=13, color=TEXT_COL, fontweight="bold")
    b1 = ax.barh(x - width/2, cats["avg_1y"], width, color=ACCENT, alpha=0.85, label="1-Year Return")
    b2 = ax.barh(x + width/2, cats["avg_3y"], width, color="#FF9800", alpha=0.85, label="3-Year CAGR")
    ax.set_yticks(x)
    ax.set_yticklabels(cats["sub_category"], fontsize=9)
    ax.set_xlabel("Average Return (%)", fontsize=9)
    ax.axvline(0, color=TEXT_COL, linewidth=0.7)
    ax.legend(fontsize=9)
    ax.grid(True, axis="x", alpha=0.3)
    for bar in b1:
        v = bar.get_width()
        ax.text(v + 0.2, bar.get_y() + bar.get_height()/2, f"{v:.1f}%", va="center", fontsize=7)
    for bar in b2:
        v = bar.get_width()
        ax.text(v + 0.2, bar.get_y() + bar.get_height()/2, f"{v:.1f}%", va="center", fontsize=7)
    fig.tight_layout()
    return _save(fig, "05_category_returns.png")


def chart_aum_growth(aum):
    pivot = aum.pivot_table(index="date", columns="fund_house",
                            values="aum_crore", aggfunc="sum").ffill()
    fig, ax = plt.subplots(figsize=(13, 6))
    fig.suptitle("AUM Growth by Fund House (Quarterly)", fontsize=13, color=TEXT_COL, fontweight="bold")
    colors = plt.cm.Set3.colors
    pivot.plot.area(ax=ax, alpha=0.75, color=colors[:len(pivot.columns)])
    ax.set_ylabel("AUM (Rs. Crore)", fontsize=9)
    ax.set_xlabel("")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"Rs.{x:,.0f}"))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=8)
    ax.legend(fontsize=7, ncol=2, framealpha=0.7, loc="upper left")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "06_aum_growth.png")


def chart_benchmark_comparison(bench_cmp):
    df = bench_cmp.dropna(subset=["fund_3y_pct", "bench_3y_pct"])
    df = df.sort_values("fund_3y_pct", ascending=False)
    fig, ax = plt.subplots(figsize=(13, 8))
    fig.suptitle("3-Year Return vs Benchmark - Fund-level Comparison",
                 fontsize=13, color=TEXT_COL, fontweight="bold")
    x = np.arange(len(df))
    w = 0.4
    ax.bar(x - w/2, df["fund_3y_pct"].values, w, color=ACCENT, alpha=0.85, label="Fund 3Y Return")
    ax.bar(x + w/2, df["bench_3y_pct"].values, w, color="#FF9800", alpha=0.85, label="Benchmark 3Y Return")
    ax.set_xticks(x)
    labels = [n[:20] + "..." if len(n) > 20 else n for n in df["scheme_name"]]
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=6.5)
    ax.set_ylabel("3-Year Return (%)", fontsize=9)
    ax.axhline(0, color=TEXT_COL, linewidth=0.6)
    ax.legend(fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    return _save(fig, "07_benchmark_comparison.png")


def chart_risk_return_bubble(perf, funds):
    merged = perf.merge(funds[["amfi_code", "category", "sub_category"]], on="amfi_code", suffixes=("_perf", ""))
    if "category_perf" in merged.columns:
        merged = merged.drop(columns=["category_perf"])
    equity = merged[merged["category"] == "Equity"].dropna(
        subset=["std_dev_ann_pct", "return_3yr_pct", "aum_crore"]
    )
    fig, ax = plt.subplots(figsize=(11, 7))
    fig.suptitle("Risk-Return Bubble Chart - Equity Funds (Bubble size = AUM)",
                 fontsize=12, color=TEXT_COL, fontweight="bold")
    for sub_cat, grp in equity.groupby("sub_category"):
        color = PALETTE.get(sub_cat, "#AAAAAA")
        sizes = (grp["aum_crore"] / grp["aum_crore"].max() * 600).clip(lower=40)
        ax.scatter(grp["std_dev_ann_pct"], grp["return_3yr_pct"],
                   s=sizes, color=color, label=sub_cat, alpha=0.75, zorder=3)
    ax.set_xlabel("Annualised Std Dev (%)", fontsize=10)
    ax.set_ylabel("3-Year CAGR (%)", fontsize=10)
    ax.legend(fontsize=8, framealpha=0.7)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return _save(fig, "08_risk_return_bubble.png")


def write_report(rankings, bench_cmp, nav_dd, perf, funds, chart_paths):
    print(f"\n{SEP}\n  WRITING REPORT\n{SEP}")
    report_path = os.path.join(REPORTS_DIR, "day3_fund_performance_report.txt")
    cat_avg     = rankings["cat_avg"]
    top_sharpe  = rankings["top_sharpe"]
    top_3y      = rankings["top_3y"]
    merged      = rankings["merged"]

    lines = [
        "BLUESTOCK MF CAPSTONE - DAY 3 FUND PERFORMANCE ANALYTICS REPORT",
        f"Generated: {datetime.now():%Y-%m-%d %H:%M:%S}",
        "=" * 72,
        "",
        "DATA SUMMARY",
        "-" * 72,
        f"  Total funds analysed     : {len(perf)}",
        f"  Fund categories          : {merged['category'].nunique()}",
        f"  Sub-categories           : {merged['sub_category'].nunique()}",
        f"  NAV data range           : Jan 2022 - May 2026",
        f"  Benchmark indices used   : {bench_cmp['benchmark'].nunique()}",
        "",
        "=" * 72,
        "SECTION 1: CATEGORY PERFORMANCE SUMMARY",
        "=" * 72, "",
    ]
    lines.append(cat_avg.to_string(index=False))

    lines += ["", "=" * 72, "SECTION 2: TOP 10 FUNDS BY SHARPE RATIO (EQUITY)", "=" * 72, ""]
    lines.append(top_sharpe.to_string(index=False))

    lines += ["", "=" * 72, "SECTION 3: TOP 10 FUNDS BY 3-YEAR CAGR (EQUITY)", "=" * 72, ""]
    lines.append(top_3y.to_string(index=False))

    beats = bench_cmp[bench_cmp["excess_return_pct"] > 0].sort_values("excess_return_pct", ascending=False)
    lags  = bench_cmp[bench_cmp["excess_return_pct"] <= 0].sort_values("excess_return_pct", ascending=True)
    lines += [
        "", "=" * 72, "SECTION 4: BENCHMARK COMPARISON", "=" * 72, "",
        f"  Funds beating benchmark  : {len(beats)} / {len(bench_cmp)}",
        f"  Funds lagging benchmark  : {len(lags)} / {len(bench_cmp)}",
        "", "  TOP 5 OUTPERFORMERS (vs benchmark, 3Y):",
    ]
    for _, row in beats.head(5).iterrows():
        lines.append(f"    {row['scheme_name'][:45]:<47}  Fund: {row['fund_3y_pct']:6.2f}%  Bench: {row['bench_3y_pct']:6.2f}%  Excess: +{row['excess_return_pct']:.2f}%")
    lines += ["", "  BIGGEST UNDERPERFORMERS (vs benchmark, 3Y):"]
    for _, row in lags.head(5).iterrows():
        lines.append(f"    {row['scheme_name'][:45]:<47}  Fund: {row['fund_3y_pct']:6.2f}%  Bench: {row['bench_3y_pct']:6.2f}%  Excess: {row['excess_return_pct']:.2f}%")

    dd_summary = (
        nav_dd.groupby("amfi_code").agg(max_dd=("drawdown_pct", "min")).reset_index()
        .merge(funds[["amfi_code", "scheme_name"]], on="amfi_code")
        .sort_values("max_dd", ascending=True)
    )
    lines += ["", "=" * 72, "SECTION 5: DRAWDOWN ANALYSIS", "=" * 72, "", "  WORST MAX DRAWDOWNS (Top 10):"]
    for _, row in dd_summary.head(10).iterrows():
        lines.append(f"    {row['scheme_name'][:50]:<52}  {row['max_dd']:.2f}%")
    lines += ["", "  LEAST DRAWDOWN (Most Resilient, Top 5):"]
    for _, row in dd_summary.tail(5).iterrows():
        lines.append(f"    {row['scheme_name'][:50]:<52}  {row['max_dd']:.2f}%")

    lines += ["", "=" * 72, "SECTION 6: RISK-ADJUSTED METRIC SUMMARY", "=" * 72, ""]
    for cat in ["Equity", "Debt"]:
        sub = merged[merged["category"] == cat]
        lines.append(f"  {cat} Funds (n={len(sub)}):")
        lines.append(f"    Avg Sharpe Ratio   : {sub['sharpe_ratio'].mean():.2f}")
        lines.append(f"    Avg Sortino Ratio  : {sub['sortino_ratio'].mean():.2f}")
        lines.append(f"    Avg Alpha          : {sub['alpha'].mean():.2f}")
        lines.append(f"    Avg Beta           : {sub['beta'].mean():.2f}")
        lines.append(f"    Avg Std Dev (ann)  : {sub['std_dev_ann_pct'].mean():.2f}%")
        lines.append(f"    Avg Max Drawdown   : {sub['max_drawdown_pct'].mean():.2f}%")
        lines.append("")

    lines += ["=" * 72, "CHARTS GENERATED", "=" * 72, ""]
    for p in chart_paths:
        lines.append(f"  . {os.path.basename(p)}")
    lines += ["", "=" * 72, "  END OF REPORT", "=" * 72]

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  Report saved: {report_path}")
    return report_path


# ══════════════════════════════════════════════════════════════════════════════
#  EXPORT — alpha_beta.csv
# ══════════════════════════════════════════════════════════════════════════════

def export_alpha_beta_csv(funds: pd.DataFrame, nav: pd.DataFrame,
                          bench: pd.DataFrame, perf: pd.DataFrame) -> str:
    """
    Build alpha_beta.csv with one row per fund containing:
      - Pre-computed alpha & beta from fact_performance
      - OLS-derived alpha & beta from daily return regression vs benchmark
      - Supporting context: fund_house, sub_category, plan, return_3yr_pct
    Saved to data/processed/alpha_beta.csv
    """
    print(f"\n{SEP}\n  EXPORTING alpha_beta.csv\n{SEP}")
    PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
    os.makedirs(PROC_DIR, exist_ok=True)

    # Build daily benchmark returns (wide)
    bench_ret = (
        bench.sort_values(["index_name", "date"])
        .assign(bench_ret=lambda d: d.groupby("index_name")["close_value"].pct_change())
        .pivot(index="date", columns="index_name", values="bench_ret")
    )

    rows = []
    for _, fund_row in funds.iterrows():
        code    = fund_row["amfi_code"]
        sub_cat = fund_row["sub_category"]
        idx     = BENCH_MAP.get(sub_cat)

        # Pre-computed values from fact_performance
        prow = perf[perf["amfi_code"] == code]
        alpha_precomp = prow["alpha"].values[0]  if len(prow) else float("nan")
        beta_precomp  = prow["beta"].values[0]   if len(prow) else float("nan")
        ret_1y        = prow["return_1yr_pct"].values[0] if len(prow) else float("nan")
        ret_3y        = prow["return_3yr_pct"].values[0] if len(prow) else float("nan")
        sharpe        = prow["sharpe_ratio"].values[0]  if len(prow) else float("nan")
        std_dev       = prow["std_dev_ann_pct"].values[0] if len(prow) else float("nan")

        # OLS regression: fund daily_return ~ benchmark daily_return
        alpha_ols = beta_ols = r_squared = float("nan")
        obs_count = 0
        if idx and idx in bench_ret.columns:
            fund_nav = nav[nav["amfi_code"] == code].sort_values("nav_date").copy()
            fund_ret = fund_nav.set_index("nav_date")["daily_return"]

            # Align on common dates, drop NaN in either series
            combined = pd.concat(
                [fund_ret.rename("fund_ret"), bench_ret[idx].rename("bench_ret")], axis=1
            ).dropna()

            # Keep only true trading days: benchmark must have a meaningful return
            # (weekends / holidays have bench_ret == 0 or NaN from forward-fill gaps)
            combined = combined[combined["bench_ret"] != 0].copy()

            if len(combined) >= 60:   # need at least 60 real trading days
                X = combined["bench_ret"].values
                Y = combined["fund_ret"].values
                # OLS: Y = alpha + beta * X
                X_mat = np.column_stack([np.ones(len(X)), X])
                try:
                    coeffs, _, _, _ = np.linalg.lstsq(X_mat, Y, rcond=None)
                    alpha_ols_raw, beta_ols = coeffs
                    # Annualise alpha (daily intercept -> annual %)
                    alpha_ols = round(alpha_ols_raw * 252 * 100, 4)
                    beta_ols  = round(beta_ols, 4)
                    # R-squared
                    Y_hat  = X_mat @ coeffs
                    ss_res = np.sum((Y - Y_hat) ** 2)
                    ss_tot = np.sum((Y - Y.mean()) ** 2)
                    r_squared = round(1 - ss_res / ss_tot, 4) if ss_tot > 0 else float("nan")
                    obs_count = len(combined)
                except Exception:
                    pass

        rows.append({
            "amfi_code":          code,
            "scheme_name":        fund_row["scheme_name"],
            "fund_house":         fund_row["fund_house"],
            "sub_category":       sub_cat,
            "category":           fund_row["category"],
            "plan":               fund_row["plan"],
            "benchmark_index":    idx if idx else "N/A",
            # Pre-computed (from fact_performance)
            "alpha_precomputed":  alpha_precomp,
            "beta_precomputed":   beta_precomp,
            # OLS derived from daily returns
            "alpha_ols_ann_pct": alpha_ols,
            "beta_ols":           beta_ols,
            "r_squared":          r_squared,
            "ols_obs_count":      obs_count,
            # Supporting metrics
            "return_1yr_pct":     ret_1y,
            "return_3yr_pct":     ret_3y,
            "sharpe_ratio":       sharpe,
            "std_dev_ann_pct":    std_dev,
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(["category", "sub_category", "alpha_precomputed"], ascending=[True, True, False])

    # Add a note about which alpha/beta to use
    df["data_note"] = (
        "alpha_precomputed & beta_precomputed are the authoritative values "
        "computed by dataset creators. alpha_ols / beta_ols are derived from "
        "synthetic NAV daily returns and should be used for methodology reference only."
    )

    out_path = os.path.join(PROC_DIR, "alpha_beta.csv")
    df.to_csv(out_path, index=False)

    # Console summary — focus on the pre-computed (canonical) values
    print(f"  Funds exported            : {len(df)}")
    print(f"  Alpha range (precomputed) : {df['alpha_precomputed'].min():.2f} to {df['alpha_precomputed'].max():.2f}")
    print(f"  Beta range  (precomputed) : {df['beta_precomputed'].min():.3f} to {df['beta_precomputed'].max():.3f}")
    print(f"  CSV saved                 : {out_path}")
    print(f"\n  Top 10 by Alpha (precomputed, descending):")
    print(df.nlargest(10, "alpha_precomputed")[
        ["scheme_name", "sub_category", "plan", "alpha_precomputed",
         "beta_precomputed", "return_3yr_pct", "sharpe_ratio"]
    ].to_string(index=False))
    print(f"\n  Equity vs Debt — avg Beta:")
    for cat in ["Equity", "Debt"]:
        sub = df[df["category"] == cat]
        print(f"    {cat}: avg alpha={sub['alpha_precomputed'].mean():.3f}  "
              f"avg beta={sub['beta_precomputed'].mean():.3f}  n={len(sub)}")
    return out_path



def main():
    print(f"\n{'#'*72}")
    print(f"  BLUESTOCK MF CAPSTONE - DAY 3: FUND PERFORMANCE ANALYTICS")
    print(f"  Run at: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"{'#'*72}")

    data = load_data()
    nav, funds, perf, bench, aum = data["nav"], data["funds"], data["perf"], data["bench"], data["aum"]

    nav_rolling = compute_rolling_returns(nav)
    nav_dd      = compute_drawdowns(nav)
    bench_cmp   = compute_benchmark_comparison(funds, nav, bench, perf)
    rankings    = build_rankings(perf, funds, bench_cmp)

    print(f"\n{SEP}\n  GENERATING CHARTS\n{SEP}")
    chart_paths = []
    chart_paths.append(chart_nav_growth(nav, funds))
    chart_paths.append(chart_rolling_returns_heatmap(nav_rolling, funds))
    chart_paths.append(chart_sharpe_vs_return(perf, funds))
    chart_paths.append(chart_drawdown(nav_dd, funds, perf))
    chart_paths.append(chart_category_returns(rankings["cat_avg"]))
    chart_paths.append(chart_aum_growth(aum))
    chart_paths.append(chart_benchmark_comparison(bench_cmp))
    chart_paths.append(chart_risk_return_bubble(perf, funds))

    write_report(rankings, bench_cmp, nav_dd, perf, funds, chart_paths)
    alpha_beta_path = export_alpha_beta_csv(funds, nav, bench, perf)

    print(f"\n{'#'*72}")
    print(f"  DAY 3 FUND PERFORMANCE ANALYTICS COMPLETE")
    print(f"  Charts      : {len(chart_paths)} -> reports/charts/")
    print(f"  Report      : reports/day3_fund_performance_report.txt")
    print(f"  alpha_beta  : {os.path.relpath(alpha_beta_path, BASE_DIR)}")
    print(f"{'#'*72}\n")


if __name__ == "__main__":
    main()
