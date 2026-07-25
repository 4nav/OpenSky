import json
from bazaar import get_modifier_cost

MASTER_STAR_IDS = {
    6: "FIRST_MASTER_STAR",
    7: "SECOND_MASTER_STAR",
    8: "THIRD_MASTER_STAR",
    9: "FOURTH_MASTER_STAR",
    10: "FIFTH_MASTER_STAR",
}

def load_essence_costs(path = "static_data/essencecosts.json"):
    """Static item id -> essence cost lookup"""
    with open(path, "r") as f:
        return json.load(f)

def calc_essence_cost(item_id, star_count, bazaar_prices, essence_costs):
    entry = essence_costs.get(item_id)
    if star_count <= 0:
        return 0

    total = 0
    essence_max_level = 0

    """ Prefix sums on essence costs for each star level. True Dungeon items only have levels 1-5 here; 
    Crimson items have their own separate star system which goes up to 15, built directly into this same data, so we read each 
    item's actual max level rather than assuming 5. """
    if entry is not None:
        essence_type = entry["type"]
        numeric_keys = [int(k) for k in entry.keys() if k.isdigit()]
        essence_max_level = max(numeric_keys) if numeric_keys else 0
        levels_to_price = min(star_count, essence_max_level)
        for star in range(1, levels_to_price + 1):
            star_key = str(star)
            total += get_modifier_cost(bazaar_prices, f"ESSENCE_{essence_type.upper()}", entry.get(star_key, 0))
            for material_entry in entry.get("items", {}).get(star_key, []):
                product_id, count = material_entry.rsplit(":", 1)
                count = int(count)

                if(product_id == "SKYBLOCK_COIN"):
                    total += count
                else:
                    total += get_modifier_cost(bazaar_prices, product_id, count)

    """ Any level beyond this item's own essence data is a Master Star (FIRST..FIFTH, straight bazaar cost)."""
    for star in range(essence_max_level + 1, star_count + 1):
        star_id = MASTER_STAR_IDS.get(star)
        if star_id:
            total += get_modifier_cost(bazaar_prices, star_id, 1)

    return total