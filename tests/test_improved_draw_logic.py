#!/usr/bin/env python3
"""
Test the NEW dynamic draw probability logic.
"""

def calculate_outcome_probabilities(home_score: float, away_score: float) -> dict:
    """
    Convert projected scores to outcome probabilities.
    Dynamic draw probability - increases when teams are more evenly matched.
    """
    diff = home_score - away_score
    
    if diff > 0.8:
        # Clear home advantage
        home_prob = 0.55 + min(diff * 0.1, 0.3)
        draw_prob = 0.25 - min(diff * 0.05, 0.15)
        away_prob = 1 - home_prob - draw_prob
    elif diff < -0.8:
        # Clear away advantage
        away_prob = 0.55 + min(abs(diff) * 0.1, 0.3)
        draw_prob = 0.25 - min(abs(diff) * 0.05, 0.15)
        home_prob = 1 - away_prob - draw_prob
    else:
        # Close match - dynamic draw probability based on how evenly matched
        # Draw probability: 40% when perfectly even (diff=0), declining to 25% at diff=0.8
        evenness_factor = 1 - min(abs(diff), 0.8) / 0.8  # 1.0 when diff=0, 0.0 when diff=0.8
        draw_prob = 0.25 + (0.15 * evenness_factor)
        
        # Split remaining probability between home and away based on score difference
        remaining = 1 - draw_prob
        if diff >= 0:
            home_prob = remaining * (0.5 + diff * 0.1)
            away_prob = remaining - home_prob
        else:
            away_prob = remaining * (0.5 + abs(diff) * 0.1)
            home_prob = remaining - away_prob
    
    return {
        "home": round(max(0.05, min(0.85, home_prob)), 3),
        "draw": round(max(0.10, min(0.40, draw_prob)), 3),
        "away": round(max(0.05, min(0.85, away_prob)), 3)
    }

print("=" * 80)
print("IMPROVED DRAW LOGIC TEST - Dynamic Draw Probability")
print("=" * 80)

test_cases = [
    {"home": 1.50, "away": 1.50, "desc": "Perfectly Even Match"},
    {"home": 1.55, "away": 1.50, "desc": "Very Close Match (0.05 diff)"},
    {"home": 1.60, "away": 1.50, "desc": "Slightly Close Match (0.10 diff)"},
    {"home": 1.70, "away": 1.50, "desc": "Close Match (0.20 diff)"},
    {"home": 1.90, "away": 1.50, "desc": "Moderate Advantage (0.40 diff)"},
    {"home": 2.10, "away": 1.50, "desc": "Clear Advantage (0.60 diff)"},
    {"home": 2.50, "away": 1.50, "desc": "Large Advantage (1.00 diff)"},
]

print("\nTesting various score differences:\n")
print(f"{'Scores':<20} {'H%':<8} {'D%':<8} {'A%':<8} {'Pick':<8} {'Description':<30}")
print("-" * 90)

for case in test_cases:
    h_score = case["home"]
    a_score = case["away"]
    probs = calculate_outcome_probabilities(h_score, a_score)
    pick = max(probs.keys(), key=lambda k: probs[k])
    
    scores = f"{h_score:.2f} - {a_score:.2f}"
    h_pct = f"{probs['home']*100:.1f}%"
    d_pct = f"{probs['draw']*100:.1f}%"
    a_pct = f"{probs['away']*100:.1f}%"
    
    pick_display = f"{pick.upper()}"
    if pick == "draw":
        pick_display = f"✅ {pick_display}"
    
    print(f"{scores:<20} {h_pct:<8} {d_pct:<8} {a_pct:<8} {pick_display:<8} {case['desc']:<30}")

print("\n" + "=" * 80)
print("KEY OBSERVATIONS:")
print("=" * 80)
print("✅ Draw probability is now HIGHEST (40%) for perfectly even matches")
print("✅ Draw probability decreases as score difference increases")
print("✅ Draw can now win and be selected as the pick")
print("✅ For lopsided matches, home/away still dominate as expected")
print("=" * 80)

# Detailed breakdown for perfectly even match
print("\n" + "=" * 80)
print("DETAILED BREAKDOWN: Perfectly Even Match (1.50 vs 1.50)")
print("=" * 80)

probs = calculate_outcome_probabilities(1.50, 1.50)
pick = max(probs.keys(), key=lambda k: probs[k])

print(f"\nScore Difference: 0.00")
print(f"Evenness Factor: 1.0 (completely even)")
print(f"Draw Probability: 0.25 + (0.15 × 1.0) = {probs['draw']*100:.1f}%")
print(f"\nProbabilities:")
print(f"  Home: {probs['home']*100:.1f}%")
print(f"  Draw: {probs['draw']*100:.1f}%  ← HIGHEST")
print(f"  Away: {probs['away']*100:.1f}%")
print(f"\n✅ Selected Pick: {pick.upper()}")
print(f"\nThis makes sense because when teams are perfectly matched,")
print(f"a draw becomes the most likely outcome!")
