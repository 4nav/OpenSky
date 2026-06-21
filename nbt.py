import base64
import gzip
import io
import nbtlib

def decode_item(item_bytes_64):
    raw = base64.b64decode(item_bytes_64)
    decompressed = gzip.decompress(raw)
    nbt_data = nbtlib.File.parse(io.BytesIO(decompressed))
    return nbt_data
