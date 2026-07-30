import sys
import json
import sqlite3

from database import get_db_connection
from bazaar import get_modifier_cost
from gemstone import load_gemstone_slot_costs, get_slot_unlock_cost
from reforges import load_reforge_stones, build_reforge_name_lookup, calc_reforge_cost
from rarity import load_item_rarities, get_effective_rarity
from essence import load_essence_costs, calc_essence_cost
from quant import calc_enchant_cost, calc_gemstone_cost, get_enchant_cost_cap, get_daily_volume

def load_bazaar_prices(conn):
    rows = conn.execute("SELECT product_id, instabuy, instasell, buy_volume, sell_volume FROM bazaar_prices").fetchall()

    return {pid: {"instabuy": instabuy, "instasell": instasell, "buy_volume": bv, "sell_volume": sv} 
            for pid, instabuy, instasell, bv, sv in rows}

def fetch_sample_rows(conn, item_id, sample_size):
    if item_id:
        query = """
            SELECT item_id, price, quantity, enchantments, hot_potato_count, rarity_upgrades,
                   gemstones, reforge, dungeon_item_level
            FROM ended_auctions
            WHERE bin = 1 AND item_id = ?
            ORDER BY sold_at DESC
            LIMIT ?
        """
        return conn.execute(query, (item_id, sample_size)).fetchall()

    else:
        #ima bias it to make sure we get more modifier costs involved
        query = """
                SELECT item_id, price, quantity, enchantments, hot_potato_count, rarity_upgrades,
                gemstones, reforge, dungeon_item_level
                FROM ended_auctions
                WHERE bin = 1
                AND (
                    (enchantments != '{}' AND enchantments != '[]' AND enchantments IS NOT NULL)
                    OR hot_potato_count > 0
                    OR (gemstones != '{}' AND gemstones IS NOT NULL)
                    OR (reforge != '' AND reforge IS NOT NULL)
                    OR dungeon_item_level > 0
                )
                ORDER BY sold_at DESC
                LIMIT ?
            """
        return conn.execute(query, (sample_size,)).fetchall()

def inspect_row(conn, row, bazaar_prices, gemstone_costs, reforge_stones, reforge_name_lookup, item_rarities, essence_costs):
    item_id, price, qty, enchants_json, hpb_count, rarity_upgrades, gemstones_json, reforge_name, star_count = row

    qty = max(qty,1)
    unit_price = price/qty

    daily_vol = get_daily_volume(conn, item_id)
    cap  = get_enchant_cost_cap(conn, item_id)

    enchant_cost = calc_enchant_cost(bazaar_prices, item_id, enchants_json, daily_vol, cap)

    hpb_cost = (get_modifier_cost(bazaar_prices, "HOT_POTATO_BOOK", min(hpb_count,10))
                + get_modifier_cost(bazaar_prices, "FUMING_POTATO_BOOK", max(hpb_count-10,0))) 
    recomb_cost = get_modifier_cost(bazaar_prices, "RECOMBOBULATOR_3000", rarity_upgrades)
    gemstone_cost = calc_gemstone_cost(bazaar_prices, gemstones_json, item_id, gemstone_costs)
    rarity = get_effective_rarity(item_id, rarity_upgrades, item_rarities)
    reforge_cost = calc_reforge_cost(reforge_name, rarity, bazaar_prices, reforge_stones, reforge_name_lookup) if rarity else 0 
    essence_cost = calc_essence_cost(item_id, star_count, bazaar_prices, essence_costs)
    total_stripped = enchant_cost + hpb_cost + recomb_cost + gemstone_cost + reforge_cost + essence_cost
    base_price = unit_price - total_stripped

    print(f"--- {item_id} ---")
    print(f"  raw price: {price:,} | qty: {qty} | unit_price: {unit_price:,.0f}")
    print(f"  enchantments: {enchants_json}")
    print(f"  hot_potato_count: {hpb_count} | rarity_upgrades (recomb): {rarity_upgrades} | effective_rarity: {rarity}")
    print(f"  gemstones: {gemstones_json}")
    print(f"  reforge: '{reforge_name}' | dungeon_item_level: {star_count}")
    print(f"  -> enchant_cost:   {enchant_cost:,.0f}")
    print(f"  -> hpb_cost:       {hpb_cost:,.0f}")
    print(f"  -> recomb_cost:    {recomb_cost:,.0f}")
    print(f"  -> gemstone_cost:  {gemstone_cost:,.0f}")
    print(f"  -> reforge_cost:   {reforge_cost:,.0f}")
    print(f"  -> essence_cost:   {essence_cost:,.0f}")
    print(f"  TOTAL STRIPPED:    {total_stripped:,.0f}")
    print(f"  BASE PRICE:        {base_price:,.0f}")
    if base_price <= 0:
        print(f"  !! WARNING: base_price <= 0 - stripped MORE than the item sold for, look into this")
    print()

def main():
    item_id = sys.argv[1] if len(sys.argv) > 1 else None
    sample_size = int(sys.argv[2]) if len(sys.argv) > 2 else None

    conn = get_db_connection()

    bazaar_prices = load_bazaar_prices(conn)

    print(f"loaded {len(bazaar_prices)} bazaar prices")

    if not bazaar_prices:
        print("No bz prices found")

    gemstone_costs = load_gemstone_slot_costs()
    reforge_stones = load_reforge_stones()
    reforge_name_lookup = build_reforge_name_lookup(reforge_stones)
    item_rarities = load_item_rarities()
    essence_costs = load_essence_costs()

    rows = fetch_sample_rows(conn, item_id, sample_size)

    print(f"inspecting {len(rows)} sold auctions" + (f" for {item_id}" if item_id else " (sampled across items with modifiers)"))
    print()

    if not rows:
        print("No rows found")
        return

    for row in rows:
        inspect_row(conn, row, bazaar_prices, gemstone_costs, reforge_stones, reforge_name_lookup, item_rarities, essence_costs)

        conn.close()

if __name__ == "__main__":
     main()