from quant import get_item_stats, calc_total_modifier_cost, get_enchant_cost_cap

def find_flips(conn, bazaar_prices, gemstone_costs, reforge_stones, reforge_name_lookup, 
               item_rarities, essence_costs, min_margin_pct = 0.10, 
min_profit_coins = 100_000):
    """
    Scans the current listings to see if we have a flip - A listing qualifies if EITHER threshold is met. The reason im not weighting by 
    confidence is cuz i want that to be a feature for the user. Returns a list of dicts, sorted by profit descending.
    """
    listings = conn.execute("""
        SELECT uuid, item_id, price, enchantments, hot_potato_count, rarity_upgrades, 
            gemstones, reforge, dungeon_item_level
        FROM item_listings 
        WHERE bin = 1
    """).fetchall()

    stats_cache = {}
    cap_cache = {}
    flips = []

    for uuid, item_id, price, enchants_json, hpb_count, rarity_upgrades, gemstones_json, reforge_name, star_count in listings:
        if item_id not in stats_cache:
            stats_cache[item_id] = get_item_stats(conn, item_id, bazaar_prices, gemstone_costs, reforge_stones, 
                                                  reforge_name_lookup, item_rarities, essence_costs)

        stats = stats_cache[item_id]

        if stats is None:
            continue

        if item_id not in cap_cache:
            cap_cache[item_id] = get_enchant_cost_cap(conn, item_id)

        cap = cap_cache[item_id]

        modifier_cost = calc_total_modifier_cost(item_id, bazaar_prices, stats["daily_volume"], cap,
                                                   gemstone_costs, reforge_stones, reforge_name_lookup,
                                                   item_rarities, essence_costs,
                                                   enchants_json, hpb_count, rarity_upgrades,
                                                   gemstones_json, reforge_name, star_count)
        
        true_value = stats["fair_price"] + modifier_cost

        profit = true_value - price
        if profit <= 0:
            continue

        margin_pct = profit/ true_value if true_value > 0 else 0

        if margin_pct >= min_margin_pct or profit >= min_profit_coins:
            flips.append({
                "uuid": uuid,
                "item_id": item_id,
                "listing_price": price,
                "true_value": true_value,
                "profit": profit,
                "margin_pct": margin_pct,
                "sample_size": stats["sample_size"],
                "volume_tier": stats["volume_tier"],
            })

    flips.sort(key=lambda f: f["profit"], reverse=True)
    return flips