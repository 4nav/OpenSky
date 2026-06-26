import asyncio
import aiohttp
from bazaar import fetch_bazaar, parse_bazaar

async def check_enchants():
    async with aiohttp.ClientSession() as session:
        products = await fetch_bazaar(session)
    prices = parse_bazaar(products)
    # check enchants
    enchant_keys = [k for k in prices.keys() if k.startswith("ENCHANTMENT")]
    print(f"total enchant products: {len(enchant_keys)}")
    print("sample:", enchant_keys[:10])

asyncio.run(check_enchants())