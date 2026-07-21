import asyncio
import aiohttp
import json
from datetime import datetime
from database import get_db_connection, create_tables
from parser import extract_gemstones

COFL_BASE = "https://sky.coflnet.com/api"
RATE_LIMIT_DELAY = 0.5

def iso_to_ms(iso_str):
    return int(datetime.fromisoformat(iso_str).timestamp() * 1000)

def get_all_items(conn):
    return [
        row[0] for row in conn.execute(
            "SELECT DISTINCT item_id FROM item_listings"
        ).fetchall()
    ]

async def fetch_sold(session, item_id):
    url = f"{COFL_BASE}/auctions/tag/{item_id}/sold"
    async with session.get(url) as response:
        if response.status != 200:
            return []
        return await response.json()

def insert_cofl_sales(conn, item_id, sales):
    rows = []
    for sale in sales:
        if not sale.get("bin"):
            continue
        try:
            flattened = sale.get("flattenedNbt", {})
            rows.append((
                sale["uuid"],
                item_id,
                sale.get("count", 1),
                sale.get("highestBidAmount", 0),
                1,
                iso_to_ms(sale["end"]),
                json.dumps(sale.get("enchantments", [])),
                int(flattened.get("rarity_upgrades", 0)),
                "[]",
                int(flattened.get("hot_potato_count", 0)),
                json.dumps(extract_gemstones(flattened)),
                flattened.get("modifier", ""),
            ))
        except Exception as e:
            print(f"row failed: {e}")
            continue

    conn.executemany("""
        INSERT OR IGNORE INTO ended_auctions
        (auction_id, item_id, quantity, price, bin, sold_at, enchantments, rarity_upgrades, bids, hot_potato_count, gemstones, reforge)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    conn.commit()
    return len(rows)

async def bootstrap():
    conn = get_db_connection()
    create_tables(conn)

    items = get_all_items(conn)
    print(f"items to bootstrap: {len(items)}")

    async with aiohttp.ClientSession() as session:
        for i, item_id in enumerate(items):
            sales = await fetch_sold(session, item_id)
            inserted = insert_cofl_sales(conn, item_id, sales)
            print(f"[{i+1}/{len(items)}] {item_id}: {inserted} sales inserted")
            await asyncio.sleep(RATE_LIMIT_DELAY)

    conn.close()
    print("bootstrap complete")

if __name__ == "__main__":
    asyncio.run(bootstrap())