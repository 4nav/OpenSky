"""
Diagnose why one item's fair_price/true_value looks wrong.
Run with: python3 diagnose_item.py <ITEM_ID>
"""

import sys
import json

from database import get_db_connection
from gemstone import load_gemstone_slot_costs
from reforges import load_reforge_stones, build_reforge_name_lookup
from rarity import load_item_rarities, get_effective_rarity
from essence import load_essence_costs
from quant import (
    get_item_stats, _get_price_rows, _base_prices_rows, get_daily_volume,
    get_enchant_cost_cap, calc_total_modifier_cost, SEVEN_DAYS_MS,
)


def main():
    if len(sys.argv) < 2:
        print("usage: python3 diagnose_item.py <ITEM_ID>")
        return
    item_id = sys.argv[1]

    conn = get_db_connection()
    bazaar_prices = {
        pid: {"instabuy": ib, "instasell": ise, "buy_volume": bv, "sell_volume": sv}
        for pid, ib, ise, bv, sv in conn.execute(
            "SELECT product_id, instabuy, instasell, buy_volume, sell_volume FROM bazaar_prices"
        ).fetchall()
    }
    gemstone_costs = load_gemstone_slot_costs()
    reforge_stones = load_reforge_stones()
    reforge_name_lookup = build_reforge_name_lookup(reforge_stones)
    item_rarities = load_item_rarities()
    essence_costs = load_essence_costs()

    print(f"=== {item_id} ===\n")

    # 1. Raw historical sales in the 7-day VWAP window, before any stripping
    rows = _get_price_rows(conn, item_id)
    print(f"raw sales in 7-day window: {len(rows)}")
    if rows:
        raw_unit_prices = [price / max(qty, 1) for price, qty, *_ in rows]
        print(f"raw unit price range: {min(raw_unit_prices):,.0f} - {max(raw_unit_prices):,.0f}")
        print(f"raw unit price average: {sum(raw_unit_prices)/len(raw_unit_prices):,.0f}")
        # flag any single sale that's wildly out of line with the rest - possible data error
        sorted_prices = sorted(raw_unit_prices)
        median_raw = sorted_prices[len(sorted_prices)//2]
        outliers = [p for p in raw_unit_prices if p > median_raw * 5 or (median_raw > 0 and p < median_raw / 5)]
        if outliers:
            print(f"!! POSSIBLE OUTLIER SALES (>5x or <1/5x the raw median of {median_raw:,.0f}): {sorted(outliers)}")
    print()

    # 2. What get_item_stats actually returns
    stats = get_item_stats(conn, item_id, bazaar_prices, gemstone_costs, reforge_stones,
                            reforge_name_lookup, item_rarities, essence_costs)
    print("get_item_stats result:", stats)
    print()

    # 3. Per-row modifier cost breakdown - same rows _base_prices_rows would strip
    daily_vol = get_daily_volume(conn, item_id)
    cap = get_enchant_cost_cap(conn, item_id)
    print(f"daily_vol: {daily_vol:.2f} | enchant_cap: {cap}\n")

    print("per-sale breakdown (raw price -> stripped modifiers -> base price):")
    breakdown_rows = []
    for price, qty, enchants_json, hpb_count, rarity_upgrades, gemstones_json, reforge_name, star_count in rows[:50]:
        qty = max(qty, 1)
        unit_price = price / qty
        modifier_cost = calc_total_modifier_cost(item_id, bazaar_prices, daily_vol, cap, gemstone_costs,
                                                   reforge_stones, reforge_name_lookup, item_rarities, essence_costs,
                                                   enchants_json, hpb_count, rarity_upgrades, gemstones_json,
                                                   reforge_name, star_count)
        rarity = get_effective_rarity(item_id, rarity_upgrades, item_rarities)
        base = unit_price - modifier_cost
        breakdown_rows.append({"unit_price": unit_price, "modifier_cost": modifier_cost, "base": base,
                                "enchants_json": enchants_json, "gemstones_json": gemstones_json,
                                "reforge_name": reforge_name, "rarity": rarity, "star_count": star_count,
                                "hpb_count": hpb_count, "rarity_upgrades": rarity_upgrades})
        print(f"  unit_price={unit_price:>14,.0f} | modifier_cost={modifier_cost:>14,.0f} | base={base:>14,.0f} "
              f"| reforge='{reforge_name}' | rarity={rarity} | stars={star_count} | hpb={hpb_count} | recomb={rarity_upgrades} | gems={gemstones_json}")
        print(f"    enchants: {enchants_json}")
        if modifier_cost > unit_price * 2:
            print(f"    !! modifier_cost is more than 2x the raw unit_price - likely the source of inflation")

    # Directly compare a low-base and high-base row among recombed (rarity_upgrades=1) sales -
    # if their enchant lists differ meaningfully, that's the smoking gun for a missing/mispriced enchant.
    recombed = [r for r in breakdown_rows if r["rarity_upgrades"] == 1 and (not r["gemstones_json"] or r["gemstones_json"] == "{}")]
    if len(recombed) >= 2:
        recombed_sorted = sorted(recombed, key=lambda r: r["base"])
        lowest = recombed_sorted[0]
        highest = recombed_sorted[-1]
        print("\n=== direct comparison: lowest-base vs highest-base recombed, no-gem sale ===")
        print(f"LOW  base={lowest['base']:,.0f} enchants={lowest['enchants_json']}")
        print(f"HIGH base={highest['base']:,.0f} enchants={highest['enchants_json']}")
        try:
            low_names = {e["type"] for e in json.loads(lowest["enchants_json"])} if lowest["enchants_json"] else set()
            high_names = {e["type"] for e in json.loads(highest["enchants_json"])} if highest["enchants_json"] else set()
            print(f"enchants only in HIGH: {high_names - low_names}")
            print(f"enchants only in LOW: {low_names - high_names}")
        except Exception as e:
            print(f"(couldn't diff enchant sets: {e})")

    conn.close()


if __name__ == "__main__":
    main()