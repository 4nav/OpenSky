import aiohttp
import asyncio
import sqlite3
from bazaar import fetch_bazaar, parse_bazaar
from quant import get_item_stats, _get_price_rows, _base_prices_rows
import numpy as np

async def test_quant():
    conn = sqlite3.connect("auctions.db", timeout = 15)

    async with aiohttp.ClientSession() as session:
        products = await fetch_bazaar(session)
    bazaar_prices = parse_bazaar(products)

    for item_id in ["VOIDWALKER_KATANA", "TREECAPITATOR_AXE", "GLACITE_CHESTPLATE", "DIVAN_LEGGINGS"]:
        stats = get_item_stats(conn, item_id, bazaar_prices)
        if stats:
            print(f"{item_id}: fair={stats['fair_price']:,.0f} | vwap={stats['vwap']:,.0f} | median={stats['median']:,.0f}")
            print(f"  σ={stats['sigma']:.4f} | daily_vol={stats['daily_volume']:.1f} ({stats['volume_tier']}) | samples={stats['sample_size']}")

            rows = _get_price_rows(conn, item_id)
            price_rows = _base_prices_rows(conn, item_id, bazaar_prices, rows, stats["daily_volume"])

            arr = np.array([p for p, _ in price_rows])

            print("Mean:", arr.mean())
            print("Percentiles:", np.percentile(arr, [0, 5, 10, 25, 50, 75, 90, 95, 99, 100]))
            print()
        else:
            print(f"{item_id}: no data available")

asyncio.run(test_quant())