import json
from bazaar import get_modifier_cost

def load_essence_costs(path = "static_data/essencecosts.json"):
    """Static item id -> essence cost lookup"""
    with open(path, "r") as f:
        return json.load(f)

def calc_essence_cost(item_id, star_count, bazaar_prices, essence_costs):
    entry = essence_costs.get(item_id)
    if entry is None or star_count <=0:
        return 0

    essence_type = entry["type"]
    total = 0

    """ Prefix sums on essence costs for each star level, since the cost to upgrade to star N includes all previous stars. """
    for star in range(1, star_count + 1):
        star_key = str(star)
        total += get_modifier_cost(bazaar_prices, f"ESSENCE_{essence_type.upper()}", entry["costs"].get(star_key, 0))
        for material_entry in entry.get("items", {}).get(star_key, []):
            product_id, count = material_entry.rsplit(":", 1)
            count = int(count)

            if(product_id == "SKYBLOCK_COIN"):
                total += count
            else:
                total += get_modifier_cost(bazaar_prices, product_id, count)
    return total