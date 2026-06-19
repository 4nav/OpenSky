import base64
import gzip
import io
import nbtlib

def decode_item(item_bytes_64):
    raw = base64.b64decode(item_bytes_64)
    decompressed = gzip.decompress(raw)
    nbt_data = nbtlib.File.parse(io.BytesIO(decompressed))
    return nbt_data

def extract_item_data(item_bytes_64, tier):
    nbt_data = decode_item(item_bytes_64)
    item = nbt_data["i"][0]
    extra = item["tag"]["ExtraAttributes"]

    return{
        "item_id": str(extra["id"]),
        "name": str(item["tag"]["display"]["Name"]),
        "reforge" : str(extra.get("modifier","")),
        "enchantments" : dict(extra.get("enchantments", {})),
        "tier" : tier,
        "rarity_upgrades" : int(extra.get("rarity_upgrades", 0)),
        "dye_item" : str(extra.get("dye_item", ""))
    }