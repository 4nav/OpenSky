import aiohttp

BAZAAR_URL = "https://api.hypixel.net/skyblock/bazaar"

async def fetch_bazaar(session):
    async with session.get(BAZAAR_URL) as resp:
        data = await resp.json()
        return data["products"]

def parse_bazaar(products):
    prices = {}
    for product_id, product in products.items():
        qs = product.get("quick_status", {})
        prices[product_id] = {
            "instabuy": qs.get("sellPrice", 0),   # cost to buy instantly
            "instasell": qs.get("buyPrice", 0),    # coins received selling instantly
            "buy_volume": qs.get("buyVolume", 0),
            "sell_volume": qs.get("sellVolume", 0),
        }
    return prices

def enchant_to_bazaar_key(name,level):
    return f"ENCHANTMENT_{name.upper()}_{level}"

def get_enchant_cost(prices,name,level):
    key = enchant_to_bazaar_key(name, level)
    return prices.get(key, {}).get("instabuy", 0)

def get_modifier_cost(prices, modifier_id, count = 1):
    return count * prices.get(modifier_id, {}).get("instabuy", 0)