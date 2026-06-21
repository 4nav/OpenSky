import asyncio
import aiohttp
import time
from fetcher import get_page
from parser import extract_item_data
from pet import extract_pet_data, is_pet
from database import get_db_connection, create_tables, insert_item_listing, insert_pet

POLL_INTERVAL = 60

async def fetch_all_auctions(session):
    first = await get_page(session, 0)
    total_pages = first["totalPages"]

    tasks = [get_page(session, page) for page in range(1, total_pages)]
    rest = await asyncio.gather(*tasks)

    all_auctions = first["auctions"]
    
    for page in rest:
        all_auctions.extend(page["auctions"])
    
    return all_auctions

def process_auction(conn,auction):
    if not auction.get("bin"):
        return
    
    try:
        if is_pet(auction["item_bytes"]):
            pet_data = extract_pet_data(auction["item_bytes"])
            insert_pet(conn, pet_data, auction)
        else:
            item_data = extract_item_data(auction["item_bytes"], auction.get("tier", ""))
            insert_item_listing(conn, item_data, auction)
    
    except Exception as e:
        print(f"Error processing auction {auction['uuid']}: {e}")

async def run_cycle(conn):
    async with aiohttp.ClientSession() as session:
        auctions = await fetch_all_auctions(session)
        for auction in auctions:
            process_auction(conn, auction)
        conn.commit()
    print(f"Cycle done - Processed {len(auctions)} auctions")  

async def main():
    conn = get_db_connection()
    create_tables(conn)

    while True:
        start = time.time()
        await run_cycle(conn)
        elapsed = time.time() - start
        sleep_time = max(0, POLL_INTERVAL - elapsed)
        print(f"Cycle completed at {time.ctime()} - Sleeping for {sleep_time:.2f} seconds")
        await asyncio.sleep(sleep_time)

if __name__ == "__main__":
    asyncio.run(main())