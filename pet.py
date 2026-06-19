import json
from parser import decode_item


def is_pet(item_bytes_64):
    nbt_data = decode_item(item_bytes_64)
    extra = nbt_data["i"][0]["tag"]["ExtraAttributes"]
    return "petInfo" in extra

def extract_pet_data(item_bytes_64):
    nbt_data = decode_item(item_bytes_64)
    item = nbt_data["i"][0]
    extra = item["tag"]["ExtraAttributes"]

    pet_info = json.loads(str(extra["petInfo"]))

    return {
        "species": pet_info["type"],
        "pet_tier": pet_info["tier"],
        "exp": float(pet_info["exp"]),
        "held_item": pet_info.get("heldItem", ""),
        "skin": pet_info.get("skin", ""),
        "candy_used": int(pet_info.get("candyUsed", 0)),
    }