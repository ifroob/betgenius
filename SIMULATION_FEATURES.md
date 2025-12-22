# 🎯 BetGenius Simulation & Enhanced Model Features

## Overview
BetGenius now includes powerful simulation/backtesting capabilities and flexible model structures to help you validate and optimize your betting strategies before risking real money.

---

## ✨ New Features

### 1. **Flexible/Unstructured Model Weights**
**What Changed:**
- Models now accept ANY custom factors you want to add
- No longer limited to the 11 predefined factors
- Weights are stored as key-value pairs allowing unlimited extensibility

**Why It Matters:**
- Add your own unique factors (e.g., "manager_experience", "crowd_pressure", "player_suspensions")
- Remove factors you don't care about
- Dynamically adjust as new betting insights emerge

**Technical Details:**
```python
# Old: Fixed 11 factors
class ModelWeights(BaseModel):
    team_offense: float = 12.0
    team_defense: float = 12.0
    # ... 9 more fixed fields

# New: Flexible factors
class ModelWeights(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Accepts any key-value pairs!
```

---

### 2. **Model Simulation & Backtesting**

#### **What Is It?**
Run your betting models against 20 historical EPL games with known results to test accuracy before using them for real predictions.

#### **Key Metrics Provided:**
- **Overall Accuracy**: % of correct predictions
- **ROI (Return on Investment)**: Simulated profit/loss percentage
- **Net Profit/Loss**: Dollar amount (assuming $10 per bet)
- **Confidence Breakdown**: Accuracy by confidence level (1-10)
- **Outcome Breakdown**: Accuracy for home/draw/away predictions
- **Game-by-Game Details**: See each prediction vs actual result

#### **How to Use:**
1. Navigate to the **Simulation** tab
2. Select a model from the dropdown
3. Click "Run Simulation"
4. Analyze the results to validate your model's performance

#### **Example Results:**
```json
{
  "model_name": "Balanced Pro",
  "total_games": 20,
  "accuracy_percentage": 30.0,
  "simulated_roi": 28.8,
  "net_profit": 57.6,
  "confidence_breakdown": {
    "10": {"total": 15, "correct": 4, "accuracy": 26.7},
    "9": {"total": 2, "correct": 1, "accuracy": 50.0},
    "8": {"total": 3, "correct": 0, "accuracy": 0.0}
  }
}
```

---

### 3. **Historical Games Database**

**What's New:**
- 20 pre-generated historical games with completed results
- Mock data includes realistic outcomes based on team strengths
- Games are regenerated on each server restart for variety

**Data Structure:**
Each historical game includes:
- Teams, date, odds
- **Completed result** (home/draw/away)
- **Final score**
- All factor data (form, injuries, rest days, etc.)

---

### 4. **Public API Integration** (Football-Data.org)

#### **Setup (Optional):**
To fetch real EPL fixtures and results:

1. Register for a free API key at: https://www.football-data.org/client/register
2. Add to `/app/betgenius/backend/.env`:
   ```
   FOOTBALL_API_KEY=your_api_key_here
   ```
3. Restart backend: `supervisorctl restart backend`

#### **Features:**
- Fetches real EPL fixtures (scheduled and finished)
- Includes actual match results when available
- Automatically mapped to BetGenius game format
- Can be filtered by data source (mock vs api)

#### **API Usage:**
```bash
# Get upcoming games only (default)
GET /api/games

# Get with historical games
GET /api/games?include_historical=true

# Filter by source
GET /api/games?source=api        # Only API data
GET /api/games?source=mock       # Only mock data
GET /api/games?source=all        # Both (default)
```

---

## 🔧 API Reference

### **New Endpoints**

#### **1. POST /api/simulate**
Run backtesting simulation on a model

**Request:**
```json
{
  "model_id": "preset-balanced",
  "game_ids": ["hist-1", "hist-2"],  // Optional: specific games
  "min_confidence": 7                 // Optional: filter by confidence
}
```

**Response:**
```json
{
  "model_id": "preset-balanced",
  "model_name": "Balanced Pro",
  "total_games": 20,
  "correct_predictions": 6,
  "accuracy_percentage": 30.0,
  "confidence_breakdown": {...},
  "outcome_breakdown": {...},
  "simulated_roi": 28.8,
  "average_odds": 2.4,
  "total_stake": 200,
  "total_return": 257.6,
  "net_profit": 57.6,
  "predictions": [...]  // Detailed game-by-game results
}
```

#### **2. GET /api/games (Enhanced)**
Fetch games with filtering options

**Query Parameters:**
- `include_historical`: boolean (default: false)
- `source`: "mock" | "api" | "all" (default: "all")

**Response:**
```json
[
  {
    "id": "game-1",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "match_date": "2025-12-22 15:00",
    "home_odds": 1.85,
    "draw_odds": 3.50,
    "away_odds": 4.20,
    "is_completed": false,
    "data_source": "mock",
    "result": null,
    "home_score": null,
    "away_score": null
  }
]
```

---

## 🎨 UI Changes

### **New Simulation Tab**
Located between "Value Finder" and "Journal"

**Features:**
- Model selector dropdown
- Run simulation button with loading state
- Results dashboard with 4 key metrics cards
- Confidence level breakdown (visual grid)
- Outcome type breakdown (home/draw/away)
- Scrollable game-by-game prediction details
- Color-coded correct/incorrect predictions

**Visual Design:**
- Green for correct predictions
- Red for incorrect predictions
- Confidence badges (1-10 scale)
- Real-time odds and scores display

---

## 📊 Use Cases

### **1. Model Validation**
- Build a custom model
- Run simulation to see 20-game performance
- Tweak weights based on results
- Re-simulate until accuracy improves

### **2. Compare Strategies**
- Test "Balanced Pro" vs "Form Hunter" vs your custom model
- Compare accuracy, ROI, and confidence calibration
- Choose the best performer

### **3. Confidence Calibration**
- Check if your high-confidence picks (8-10) actually win more
- Adjust bet sizing based on confidence accuracy

### **4. Risk Management**
- See simulated ROI before betting real money
- Identify models with positive expected value
- Avoid models with negative backtested returns

---

## 🚀 Quick Start Guide

### **Run Your First Simulation:**

1. **Access the App:**
   - Frontend: http://localhost:3000
   - Backend: http://localhost:8001

2. **Navigate to Simulation Tab:**
   - Click "Simulation" in the top navigation

3. **Select a Model:**
   - Choose from "Balanced Pro", "Form Hunter", "Stats Machine"
   - Or create a custom model first in the Models tab

4. **Run Simulation:**
   - Click "Run Simulation" button
   - Wait 1-2 seconds for results

5. **Analyze Results:**
   - Check overall accuracy (aim for >40% for value)
   - Review ROI (positive = profitable strategy)
   - Examine confidence breakdown (higher confidence should = higher accuracy)
   - Review game-by-game to understand failure patterns

6. **Iterate:**
   - Go to Models tab
   - Adjust weights based on insights
   - Re-run simulation
   - Repeat until optimal

---

## 🧪 Testing

### **Backend Tests:**
```bash
# Test simulation endpoint
curl -X POST http://localhost:8001/api/simulate \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-balanced"}'

# Test games with historical
curl "http://localhost:8001/api/games?include_historical=true"

# Count completed games
curl "http://localhost:8001/api/games?include_historical=true" | \
  jq '[.[] | select(.is_completed == true)] | length'
```

### **Frontend Tests:**
1. Open http://localhost:3000
2. Navigate to Simulation tab
3. Select "Balanced Pro"
4. Click "Run Simulation"
5. Verify results display correctly
6. Try different models

---

## 🔐 Environment Variables

### **Backend (.env):**
```bash
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
CORS_ORIGINS="*"

# Optional: Real EPL data
FOOTBALL_API_KEY=your_api_key_here
```

### **Frontend (.env):**
```bash
REACT_APP_BACKEND_URL=https://bet-genius-31.preview.emergentagent.com
WDS_SOCKET_PORT=443
ENABLE_HEALTH_CHECK=false
```

---

## 📈 Performance Notes

- **Simulation Speed**: ~1-2 seconds for 20 games
- **API Rate Limits**: Football-Data.org free tier = 10 requests/minute
- **Mock Data**: Regenerates on server restart for variety
- **Historical Games**: 20 games stored in memory (lightweight)

---

## 🛠️ Technical Architecture

### **Backend Structure:**
```
/app/betgenius/backend/
├── server.py               # Main FastAPI app
│   ├── ModelWeights        # Flexible Pydantic model
│   ├── SimulationRequest   # Simulation input schema
│   ├── SimulationResult    # Simulation output schema
│   ├── generate_historical_games()   # Mock data generator
│   ├── fetch_epl_fixtures_from_api() # Real API integration
│   └── /api/simulate       # Backtesting endpoint
└── .env                    # Config
```

### **Frontend Structure:**
```
/app/betgenius/frontend/src/
├── App.js                  # Main component
│   ├── SimulationTab       # New tab content
│   ├── runSimulation()     # API call function
│   └── simulationResults   # State management
└── components/ui/          # Reusable UI components
```

---

## 🎯 Future Enhancements

### **Planned Features:**
1. **Multi-Model Comparison**: Run multiple models side-by-side
2. **Custom Date Ranges**: Select specific historical periods
3. **Export Results**: Download simulation reports as CSV/PDF
4. **Advanced Filters**: Filter by team, competition, odds range
5. **Live API Sync**: Auto-update with latest EPL results
6. **Confidence Thresholds**: Only simulate high-confidence picks
7. **Bet Sizing Strategies**: Test Kelly Criterion, flat stakes, etc.

---

## 🐛 Troubleshooting

### **Simulation Returns 0 Games:**
- Check if historical games exist: `curl http://localhost:8001/api/games?include_historical=true`
- Restart backend: `supervisorctl restart backend`

### **API Data Not Loading:**
- Verify `FOOTBALL_API_KEY` in backend/.env
- Check API rate limits (10/min for free tier)
- Review logs: `tail -f /var/log/supervisor/backend.err.log`

### **Frontend Not Updating:**
- Clear browser cache
- Check console for errors (F12)
- Restart frontend: `supervisorctl restart frontend`

---

## 📚 Resources

- **Football-Data.org API Docs**: https://www.football-data.org/documentation/api
- **BetGenius Docs**: See `/app/betgenius/documentation/` folder
- **Support**: Check README.md for contact info

---

## 🏆 Best Practices

1. **Always Simulate First**: Never use a model without backtesting
2. **Aim for 40%+ Accuracy**: Below this, market odds are likely better
3. **Check ROI**: Accuracy alone doesn't guarantee profit
4. **Trust Confidence Levels**: Use them for bet sizing
5. **Iterate**: Refine models based on simulation insights
6. **Diversify**: Test multiple models, use the best performers
7. **Stay Disciplined**: Don't bet without positive simulated ROI

---

**Built with:**
- FastAPI (Backend)
- React + Tailwind (Frontend)
- MongoDB (Database)
- Football-Data.org API (Real EPL data)

**Version:** 2.0 with Simulation
**Last Updated:** December 2025
