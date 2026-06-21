import asyncio
import aiohttp
import time
from fetcher import get_page
from parser import extract_item_data
from pet import extract_pet_data, is_pet
from database import get_db_connection, create_tables, insert_item_listing, insert_pet

POLL_INTERVAL = 25 # Faster than main since we need to snipe the live auctions before they end

def process_ended_auction(conn, auction):
    try:
        sold_data = extract_item_data(auction["item_bytes"])
        insert_item_listing(conn, sold_data, auction)
    
    except Exception as e:
        print(f"Failed on auction {auction['auction_id', '???']}: {e}")

async def run_cycle(conn):
    async with aiohttp.ClientSession() as session:
        data = await get_page(session, 0, ended=True)
        auctions = data["auctions"]

        for auction in auctions:
            process_ended_auction(conn, auction)

        conn.commit()

        print(f"Cycle completed at {time.ctime()}  - Processed {len(auctions)} ended auctions")

async def main():
    conn = get_db_connection()
    create_tables(conn)

    while True:
        start = time.time()
        await run_cycle(conn)
        elapsed = time.time() - start
        sleep_time = max(0, POLL_INTERVAL - elapsed)
        print(f"Sleeping for {sleep_time:.2f} seconds")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(main())