VOLUME_TIER_WEIGHTS = {"high":1.0, "medium":0.8, "low":0.5, "illiquid":0.2}

def confidence_factor(sample_size, volume_tier, full_confidence_samples=20, tier_weights=None):
    """
    Scales 0-1 based on how much we should trust this item's fair_price estimate.
    """
    weights = tier_weights or VOLUME_TIER_WEIGHTS
    sample_component = min(sample_size / full_confidence_samples, 1.0)
    tier_component = weights.get(volume_tier, 0.2)
    return sample_component * tier_component

def score_flip(flip, full_confidence_samples=20, volatility_penalty=1.0, tier_weights=None):
    """
    Kinda like a Sharpe score but modified slightly since we do value resellability
    """
    conf = confidence_factor(flip["sample_size"], flip["volume_tier"], full_confidence_samples, tier_weights)
    return flip["profit"] * conf/ (1 + volatility_penalty * flip["sigma"])

def rank_flips(flips, full_confidence_samples=20, volatility_penalty=1.0, tier_weights=None):
    """
    Returns a list of flips sorted by score descending.
    """
    scored = []
    for flip in flips:
        scored_flip = dict(flip)
        scored_flip["score"] = score_flip(flip, full_confidence_samples, volatility_penalty, tier_weights)
        scored.append(scored_flip)
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    return [flip for flip in scored]