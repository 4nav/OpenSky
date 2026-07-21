import json

RARITY_ORDER = ["COMMON", "UNCOMMON", "RARE", "EPIC", "LEGENDARY", "MYTHIC", "DIVINE"]

def load_item_rarities(path = "static_data/item_rarities.json"):
    """Static item id -> base rarity lookup, built by parsing NEU repo item lore text"""
    with open(path, "r") as f:
        return json.load(f)
    
def get_effective_rarity(item_id, rarity_upgrades, item_rarities):
    """Base rarity of the item, bumped up by rarity_upgrades (each recomb bumps one tier, capped at DIVINE). 
    """
    base = item_rarities.get(item_id)

    if base is None or base not in RARITY_ORDER:
        return base 
    
    index = RARITY_ORDER.index(base) + rarity_upgrades
    index = min(index, len(RARITY_ORDER) - 1)
    return RARITY_ORDER[index]
