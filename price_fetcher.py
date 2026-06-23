import aiohttp
import asyncio

URL = "https://api.hypixel.net/skyblock/auctions_ended"

async def get_ended_auctions(session):
    async with aiohttp.ClientSession() as session:
        async with session.get(URL) as response:
            return await response.json()
    
async def main():
    async with aiohttp.ClientSession() as session:
        data = await get_ended_auctions(session)
        print(f"Total ended auctions: {len(data['auctions'])}")
        
if __name__ == "__main__":
    asyncio.run(main())