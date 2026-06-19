import aiohttp
import asyncio

URL = "https://api.hypixel.net/skyblock/auctions"

async def get_page(session, page):
    async with session.get(URL, params={"page": page}) as response:
        return await response.json()

async def main():
    async with aiohttp.ClientSession() as session:
        first = await get_page(session, 0)
        total_pages = first["totalPages"]
        print(f"Total pages: {total_pages}")

        tasks = [get_page(session, page) for page in range(1, total_pages)]
        rest = await asyncio.gather(*tasks)

        all_auctions = first["auctions"]
        for page_data in rest:
            all_auctions.extend(page_data["auctions"])

        print(f"Total auctions: {len(all_auctions)}")
if __name__ == "__main__":
    asyncio.run(main())
