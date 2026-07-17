from itertools import count
import numpy as np
import json
import time
from bazaar import get_modifier_cost

SEVEN_DAYS_MS   = 7 * 24 * 60 * 60 * 1000
ONE_DAY_MS      = 24 * 60 * 60 * 1000
MIN_VWAP_SALES  = 5
LIQ_THRESHOLD   = 5  

#----------------------Volume-------------------------------------------------------
def get_daily_volume(conn,item_id):
    '''
    Estimate BIN sale volume from total sales in time period (we cap at 7 days prior since updates might come around which kill 
    the demand for our item but our flipper would assume it has medium sales stillS)
    '''
    row = conn.execute("""
        SELECT COUNT(*), MIN(sold_at), MAX(sold_at)
        FROM ended_auctions
        WHERE item_id = ? AND bin = 1
    """, (item_id,)).fetchone()

    count,earliest,latest = row
    if not count or count < 2 or earliest == latest:
        return 0
    
    day_span = min((latest - earliest)/ ONE_DAY_MS,7)

    return count / day_span if day_span > 0 else 0


def volume_tier(daily_vol):
    """
    classify liquidity of item
    """
    if daily_vol > 20: return "high"
    if daily_vol > 5: return "medium"
    if daily_vol > 1: return "low"
    else: return "illiquid"

#----------------------Enchantments-------------------------------------------------
def get_enchant_true_cost(prices, name, level):
    '''
    Real cost of enchant book -  we can use 16 sharp 1 books, 8 sharp 2 books, 4 sharp 3 books, 2 sharp 4 books or 1 sharp 5
    and we compute the min across all
    cost(N) = min(bazaar_price(N), 2 × cost(N-1))
    '''
    bazaar_price = prices.get(f"ENCHANTMENT_{name.upper()}_{level}", {}).get("instabuy", 0)
    if level <= 1:
        return bazaar_price
    combine_cost = 2 * get_enchant_true_cost(prices, name, level - 1)
    return min(bazaar_price, combine_cost)

def calc_enchant_cost(prices, enchantments_json, daily_vol, cap=None):
    """
    Sum true cost of all enchants on an item, discounted by base item liquidity.
    High enchant on unpopular item -> near-zero contribution.
    Handles both NBT dict format and Coflnet list format - NBT format: {"sharpness": 5} but Coflnet format: [{"type": "sharpness", "level": 5}]:
      both normalised to dict before processing
    """
    
    if not enchantments_json:
        return 0
    
    try:
        raw = json.loads(enchantments_json)
    except (json.JSONDecodeError, TypeError):
        return 0


    # normalise to {name: level}
    if isinstance(raw,list):
        enchants = {e["type"]: e["level"] for e in raw}
    else :
        enchants = raw
    
    liq_score = min(daily_vol/ LIQ_THRESHOLD, 1.0)

    total = sum(
        get_enchant_true_cost(prices, name, level)
        for name, level in enchants.items()
    )
    discounted = total * liq_score

    return min(discounted, cap) if cap is not None else discounted

def get_percentile(n_sales):
    if(n_sales < 10):return 70
    if n_sales < 50: return 80
    if n_sales < 200: return 90
    return 99

def get_enchant_cost_cap(conn, item_id):
    """
    Max enchant premium the market's actually paid for this item, scaled by sample size.
    """
    clean_rows = conn.execute("""
        SELECT price, quantity FROM ended_auctions
        WHERE item_id = ? AND bin = 1 
          AND (enchantments = '{}' OR enchantments = '[]' OR enchantments IS NULL)
    """, (item_id,)).fetchall()

    enchanted_rows = conn.execute("""
        SELECT price, quantity FROM ended_auctions
        WHERE item_id = ? AND bin = 1
          AND enchantments != '{}' AND enchantments != '[]' AND enchantments IS NOT NULL
    """, (item_id,)).fetchall()


    if(len(clean_rows) < 5 or len(enchanted_rows) < 5):
        return None
    
    clean_unit_prices = [p / max(q, 1) for p, q in clean_rows]
    enchanted_unit_prices = [p / max(q, 1) for p, q in enchanted_rows]


    clean_median = float(np.median(clean_unit_prices))
    percentile = get_percentile(len(enchanted_unit_prices))
    enchant_cap = float(np.percentile(enchanted_unit_prices, percentile)) 

    return max(enchant_cap - clean_median, 0)

#----------------------Price Fetching-------------------------------------------------

def _get_price_rows(conn,item_id, window_ms = SEVEN_DAYS_MS):
    """Rolling 7-day window.
    ORDER BY sold_at is required since log returns in get_item_stats assume chronological order, thus 
    random order produces meaningless rho"""

    cutoff = int(time.time()*1000) - window_ms

    return conn.execute("""
        SELECT price, quantity, enchantments, hot_potato_count, rarity_upgrades
        FROM ended_auctions
        WHERE item_id = ?
          AND bin = 1
          AND sold_at > ?
        ORDER BY sold_at
    """, (item_id, cutoff)).fetchall()


def _base_prices_rows(conn, item_id, bazaar_prices, rows, daily_vol):
    """"Strip enchant costs from item and create a list of base prices, preserve qty for VWAP"""
    cap = get_enchant_cost_cap(conn, item_id)
    result = []
    for price,qty,enchants_json,hpb_count, recomb_flag in rows:
        qty = max(qty, 1)
        unit_price = price/qty
        enchant_cost = calc_enchant_cost(bazaar_prices, enchants_json, daily_vol, cap)
        hpb_cost = (get_modifier_cost(bazaar_prices, "HOT_POTATO_BOOK", min(hpb_count, 10))
                    + get_modifier_cost(bazaar_prices, "FUMING_POTATO_BOOK", max(0, hpb_count - 10)))
        recomb_cost = get_modifier_cost(bazaar_prices, "RECOMBOBULATOR_3000", recomb_flag)
        base = unit_price - enchant_cost - hpb_cost - recomb_cost
        if base > 0:
                result.append((base,qty))
    return result

# ---------------------- Public API -------------------------------------------------

def get_item_stats(conn,item_id,bazaar_prices):
    """
    All stats in one call - uses VWAP if ≥ MIN_VWAP_SALES data points (enough volume to trust weighted average), median otherwise
    """

    rows = _get_price_rows(conn, item_id)
    daily_vol = get_daily_volume(conn, item_id)

    if not rows:
         return None
    price_rows = _base_prices_rows(conn, item_id, bazaar_prices, rows, daily_vol)
    if not price_rows:
         return None
    
    total_value = sum(p*q for p,q in price_rows)
    total_qty   = sum(q for _, q in price_rows)
    vwap        = total_value / total_qty if total_qty > 0 else None

    unit_prices = [p for p, _ in price_rows]
    arr         = np.array(unit_prices)
    median      = float(np.median(arr))
    log_returns = np.diff(np.log(arr)) if len(arr) > 1 else np.array([0.0])

    fair = vwap if len(price_rows) >= MIN_VWAP_SALES else median


    return {
        "item_id":      item_id,
        "fair_price":   fair,
        "vwap":         vwap,
        "median":       median,
        "sigma":        float(np.std(log_returns)),
        "daily_volume": daily_vol,
        "volume_tier":  volume_tier(daily_vol),
        "sample_size":  len(price_rows),
    }


def get_fair_price(conn, item_id, bazaar_prices):
    """"
    returns just the fair_price float from get_item_stats, or none if no data
    """
    stats = get_item_stats(conn, item_id, bazaar_prices)
    return stats["fair_price"] if stats else None

