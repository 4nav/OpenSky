import json
from bazaar import get_modifier_cost

BASIC_REFORGE_COSTS = {
    "COMMON": 250, "UNCOMMON": 500, "RARE": 1_000, "EPIC": 2_500, "LEGENDARY": 5_000, "MYTHIC": 10_000, "DIVINE": 10_000, "SPECIAL": 25_000, "VERY_SPECIAL": 50_000,
}

def load_reforge_stones(path = "static_data/reforge_stones.json"):
    with open(path, "r") as f:
        return json.load(f)
    
def build_reforge_name_lookup(reforge_stones):
    return {data["reforgeName"].lower(): internal_name for internal_name, data in reforge_stones.items()}

def calc_reforge_cost(reforge_name, rarity, bazaar_prices, reforge_stones, name_lookup):
    if not reforge_name:
        return 0
    
    name = reforge_name.lower()
    stone_internal_name = name_lookup.get(name)

    if stone_internal_name is not None:
        stone_data = reforge_stones[stone_internal_name]
        application_fee = stone_data.get("reforgeCosts", {}).get(rarity, 0)
        stone_cost = get_modifier_cost(bazaar_prices, stone_internal_name, 1)
        return application_fee + stone_cost
    return BASIC_REFORGE_COSTS.get(rarity, 0)
