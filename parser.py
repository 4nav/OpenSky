import json
from nbt import decode_item
from pet import is_pet, extract_pet_data

def extract_item_data(item_bytes_64, tier):
    nbt_data = decode_item(item_bytes_64)
    item = nbt_data["i"][0]
    extra = item["tag"]["ExtraAttributes"]

    return {
        "item_id": str(extra["id"]),
        "name": str(item["tag"]["display"]["Name"]),
        "reforge": str(extra.get("modifier", "")),
        "enchantments": dict(extra.get("enchantments", {})),
        "tier": tier,
        "rarity_upgrades": int(extra.get("rarity_upgrades", 0)),
        "dye_item": str(extra.get("dye_item", "")),
        "hot_potato_count": int(extra.get("hot_potato_count", 0)),
    }

def extract_sold_item(item_bytes_64):
    nbt_data = decode_item(item_bytes_64)
    item = nbt_data["i"][0]
    extra = item["tag"]["ExtraAttributes"]

    if is_pet(extra):
        pet_data = extract_pet_data(extra)
        return {
            "item_id": f"PET_{pet_data['species']}",
            "quantity": int(item["Count"]),
            "enchantments": "[]",
            "rarity_upgrades": 0,
            "hot_potato_count": 0,
        }
    
    enchants = dict(extra.get("enchantments", {}))
    return {
        "item_id": str(extra["id"]),
        "quantity": int(item["Count"]),
        "enchantments": json.dumps(enchants),
        "rarity_upgrades": int(extra.get("rarity_upgrades", 0)),
        "hot_potato_count": int(extra.get("hot_potato_count", 0)),
    }