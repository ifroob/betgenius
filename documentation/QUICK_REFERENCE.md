# BetGenius - Real API Data Quick Reference

## What Changed?

Your BetGenius app now uses **real EPL match data** from Football-Data.org instead of mock/random data.

## Current Data Sources

### ✅ Now Using Real Data:
- **Matches**: 15 real upcoming EPL fixtures
- **Teams**: 20 EPL teams with stats calculated from actual matches
- **Historical Data**: 30 completed matches with real scores
- **Team Stats**: Derived from actual goals scored/conceded and win rates
- **Predictions**: Based on real team performance

### 📊 Data Details:
- **Offense Rating**: Calculated from average goals scored per match
- **Defense Rating**: Calculated from goals conceded (inverse)
- **Form Rating**: Based on actual win percentage
- **Match Results**: Real scores from completed games

## How to Use

### 1. View Real Matches
Just use the app normally - it automatically fetches real EPL data!

### 2. Refresh Data Button
Click "New Fixtures" in the Dashboard to fetch the latest matches from the API.

```bash
# What it does:
- Fetches latest EPL fixtures
- Updates team statistics from recent matches
- Loads upcoming games and historical results
```

### 3. Generate Predictions
All predictions now use real team data:
- Select any model (Balanced Pro, Form Hunter, etc.)
- Click "Generate Picks"
- Predictions based on actual team performance

### 4. Run Simulations
Backtesting now uses real historical matches:
- 30 completed EPL matches available
- Real scores and outcomes
- Test your models against actual results

## API Endpoints (if you want to test manually)

```bash
# Check data source status
curl http://localhost:8001/api/

# Get upcoming matches
curl http://localhost:8001/api/games

# Get team stats
curl http://localhost:8001/api/teams

# Refresh data from API
curl -X POST http://localhost:8001/api/refresh-data

# Generate picks
curl -X POST "http://localhost:8001/api/picks/generate?model_id=preset-balanced"
```

## Fallback Behavior

If the Football API is unavailable:
- ✅ App automatically uses mock data
- ✅ All features continue to work
- ✅ No errors or crashes
- ⚠️ Check logs if you want to know which source is active

## API Key

Your API key is configured in `/app/betgenius/backend/.env`:
- **Free tier** with 10 calls/minute
- Plenty for regular usage
- Automatically used on server startup and refresh

## Verification

You can verify real data is being used:

1. **Check API response**:
   ```bash
   curl http://localhost:8001/api/ | jq .data_source
   # Should return: "api"
   ```

2. **Check match data**:
   - Real team names (e.g., "Fulham FC", "Liverpool FC")
   - Real match dates (actual EPL schedule)
   - data_source field shows "api"

3. **Check backend logs**:
   ```bash
   tail /var/log/supervisor/backend.err.log
   # Look for: "Successfully loaded X games from API"
   ```

## Current Status

🟢 **LIVE - Using Real API Data**
- ✅ 15 upcoming EPL matches loaded
- ✅ 20 teams with calculated stats
- ✅ 30 historical matches for backtesting
- ✅ All predictions using real data

## What's Still Simulated?

Since this is the free API tier, some advanced features are still calculated/estimated:
- **Injury Impact**: Randomized (not in free API)
- **Weather Conditions**: Default values
- **Travel Distance**: Estimated
- **Betting Odds**: Generated based on team strength (not live odds)

For live odds, you'd need to integrate with a dedicated odds API (like The Odds API).

## Need Help?

- Check `/app/betgenius/REAL_API_MIGRATION.md` for technical details
- Check backend logs: `tail -f /var/log/supervisor/backend.err.log`
- Restart services: `sudo supervisorctl restart all`

---

**Enjoy your real EPL betting analytics! 🎯⚽**
