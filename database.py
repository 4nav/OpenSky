import sqlite3
import json
import time

DB_PATH = "auctions.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH,timeout=15)
    return conn

def create_tables(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS item_listings (
            uuid TEXT PRIMARY KEY,
            item_id TEXT,
            name TEXT,
            price INTEGER,
            reforge TEXT,
            enchantments TEXT,
            tier TEXT,
            rarity_upgrades INTEGER,
            dye_item TEXT,
            bin INTEGER,
            start INTEGER,
            end INTEGER
        )
        """)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS pet_listings (
            uuid TEXT PRIMARY KEY,
            species TEXT,
            pet_tier TEXT,
            exp REAL,
            held_item TEXT,
            skin TEXT,
            candy_used INTEGER,
            price INTEGER,
            bin INTEGER,
            start INTEGER,
            end INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ended_auctions (
            auction_id TEXT PRIMARY KEY,
            item_id TEXT,
            quantity INTEGER,
            price INTEGER,
            bin INTEGER,
            sold_at INTEGER,
            enchantments TEXT,
            rarity_upgrades INTEGER,
            bids TEXT,
            hot_potato_count INTEGER,
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bazaar_prices (
            product_id TEXT PRIMARY KEY,
            instabuy REAL,
            instasell REAL,
            buy_volume INTEGER,
            sell_volume INTEGER,
            updated_at INTEGER
        )
        """
    )

    conn.commit()

def insert_item_listing(conn, item_data, auction):
    conn.execute(
        """
        INSERT OR REPLACE INTO item_listings (
            uuid, item_id, name, price, reforge, enchantments, tier, rarity_upgrades, dye_item, bin, start, end
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            auction["uuid"],
            item_data["item_id"],
            item_data["name"],
            auction["starting_bid"],
            item_data["reforge"],
            json.dumps(item_data["enchantments"]),
            item_data["tier"],
            item_data["rarity_upgrades"],
            item_data["dye_item"],
            int(auction.get("bin", False)),
            auction["start"],
            auction["end"],
        )
    )

def insert_pet(conn, pet_data, auction):
    conn.execute("""
        INSERT OR REPLACE INTO pet_listings
        (uuid, species, pet_tier, exp, held_item, skin, candy_used,
         price, bin, start, end)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        auction["uuid"],
        pet_data["species"],
        pet_data["pet_tier"],
        pet_data["exp"],
        pet_data["held_item"],
        pet_data["skin"],
        pet_data["candy_used"],
        auction["starting_bid"],
        int(auction.get("bin", False)),
        auction["start"],
        auction["end"],
    )
)
    
def insert_ended_auction(conn, sold_data, auction):
    conn.execute("""
        INSERT OR REPLACE INTO ended_auctions
        (auction_id, item_id, quantity, price, bin, sold_at, enchantments, rarity_upgrades, bids, hot_potato_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        auction["auction_id"],
        sold_data["item_id"],
        sold_data["quantity"],
        auction["price"],
        int(auction.get("bin", False)),
        auction["timestamp"],
        sold_data.get("enchantments", "[]"),
        sold_data.get("rarity_upgrades", 0),
        json.dumps(auction.get("bids", [])),
        sold_data.get("hot_potato_count", 0),
    )
)

def upsert_bazaar_prices(conn,prices):
    now = int(time.time() * 1000)
    conn.executemany("""
        INSERT OR REPLACE INTO bazaar_prices
        (product_id, instabuy, instasell, buy_volume, sell_volume, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        (pid, p["instabuy"], p["instasell"], p["buy_volume"], p["sell_volume"], now)
        for pid, p in prices.items()
    ])
