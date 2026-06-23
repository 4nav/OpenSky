import asyncio
import aiohttp
import time
from price_fetcher import get_ended_auctions
from parser import extract_sold_item
from database import get_db_connection, create_tables, insert_ended_auction

POLL_INTERVAL = 25

def process_ended_auction(conn, auction):
    try:
        sold_data = extract_sold_item(auction["item_bytes"])
        insert_ended_auction(conn, sold_data, auction)
    except Exception as e:
        print(f"Failed on auction {auction.get('auction_id', '???')}: {e}")

async def run_cycle(conn):
    async with aiohttp.ClientSession() as session:
        data = await get_ended_auctions(session)
    auctions = data["auctions"]

    for auction in auctions:
        process_ended_auction(conn, auction)

    conn.commit()
    print(f"Cycle completed at {time.ctime()} - Processed {len(auctions)} ended auctions")

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