# BetGenius - EPL Betting Analytics MVP

## Functional Blueprint

A sports betting analytics platform that allows users to build prediction models, identify value bets, and track betting performance.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │ Dashboard │ │  Models   │ │Value Finder│ │  Journal  │       │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       BACKEND (FastAPI)                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Model Engine │ │ Value Finder │ │   Journal    │            │
│  │  /api/models │ │ /api/picks   │ │ /api/journal │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                              │                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │           Data Generator (Randomized)            │          │
│  │   Teams → Fixtures → Odds → Picks Calculation    │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE (MongoDB)                        │
│     models (custom)  │  journal (bets)  │  stats (aggregated)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Modules

### 2.1 Model Engine ("Create")

**Purpose:** Allow users to build betting prediction models by assigning weights to key factors.

#### Input Factors (5 Core Inputs)

| Factor | Description | Weight Range |
|--------|-------------|--------------|
| Team Offense | Attacking capability, goals scored | 0-100% |
| Team Defense | Defensive solidity, goals conceded | 0-100% |
| Recent Form | Performance in last 5 matches | 0-100% |
| Injuries | Squad availability impact | 0-100% |
| Home Advantage | Home vs away performance boost | 0-100% |

#### Model Types

**Preset Models** (Admin-provided, read-only):
- **Balanced Pro**: Equal 20% weighting across all factors
- **Form Hunter**: Heavy form emphasis (40% form, 20% home, 15% off/def, 10% injuries)
- **Stats Machine**: Pure statistics (35% offense, 35% defense, 10% others)

**Custom Models** (User-created):
- User sets name and adjusts 5 sliders
- Total weight can be any value (normalized during calculation)
- Stored in MongoDB, can be deleted

#### Projected Score Calculation

```python
def calculate_team_score(team, weights, is_home):
    # Normalize weights to sum to 1.0
    norm_weights = normalize(weights)
    
    # Calculate score components (0-4 goal range)
    offense_contrib = (team.offense / 100) * norm_weights.offense * 3
    form_contrib = (team.form / 100) * norm_weights.form * 2
    injury_penalty = (team.injury / 100) * norm_weights.injuries
    home_bonus = 0.3 * norm_weights.home if is_home else 0
    
    score = offense_contrib + form_contrib + home_bonus - injury_penalty
    return clamp(score, 0.5, 4.0)
```

---

### 2.2 Value Finder ("Pick")

**Purpose:** Identify betting opportunities where the model's prediction differs from market odds.

#### Process Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Select Model │ ──▶ │ Calculate   │ ──▶ │ Compare to  │
│             │     │ Projections │     │ Market Odds │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                    ┌─────────────┐     ┌──────▼──────┐
                    │ Rank by     │ ◀── │ Calculate   │
                    │ Confidence  │     │ Edge %      │
                    └─────────────┘     └─────────────┘
```

#### Edge Calculation

```python
# Convert projected scores to outcome probabilities
def scores_to_probabilities(home_score, away_score):
    diff = home_score - away_score
    
    if diff > 0.8:      # Strong home favorite
        home_prob = 0.55 + (diff * 0.1)  # up to 85%
    elif diff < -0.8:   # Strong away favorite
        away_prob = 0.55 + (abs(diff) * 0.1)
    else:               # Close match
        draw_prob = 0.30
        home_prob = 0.35 + (diff * 0.1)
    
    return {home, draw, away}

# Compare to market
market_prob = 1 / market_odds  # e.g., odds 2.0 = 50% implied
model_prob = calculated_probability

edge = (model_prob - market_prob) / market_prob * 100
```

#### Confidence Score (1-10)

| Edge % | Confidence | Interpretation |
|--------|------------|----------------|
| ≤ 0%   | 1-5        | No value / Against model |
| 1-5%   | 6          | Slight edge |
| 5-10%  | 7          | Moderate edge |
| 10-15% | 8          | Good value |
| 15-25% | 9          | Strong value |
| > 25%  | 10         | Exceptional value |

#### Pick Output

Each pick contains:
- Match details (teams, date)
- Projected score (e.g., 2.1 - 1.4)
- Predicted outcome (HOME / DRAW / AWAY)
- Market odds for that outcome
- Edge percentage (+12.5%)
- Confidence score (8/10)

---

### 2.3 Journal ("Track")

**Purpose:** Record bets and track performance over time.

#### Bet Lifecycle

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  PICK    │ ─▶ │  STAKE   │ ─▶ │ PENDING  │ ─▶ │ SETTLED  │
│ Selected │    │ Entered  │    │ (wait)   │    │ WON/LOST │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

#### Journal Entry Data

```json
{
  "id": "uuid",
  "pick_id": "reference to original pick",
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "predicted_outcome": "home",
  "stake": 100.00,
  "odds_taken": 2.40,
  "status": "pending | won | lost",
  "profit_loss": 0.00,
  "result": null,
  "created_at": "2024-12-21T15:00:00Z",
  "settled_at": null
}
```

#### Profit/Loss Calculation

```python
def settle_bet(entry, actual_result):
    if entry.predicted_outcome == actual_result:
        # WIN: Profit = Stake × (Odds - 1)
        profit = entry.stake * (entry.odds_taken - 1)
        status = "won"
    else:
        # LOSS: Lose entire stake
        profit = -entry.stake
        status = "lost"
    
    return profit, status
```

#### Performance Metrics

| Metric | Formula |
|--------|---------|
| Win Rate | Won Bets / Total Settled Bets × 100 |
| ROI | Total Profit / Total Staked × 100 |
| Total P/L | Sum of all profit_loss values |

---

## 3. Team Rating System

### Current Implementation (Hardcoded Base + Randomization)

Teams have **base ratings** reflecting general quality tier:

| Tier | Teams | Base Offense | Base Defense |
|------|-------|--------------|--------------|
| Elite | Man City, Liverpool | 90-92 | 85-88 |
| Contenders | Arsenal, Tottenham | 80-85 | 74-82 |
| Top Half | Chelsea, Newcastle, Villa, Brighton | 72-78 | 70-80 |
| Mid-table | Fulham, Brentford, Wolves, Bournemouth | 65-71 | 64-72 |
| Lower | Everton, Leicester, Forest | 62-69 | 63-71 |
| Relegation | Ipswich, Southampton | 58-60 | 58-60 |

### Dynamic Randomization (Per Refresh)

```python
# On each "New Fixtures" refresh:
offense = base_offense + random(-5, +5)
defense = base_defense + random(-5, +5)
form = base_offense + random(-15, +15)  # High variance
injury = random(0, 25)  # 0-25% impact
```

### Odds Generation

```python
def generate_odds(home_strength, away_strength):
    # Calculate strength differential
    diff = home_strength - away_strength + random(-10, +10)
    
    # Map to probabilities
    if diff > 15:    home_prob = 0.55-0.70
    elif diff > 5:   home_prob = 0.42-0.55
    elif diff > -5:  home_prob = 0.32-0.42  # Close match
    elif diff > -15: home_prob = 0.25-0.35
    else:            home_prob = 0.15-0.28  # Away favorite
    
    # Convert to decimal odds with 5-8% bookmaker margin
    odds = margin / probability
```

---

## 4. API Reference

### Models

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models` | List all models (preset + custom) |
| POST | `/api/models` | Create custom model |
| GET | `/api/models/{id}` | Get single model |
| DELETE | `/api/models/{id}` | Delete custom model |

### Games & Picks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/games` | List current fixtures |
| GET | `/api/teams` | List all teams with ratings |
| POST | `/api/picks/generate?model_id={id}` | Generate picks using model |
| POST | `/api/refresh-data` | Regenerate all fixtures |

### Journal

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/journal` | List all bet entries |
| POST | `/api/journal` | Add bet to journal |
| PATCH | `/api/journal/{id}/settle` | Settle bet with result |
| DELETE | `/api/journal/{id}` | Delete entry |
| GET | `/api/stats` | Get aggregate statistics |

---

## 5. Data Flow Example

### Complete User Journey

```
1. USER visits Dashboard
   └─▶ API: GET /api/games, /api/models, /api/stats
   └─▶ Display: 8 fixtures, 3 preset models, performance stats

2. USER clicks "Use" on "Form Hunter" model
   └─▶ Navigate to Value Finder tab
   └─▶ API: POST /api/picks/generate?model_id=preset-form-focused
   └─▶ Backend calculates projections for all 8 games
   └─▶ Display: Picks sorted by confidence (highest first)

3. USER sees Arsenal vs Chelsea with Confidence 8/10
   └─▶ Click "Add to Journal"
   └─▶ Enter: Stake $50, Odds 2.40
   └─▶ API: POST /api/journal
   └─▶ Entry created with status="pending"

4. MATCH completes, Arsenal wins
   └─▶ USER clicks "Settle" on Journal tab
   └─▶ Select result: "Home Win"
   └─▶ API: PATCH /api/journal/{id}/settle
   └─▶ Calculation: $50 × (2.40 - 1) = $70 profit
   └─▶ Entry updated: status="won", profit_loss=70.00

5. Dashboard stats update
   └─▶ Total Bets: 1, Won: 1, Win Rate: 100%, P/L: +$70
```

---

## 6. Future Enhancements

### Phase 2: Real Data Integration
- [ ] Connect to Football-Data.org or API-Football
- [ ] Real-time odds from The Odds API
- [ ] Auto-settle bets when match results come in

### Phase 3: Advanced Features
- [ ] Historical backtesting with charts
- [ ] Bankroll management (Kelly Criterion)
- [ ] User authentication & saved preferences

### Phase 4: Monetization (Paywall Triggers)
- [ ] Trigger A: Limit to 1 custom model (free tier)
- [ ] Trigger B: Lock advanced inputs (xG, possession)
- [ ] Trigger C: Limit backtest history to 7 days

---

## 7. Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Tailwind CSS, Shadcn/UI |
| Backend | FastAPI (Python), Pydantic |
| Database | MongoDB (Motor async driver) |
| Styling | Dark "Neon Quant" theme |
| Fonts | Chivo (headings), JetBrains Mono (data) |
