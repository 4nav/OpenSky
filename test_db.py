import asyncio
import aiohttp  
import sqlite3
from database import create_tables, get_db_connection
from fetcher import get_page

DB_PATH = "auctions.db"

async def test_db():
    async with aiohttp.ClientSession() as session:
        first = await get_page(session, 0)
        total_pages = first["totalPages"]

        tasks = [get_page(session, page) for page in range(1, total_pages)]

        rest = await asyncio.gather(*tasks)
        all_auctions = first["auctions"]

        for page in rest:
            all_auctions.extend(page["auctions"])

    bin_count = sum(1 for auction in all_auctions if auction.get("bin"))
    print(f"Total BIN auctions: {bin_count}")

    conn = sqlite3.connect(DB_PATH)

    item_count = conn.execute("SELECT COUNT(*) FROM item_listings").fetchone()[0]

    pet_count = conn.execute("SELECT COUNT(*) FROM pet_listings").fetchone()[0]

    print(f"DB item_listings: {item_count}")

    print(f"DB pet_listings: {pet_count}")

    print(f"DB total: {item_count + pet_count}  (vs {bin_count} live BIN auctions)")

    bad_items = conn.execute(
        "SELECT COUNT(*) FROM item_listings WHERE item_id = '' OR item_id IS NULL OR name = '' OR name IS NULL"
    ).fetchone()[0]

    bad_pets = conn.execute(
        "SELECT COUNT(*) FROM pet_listings WHERE species = '' OR species IS NULL"
    ).fetchone()[0]

    print(f"Items with missing item_id/name: {bad_items}")
    
    print(f"Pets with missing species: {bad_pets}")

    conn.close()

asyncio.run(test_db())