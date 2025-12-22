# Market Value/Probability Explanation

## What is Market Probability?

**Market probability** is the implied probability of an outcome based on the **bookmaker's odds**.

## Formula

```python
market_probability = 1 / decimal_odds
```

## Examples

| Outcome | Decimal Odds | Market Probability | Explanation |
|---------|--------------|-------------------|-------------|
| Home Win | 2.00 | 1/2.00 = **50%** | Bookmaker thinks home has 50% chance |
| Draw | 3.50 | 1/3.50 = **28.6%** | Bookmaker thinks draw has 28.6% chance |
| Away Win | 4.00 | 1/4.00 = **25%** | Bookmaker thinks away has 25% chance |

## Why Odds Work This Way

**Lower odds = Higher probability = More likely to happen**
- Odds of 1.50 = 66.7% probability (strong favorite)
- Odds of 10.0 = 10% probability (big underdog)

**The Bookmaker's Margin (Overround)**

If you add up all market probabilities, they exceed 100%:
```
50% + 28.6% + 25% = 103.6%
```

This 3.6% "overround" is the bookmaker's profit margin built into the odds.

## How Market Probability is Used in BetGenius

### 1. **Edge Calculation** ✅ (DISPLAYED TO USER)

Edge measures how much better your model's assessment is versus the market:

```python
edge = (model_probability - market_probability) / market_probability × 100
```

**Example:**
- Your model: Away team has **39%** chance to win
- Market odds: 2.22 → Market probability = **45%**
- Edge = (0.39 - 0.45) / 0.45 × 100 = **-13.4%**

**Interpretation:**
- **Positive edge (+10%)**: Your model thinks the outcome is MORE likely than the market → Value bet opportunity
- **Negative edge (-10%)**: Your model thinks the outcome is LESS likely than the market → Avoid this bet
- **Zero edge (0%)**: Your model agrees with the market

### 2. **Confidence Score Calculation** ✅ (INTERNAL USE)

Market probability is one factor in calculating the 1-10 confidence score:

```python
def calculate_confidence(model_prob, market_prob, home_score, away_score):
    # Factor 1: Edge percentage
    edge = (model_prob - market_prob) / market_prob * 100
    
    # Factor 2: Model probability strength (higher = more confident)
    # Factor 3: Score differential clarity (bigger difference = clearer winner)
    
    # Returns: 1-10 confidence score
```

### 3. **Pick Selection** ❌ (NOT USED - AFTER FIX)

**IMPORTANT:** Market probability is **NOT** used to determine the pick itself!

**Pick is determined by:**
```python
best_outcome = max(probs.keys(), key=lambda k: probs[k])
```

This selects the outcome with the **highest model probability** only.

## Complete Flow Example

**Match:** Nottingham Forest vs Manchester City

### Step 1: Model Calculates Projected Scores
```
Home (Forest): 1.82 goals
Away (City):   2.22 goals
```

### Step 2: Convert to Model Probabilities
```python
probs = calculate_outcome_probabilities(1.82, 2.22)
```
Result:
```
Home: 31%
Draw: 30%
Away: 39%  ← Highest
```

### Step 3: Select Pick (ONLY uses model probabilities)
```python
best_outcome = max(probs.keys(), key=lambda k: probs[k])
# Result: "away" (39% is highest)
```

### Step 4: Calculate Edge (uses market probabilities)
```python
market_odds = {"home": 3.18, "draw": 3.50, "away": 2.22}
market_probs = {
    "home": 1/3.18 = 31.4%,
    "draw": 1/3.50 = 28.6%,
    "away": 1/2.22 = 45.0%
}

# Edge for the selected pick (away)
edge = (39% - 45%) / 45% × 100 = -13.4%
```

### Step 5: Calculate Confidence
```python
confidence = calculate_confidence(
    model_prob=0.39,     # Away probability
    market_prob=0.45,    # Away market probability  
    home_score=1.82,
    away_score=2.22
)
# Result: Confidence score between 1-10
```

### Step 6: Display to User
```
Pick: AWAY
Projected Score: 1.82 - 2.22
Odds: 2.22
Edge: -13.4%  ← Shows value assessment
Confidence: 6/10
```

## Summary: Market Probability's Role

| Use Case | Is Market Prob Used? | Purpose |
|----------|---------------------|---------|
| **Pick Selection** | ❌ NO | Pick is based ONLY on model probability |
| **Edge Calculation** | ✅ YES | Shows if bet has value vs market |
| **Confidence Score** | ✅ YES | Helps determine betting confidence |
| **Display Info** | ✅ YES | Shows user market odds and implied probability |

## Key Takeaway

**Market probability is used for ANALYSIS and VALUE ASSESSMENT, but does NOT determine which outcome is picked.**

The pick is purely based on your model's assessment of what is most likely to happen.
