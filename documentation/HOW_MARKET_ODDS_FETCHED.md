# How Market Odds Are Fetched in BetGenius

## Overview

**Market odds in BetGenius are NOT fetched from bookmakers** - they are **calculated internally** based on team statistics from real match data.

---

## Complete Process

### Step 1: Fetch Real Match Data from Football-Data.org API

**Source:** `https://api.football-data.org/v4/competitions/PL/matches`

**What's fetched:**
```json
{
  "matches": [
    {
      "id": 12345,
      "homeTeam": {"name": "Manchester City"},
      "awayTeam": {"name": "Liverpool"},
      "utcDate": "2024-12-25T15:00:00Z",
      "status": "SCHEDULED",
      "score": {
        "fullTime": {"home": null, "away": null}
      }
    }
  ]
}
```

**Note:** Football-Data.org API does **NOT** provide betting odds. It only provides:
- Match fixtures (teams, dates, times)
- Match results (when completed)
- Team names and basic info

**Code Location:** Lines 329-464 in `server.py` (function: `fetch_epl_fixtures_from_api()`)

---

### Step 2: Calculate Team Statistics from Historical Results

The system analyzes **completed matches** to calculate team ratings:

```python
def calculate_team_stats_from_matches(matches):
    # For each completed match, track:
    # - Goals scored/conceded
    # - Wins/draws/losses
    # - Home/away performance
    
    # Convert to ratings (0-100 scale):
    offense_rating = based on actual goals scored per match
    defense_rating = based on actual goals conceded per match  
    form_rating = based on actual win percentage
```

**Example Output:**
```python
{
  "Manchester City": {
    "offense": 85.5,  # High scoring team
    "defense": 82.3,  # Strong defense
    "form": 78.9,     # Good recent form
    "goals_for": 45,
    "goals_against": 18
  },
  "Nottingham Forest": {
    "offense": 68.2,
    "defense": 71.5,
    "form": 65.3,
    "goals_for": 28,
    "goals_against": 32
  }
}
```

**Code Location:** Lines 177-283 (function: `calculate_team_stats_from_matches()`)

---

### Step 3: Calculate Market Odds from Team Stats

Once team statistics are known, odds are **generated internally**:

```python
def calculate_odds_from_stats(home_stats, away_stats):
    # 1. Calculate team strength
    home_strength = (offense + defense + form) / 3
    away_strength = (offense + defense + form) / 3
    
    # 2. Add home advantage
    home_strength += 5  # Fixed bonus for playing at home
    
    # 3. Determine probabilities based on strength difference
    diff = home_strength - away_strength
    
    if diff > 20:
        home_prob = 0.65  # Strong home favorite
        draw_prob = 0.20
    elif diff > 10:
        home_prob = 0.55
        draw_prob = 0.25
    elif diff > 0:
        home_prob = 0.45
        draw_prob = 0.30
    # ... more brackets
    
    away_prob = 1 - home_prob - draw_prob
    
    # 4. Convert probabilities to decimal odds with bookmaker margin
    margin = 1.05  # 5% bookmaker profit margin
    home_odds = margin / home_prob
    draw_odds = margin / draw_prob
    away_odds = margin / away_prob
```

**Example:**
```
Man City (away) vs Nottingham Forest (home)

Team Strengths:
- Forest: (68.2 + 71.5 + 65.3) / 3 + 5 (home) = 73.3
- City:   (85.5 + 82.3 + 78.9) / 3 = 82.2

Difference: 73.3 - 82.2 = -8.9 (City stronger)

Probabilities:
- Home: 35%
- Draw: 30%
- Away: 35%

Market Odds (with 5% margin):
- Home: 1.05 / 0.35 = 3.00
- Draw: 1.05 / 0.30 = 3.50
- Away: 1.05 / 0.35 = 3.00
```

**Code Location:** Lines 285-327 (function: `calculate_odds_from_stats()`)

---

## Why Not Fetch Real Bookmaker Odds?

### Limitations of Football-Data.org Free API:
- ✅ Provides: Match fixtures, results, team info
- ❌ Does NOT provide: Betting odds

### Options for Real Bookmaker Odds:

**1. Paid APIs (£££):**
- The Odds API (https://the-odds-api.com/) - $100-500/month
- Betfair API - Requires betting account
- RapidAPI Sports Odds - $50+/month

**2. Web Scraping:**
- Scrape odds from betting sites (Bet365, William Hill, etc.)
- ⚠️ Legal/ToS concerns
- ⚠️ Odds change frequently (need real-time updates)
- ⚠️ Anti-scraping measures

**3. Current Approach (Calculated):**
- ✅ Free
- ✅ Based on real match statistics
- ✅ Consistent and reproducible
- ✅ Good proxy for actual market odds
- ⚠️ Not exact bookmaker prices

---

## Data Flow Diagram

```
┌─────────────────────────────────────┐
│   Football-Data.org API             │
│   (Real EPL Match Data)             │
└────────────┬────────────────────────┘
             │
             │ Fetch matches & results
             ▼
┌─────────────────────────────────────┐
│   Calculate Team Statistics         │
│   (Offense, Defense, Form)          │
│   Based on completed matches        │
└────────────┬────────────────────────┘
             │
             │ Team ratings
             ▼
┌─────────────────────────────────────┐
│   Calculate Market Odds             │
│   - Compare team strengths          │
│   - Apply home advantage            │
│   - Convert to probabilities        │
│   - Add bookmaker margin (5%)       │
│   - Convert to decimal odds         │
└────────────┬────────────────────────┘
             │
             │ Odds for each match
             ▼
┌─────────────────────────────────────┐
│   Used in Pick Generation           │
│   - Calculate edge                  │
│   - Determine confidence            │
│   - Display to user                 │
└─────────────────────────────────────┘
```

---

## How to Integrate Real Bookmaker Odds (Future Enhancement)

If you want to use actual bookmaker odds:

### Option 1: The Odds API (Recommended)

```python
import httpx

async def fetch_real_bookmaker_odds():
    """Fetch odds from The Odds API"""
    api_key = "YOUR_API_KEY"
    url = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds/"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={
                "apiKey": api_key,
                "regions": "uk",
                "markets": "h2h",  # Head-to-head (home/draw/away)
                "oddsFormat": "decimal"
            }
        )
        
        data = response.json()
        
        # Parse odds by bookmaker
        for event in data:
            home_team = event["home_team"]
            away_team = event["away_team"]
            
            # Get average odds across multiple bookmakers
            bookmakers = event["bookmakers"]
            # Extract home/draw/away odds
```

### Option 2: Modify Existing Code

Replace the odds calculation section (lines 426-437) with:

```python
# Instead of:
h_odds, d_odds, a_odds = calculate_odds_from_stats(home_stats, away_stats)

# Use:
h_odds, d_odds, a_odds = fetch_real_odds(home_team, away_team)
# Fallback to calculated if fetch fails
if not h_odds:
    h_odds, d_odds, a_odds = calculate_odds_from_stats(home_stats, away_stats)
```

---

## Summary

| Aspect | Current Implementation |
|--------|----------------------|
| **Match Data** | ✅ Real (from Football-Data.org API) |
| **Team Statistics** | ✅ Real (calculated from actual match results) |
| **Market Odds** | ⚠️ Calculated (not from bookmakers) |
| **Accuracy** | Good proxy for real odds based on team strength |
| **Cost** | Free |
| **Limitation** | Not exact bookmaker prices (may differ by 10-20%) |

**Bottom Line:** Market odds are generated internally using a formula based on real team performance statistics. They serve as a reasonable proxy for actual bookmaker odds but are not fetched from betting sites.

---

## Files Referenced

- `/app/betgenius/backend/server.py`
  - Lines 285-327: `calculate_odds_from_stats()`
  - Lines 177-283: `calculate_team_stats_from_matches()`
  - Lines 329-464: `fetch_epl_fixtures_from_api()`

- Environment: `/app/betgenius/backend/.env`
  - `FOOTBALL_API_KEY=f9a65271eb9340c08c1b015bf304fab7`
