import sqlite3
import json

DB_PATH = "auctions.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
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
