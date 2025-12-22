#!/usr/bin/env python3
"""
Test script to verify the pick logic fix.
This tests that picks are selected based on highest probability, not highest edge.
"""

def calculate_outcome_probabilities(home_score: float, away_score: float) -> dict:
    """Convert projected scores to outcome probabilities"""
    diff = home_score - away_score
    
    if diff > 0.8:
        home_prob = 0.55 + min(diff * 0.1, 0.3)
        draw_prob = 0.25 - min(diff * 0.05, 0.15)
        away_prob = 1 - home_prob - draw_prob
    elif diff < -0.8:
        away_prob = 0.55 + min(abs(diff) * 0.1, 0.3)
        draw_prob = 0.25 - min(abs(diff) * 0.05, 0.15)
        home_prob = 1 - away_prob - draw_prob
    else:
        draw_prob = 0.30
        home_prob = 0.35 + diff * 0.1
        away_prob = 1 - home_prob - draw_prob
    
    return {
        "home": round(max(0.05, min(0.85, home_prob)), 3),
        "draw": round(max(0.10, min(0.40, draw_prob)), 3),
        "away": round(max(0.05, min(0.85, away_prob)), 3)
    }

# Test Case 1: User's example - Nottingham Forest vs Man City
print("=" * 80)
print("TEST CASE 1: Nottingham Forest (Home) vs Manchester City (Away)")
print("=" * 80)

home_score = 1.82
away_score = 2.22

print(f"\nProjected Scores:")
print(f"  Home (Nottingham Forest): {home_score}")
print(f"  Away (Manchester City):   {away_score}")

probs = calculate_outcome_probabilities(home_score, away_score)
print(f"\nModel Probabilities:")
print(f"  Home: {probs['home']*100:.1f}%")
print(f"  Draw: {probs['draw']*100:.1f}%")
print(f"  Away: {probs['away']*100:.1f}%")

# Simulate market odds
market_odds = {"home": 3.18, "draw": 3.50, "away": 2.22}
market_probs = {
    "home": 1 / market_odds["home"],
    "draw": 1 / market_odds["draw"],
    "away": 1 / market_odds["away"]
}

print(f"\nMarket Odds & Probabilities:")
print(f"  Home: {market_odds['home']:.2f} ({market_probs['home']*100:.1f}%)")
print(f"  Draw: {market_odds['draw']:.2f} ({market_probs['draw']*100:.1f}%)")
print(f"  Away: {market_odds['away']:.2f} ({market_probs['away']*100:.1f}%)")

# Calculate edges
edges = {
    "home": (probs["home"] - market_probs["home"]) / market_probs["home"] * 100,
    "draw": (probs["draw"] - market_probs["draw"]) / market_probs["draw"] * 100,
    "away": (probs["away"] - market_probs["away"]) / market_probs["away"] * 100
}

print(f"\nEdge Percentages:")
print(f"  Home: {edges['home']:+.1f}%")
print(f"  Draw: {edges['draw']:+.1f}%")
print(f"  Away: {edges['away']:+.1f}%")

# NEW LOGIC: Pick based on highest probability
best_outcome_new = max(probs.keys(), key=lambda k: probs[k])

# OLD BUGGY LOGIC: Pick based on highest edge
best_outcome_old = max(probs.keys(), key=lambda k: probs[k] - market_probs[k])

print(f"\n" + "=" * 80)
print(f"RESULTS:")
print(f"=" * 80)
print(f"✅ NEW LOGIC (Highest Probability): {best_outcome_new.upper()} ({probs[best_outcome_new]*100:.1f}%)")
print(f"❌ OLD LOGIC (Highest Edge):        {best_outcome_old.upper()} ({edges[best_outcome_old]:+.1f}% edge)")

if best_outcome_new == "away":
    print(f"\n✅ CORRECT! Away team has higher projected score (2.22 > 1.82), so 'away' is picked.")
else:
    print(f"\n❌ ERROR! Away team has higher projected score (2.22 > 1.82), but '{best_outcome_new}' was picked!")

# Test Case 2: Clear home win scenario
print("\n\n" + "=" * 80)
print("TEST CASE 2: Strong Home Team vs Weak Away Team")
print("=" * 80)

home_score = 2.5
away_score = 1.0

print(f"\nProjected Scores:")
print(f"  Home: {home_score}")
print(f"  Away: {away_score}")

probs = calculate_outcome_probabilities(home_score, away_score)
print(f"\nModel Probabilities:")
print(f"  Home: {probs['home']*100:.1f}%")
print(f"  Draw: {probs['draw']*100:.1f}%")
print(f"  Away: {probs['away']*100:.1f}%")

best_outcome = max(probs.keys(), key=lambda k: probs[k])
print(f"\n✅ Pick: {best_outcome.upper()} ({probs[best_outcome]*100:.1f}%)")

if best_outcome == "home":
    print("✅ CORRECT! Home team has significantly higher score.")
else:
    print(f"❌ ERROR! Expected 'home' but got '{best_outcome}'")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
