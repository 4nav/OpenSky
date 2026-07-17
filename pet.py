import json
from nbt import decode_item

def is_pet(extra):
    return "petInfo" in extra

def extract_pet_data(extra):
    pet_info = json.loads(str(extra["petInfo"]))

    return {
        "species": pet_info["type"],
        "pet_tier": pet_info["tier"],
        "exp": float(pet_info["exp"]),
        "held_item": pet_info.get("heldItem", ""),
        "skin": pet_info.get("skin", ""),
        "candy_used": int(pet_info.get("candyUsed", 0)),
    }