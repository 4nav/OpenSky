import asyncio, aiohttp, json

async def check():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://sky.coflnet.com/api/auctions/tag/POWER_WITHER_CHESTPLATE/sold") as resp:
            data = await resp.json()

    for sale in data:
        if "➍" in sale.get("itemName", ""):
            print(json.dumps(sale, indent=2))
            break

if __name__ == "__main__":
    asyncio.run(check())