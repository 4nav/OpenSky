import json
from bazaar import get_modifier_cost

def load_gemstone_slot_costs(path = "gemstonecosts.json"):
    """Static per-item slot unlock recipes, sourced from NEU repo's constants/gemstonecosts.json"""
    with open(path, "r") as f:
        return json.load(f)

def parse_slot_cost(entries):
    """
    entries looks like ["SKYBLOCK_COIN:250000", "FLAWLESS_JASPER_GEM:1", ...].
    Returns {"coins": int, "gems": [(product_id, count), ...]}.
    """
    coins = 0
    gems = []
    for entry in entries:
        product_id, count = entry.rsplit(":",1)
        count = int(count)
        if product_id == "SKYBLOCK_COIN":
            coins += count
        else:
            gems.append((product_id, count))
    return {"coins": coins, "gems": gems}

def get_unlock_slot_cost(item_id, slot_key, gemstone_costs, bazaar_prices):
    """
    Total coin cost to unlock one gemstone slot on an item. Should return 0 if its free to unlock. 
    TEMPORARY: a slot's gem requirement can itself be a non-bazaar item (e.g. GEMSTONE_CHAMBER on
    Divan armor, crafted in the Forge) - get_modifier_cost returns 0 for anything not on the
    bazaar, so those cases will under-price until/unless that's handled separately.
    """
    item_slots = gemstone_costs.get(item_id)
    if item_slots is None or slot_key not in item_slots:
        return None
    
    parsed = parse_slot_cost(item_slots[slot_key])
    gem_cost = sum(get_modifier_cost(bazaar_prices, product_id, count) for product_id, count in parsed["gems"])
    return parsed["coins"] + gem_cost