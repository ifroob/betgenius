# Pick Selection Logic Fix - Documentation

## Issue Identified
The betting pick selection logic was incorrectly choosing picks based on the **highest edge** (difference between model probability and market probability) rather than the **most likely outcome** based on projected scores.

## Example of the Bug
**Match:** Nottingham Forest (Home) vs Manchester City (Away)

**Projected Scores:**
- Nottingham Forest (Home): 1.82
- Manchester City (Away): 2.22

**Model Probabilities:**
- Home: 31%
- Draw: 30%
- Away: 39%

**Old Buggy Logic:**
- Would pick based on highest edge vs market odds
- Could select "Home" or "Draw" even though "Away" has the highest probability

**Result:** Illogical picks where the team with lower projected score gets selected

## Root Cause
The bug was in two locations in `/app/betgenius/backend/server.py`:

### Location 1: Generate Picks Function (Line ~1110)
```python
# OLD BUGGY CODE
best_outcome = max(probs.keys(), key=lambda k: probs[k] - market_probs[k])
```

### Location 2: Simulation Function (Line ~1323)
```python
# OLD BUGGY CODE
best_outcome = max(probs.keys(), key=lambda k: probs[k] - market_probs[k])
```

## The Fix
Changed the selection logic to pick the outcome with the **highest model probability**:

```python
# NEW CORRECT CODE
# Pick the outcome with highest model probability (aligns with projected scores)
best_outcome = max(probs.keys(), key=lambda k: probs[k])
```

## Why This is Correct
1. **Projected scores reflect team strength:** If Man City has a higher projected score (2.22 vs 1.82), they should be picked
2. **Probabilities are derived from scores:** The `calculate_outcome_probabilities()` function converts scores to win probabilities
3. **Logical consistency:** The pick should align with "who is most likely to win" based on the model's assessment
4. **Edge is still calculated:** The edge percentage is still computed and displayed, but doesn't determine the pick

## What Changed for Users
### Before Fix:
- Picks could seem random or illogical
- Team with lower projected score might be selected
- Edge was the primary selection criterion

### After Fix:
- Picks align with projected scores
- Team with higher probability of winning gets selected
- Edge is displayed as additional information for bet value assessment
- More intuitive and predictable outcomes

## Testing
The fix has been tested with:
1. **User's example:** Nottingham Forest vs Man City - correctly selects "Away" (39% probability)
2. **Strong home scenario:** Home 2.5 vs Away 1.0 - correctly selects "Home" (70% probability)

## Files Modified
- `/app/betgenius/backend/server.py` (Lines 1110 and 1323)

## Impact
- ✅ More logical and predictable picks
- ✅ Picks align with projected scores
- ✅ Better user trust in the system
- ✅ Edge percentage still available for value assessment
- ⚠️ Some historical picks/simulations may show different results when re-run

## Date Fixed
December 22, 2024
