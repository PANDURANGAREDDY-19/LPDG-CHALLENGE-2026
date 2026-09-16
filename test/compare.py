from __future__ import annotations

import argparse
import pathlib

import numpy as np
import pandas as pd


def compare(path_a: pathlib.Path, path_b: pathlib.Path) -> None:
    a = pd.read_csv(path_a)
    b = pd.read_csv(path_b)

    weeks = sorted(set(a["week_start"]) | set(b["week_start"]))

    # ── Weekly overlap table ──────────────────────────────────────────────────
    print(f"\n{'='*65}")
    print(f"  A = {path_a.name}")
    print(f"  B = {path_b.name}")
    print(f"{'='*65}")
    print(f"\n{'Week':<14} {'Both':>6} {'Only A':>8} {'Only B':>8} {'Overlap%':>10} {'Rank-Corr':>10}")
    print("-" * 60)

    weekly_rows = []
    for week in weeks:
        wa = a[a["week_start"] == week].set_index("gateway_id")
        wb = b[b["week_start"] == week].set_index("gateway_id")
        set_a = set(wa.index)
        set_b = set(wb.index)
        overlap = set_a & set_b
        union = set_a | set_b

        # Rank correlation on common gateways
        if len(overlap) >= 2:
            ranks_a = wa.loc[list(overlap), "rank"].values.astype(float)
            ranks_b = wb.loc[list(overlap), "rank"].values.astype(float)
            rank_corr = float(np.corrcoef(ranks_a, ranks_b)[0, 1])
        else:
            rank_corr = float("nan")

        overlap_pct = round(100 * len(overlap) / max(len(union), 1), 1)
        weekly_rows.append({
            "week": week,
            "both": len(overlap),
            "only_a": len(set_a - set_b),
            "only_b": len(set_b - set_a),
            "overlap_pct": overlap_pct,
            "rank_corr": rank_corr,
        })
        corr_str = f"{rank_corr:>9.3f}" if not np.isnan(rank_corr) else "       N/A"
        print(f"{week:<14} {len(overlap):>6} {len(set_a - set_b):>8} {len(set_b - set_a):>8} {overlap_pct:>9}% {corr_str}")

    # ── Overall summary ───────────────────────────────────────────────────────
    all_a = set(a["gateway_id"])
    all_b = set(b["gateway_id"])
    total_overlap = all_a & all_b
    total_union = all_a | all_b
    total_pct = round(100 * len(total_overlap) / max(len(total_union), 1), 1)

    print("-" * 60)
    print(f"{'TOTAL (unique)':<14} {len(total_overlap):>6} {len(all_a - all_b):>8} {len(all_b - all_a):>8} {total_pct:>9}%")

    # ── Consistently agreed gateways (appear in both every week they're picked) ──
    merged = a.merge(b, on=["week_start", "gateway_id"], suffixes=("_a", "_b"))
    if not merged.empty:
        consistent = (
            merged.groupby("gateway_id")
            .size()
            .rename("weeks_agreed")
            .sort_values(ascending=False)
            .reset_index()
        )
        print(f"\nGateways both models agree on (all weeks combined):")
        print(f"{'Gateway ID':<25} {'Weeks Agreed':>14}")
        print("-" * 42)
        for _, row in consistent.iterrows():
            print(f"{row.gateway_id:<25} {int(row.weeks_agreed):>14}")
    else:
        print("\nNo gateways agreed upon across any week.")

    # ── Repeated gateways per file ─────────────────────────────────────────
    for label, df in [(path_a.name, a), (path_b.name, b)]:
        freq = (
            df.groupby("gateway_id")["week_start"]
            .count()
            .rename("weeks_flagged")
            .sort_values(ascending=False)
            .reset_index()
        )
        repeated = freq[freq["weeks_flagged"] > 1]
        once = freq[freq["weeks_flagged"] == 1]
        print(f"\nGateway frequency in {label}:")
        print(f"  Total unique gateways : {len(freq)}")
        print(f"  Flagged in >1 week    : {len(repeated)}")
        print(f"  Flagged in 1 week only: {len(once)}")
        print(f"\n  {'Gateway ID':<25} {'Weeks Flagged':>14}")
        print("  " + "-" * 42)
        for _, row in freq.iterrows():
            marker = " *" if row.weeks_flagged > 1 else ""
            print(f"  {row.gateway_id:<25} {int(row.weeks_flagged):>14}{marker}")

    # ── Score distribution comparison ────────────────────────────────────────
    print(f"\nScore distribution:")
    print(f"{'':20} {'A':>12} {'B':>12}")
    print("-" * 46)
    for stat, va, vb in [
        ("mean",  a["score"].mean(),  b["score"].mean()),
        ("std",   a["score"].std(),   b["score"].std()),
        ("min",   a["score"].min(),   b["score"].min()),
        ("max",   a["score"].max(),   b["score"].max()),
    ]:
        print(f"  {stat:<18} {va:>12.4f} {vb:>12.4f}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Compare two prediction CSVs.")
    parser.add_argument("a", type=pathlib.Path, help="First predictions CSV (baseline)")
    parser.add_argument("b", type=pathlib.Path, help="Second predictions CSV (model)")
    args = parser.parse_args(argv)
    compare(args.a, args.b)


if __name__ == "__main__":
    main()
