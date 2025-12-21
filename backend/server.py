from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="BetGenius - EPL Betting Analytics")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============ ENUMS ============
class BetStatus(str, Enum):
    PENDING = "pending"
    WON = "won"
    LOST = "lost"
    VOID = "void"

class ModelType(str, Enum):
    PRESET = "preset"
    CUSTOM = "custom"

# ============ MODELS ============
class ModelWeights(BaseModel):
    team_offense: float = Field(default=20.0, ge=0, le=100)
    team_defense: float = Field(default=20.0, ge=0, le=100)
    recent_form: float = Field(default=20.0, ge=0, le=100)
    injuries: float = Field(default=20.0, ge=0, le=100)
    home_advantage: float = Field(default=20.0, ge=0, le=100)

class BettingModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    model_type: ModelType = ModelType.CUSTOM
    weights: ModelWeights
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_active: bool = True

class BettingModelCreate(BaseModel):
    name: str
    description: str = ""
    weights: ModelWeights

class EPLTeam(BaseModel):
    name: str
    short_name: str
    offense_rating: float
    defense_rating: float
    form_rating: float
    injury_impact: float

class Game(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    home_team: str
    away_team: str
    match_date: str
    home_odds: float
    draw_odds: float
    away_odds: float
    home_team_data: Optional[dict] = None
    away_team_data: Optional[dict] = None
    result: Optional[str] = None  # "home", "draw", "away", None
    home_score: Optional[int] = None
    away_score: Optional[int] = None

class Pick(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    model_id: str
    model_name: str
    home_team: str
    away_team: str
    match_date: str
    predicted_outcome: str  # "home", "draw", "away"
    projected_home_score: float
    projected_away_score: float
    market_odds: float
    confidence_score: int  # 1-10
    edge_percentage: float
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class JournalEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    pick_id: str
    game_id: str
    model_name: str
    home_team: str
    away_team: str
    match_date: str
    predicted_outcome: str
    stake: float
    odds_taken: float
    status: BetStatus = BetStatus.PENDING
    profit_loss: float = 0.0
    result: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    settled_at: Optional[str] = None

class JournalEntryCreate(BaseModel):
    pick_id: str
    stake: float
    odds_taken: float

class SettleBetRequest(BaseModel):
    result: str  # "home", "draw", "away"

# ============ DYNAMIC DATA GENERATOR ============
import random
from datetime import timedelta

EPL_TEAMS_BASE = {
    "Arsenal": {"short": "ARS", "base_offense": 85, "base_defense": 82},
    "Manchester City": {"short": "MCI", "base_offense": 92, "base_defense": 88},
    "Liverpool": {"short": "LIV", "base_offense": 90, "base_defense": 85},
    "Chelsea": {"short": "CHE", "base_offense": 78, "base_defense": 75},
    "Manchester United": {"short": "MUN", "base_offense": 75, "base_defense": 72},
    "Tottenham": {"short": "TOT", "base_offense": 80, "base_defense": 74},
    "Newcastle": {"short": "NEW", "base_offense": 76, "base_defense": 80},
    "Brighton": {"short": "BHA", "base_offense": 72, "base_defense": 70},
    "Aston Villa": {"short": "AVL", "base_offense": 74, "base_defense": 73},
    "West Ham": {"short": "WHU", "base_offense": 68, "base_defense": 65},
    "Fulham": {"short": "FUL", "base_offense": 70, "base_defense": 68},
    "Brentford": {"short": "BRE", "base_offense": 71, "base_defense": 69},
    "Crystal Palace": {"short": "CRY", "base_offense": 66, "base_defense": 70},
    "Wolves": {"short": "WOL", "base_offense": 65, "base_defense": 72},
    "Bournemouth": {"short": "BOU", "base_offense": 67, "base_defense": 64},
    "Nottingham Forest": {"short": "NFO", "base_offense": 64, "base_defense": 71},
    "Everton": {"short": "EVE", "base_offense": 62, "base_defense": 68},
    "Leicester": {"short": "LEI", "base_offense": 69, "base_defense": 63},
    "Ipswich": {"short": "IPS", "base_offense": 58, "base_defense": 60},
    "Southampton": {"short": "SOU", "base_offense": 60, "base_defense": 58},
}

def get_randomized_teams():
    """Generate team stats with random variations for form and injuries"""
    teams = {}
    for name, base in EPL_TEAMS_BASE.items():
        # Randomize form (can swing wildly based on recent results)
        form_variation = random.randint(-15, 15)
        form = max(40, min(95, base["base_offense"] + form_variation))
        
        # Randomize injury impact (0-25%)
        injury = random.randint(0, 25)
        
        # Add slight variation to offense/defense
        offense = max(50, min(95, base["base_offense"] + random.randint(-5, 5)))
        defense = max(50, min(95, base["base_defense"] + random.randint(-5, 5)))
        
        teams[name] = {
            "short": base["short"],
            "offense": offense,
            "defense": defense,
            "form": form,
            "injury": injury
        }
    return teams

def generate_odds(home_strength: float, away_strength: float) -> tuple:
    """Generate realistic odds based on team strengths with randomness"""
    diff = home_strength - away_strength + random.uniform(-10, 10)  # Home advantage + noise
    
    # Base probabilities with variation
    if diff > 15:
        home_prob = random.uniform(0.55, 0.70)
        draw_prob = random.uniform(0.18, 0.25)
    elif diff > 5:
        home_prob = random.uniform(0.42, 0.55)
        draw_prob = random.uniform(0.22, 0.30)
    elif diff > -5:
        home_prob = random.uniform(0.32, 0.42)
        draw_prob = random.uniform(0.28, 0.35)
    elif diff > -15:
        home_prob = random.uniform(0.25, 0.35)
        draw_prob = random.uniform(0.25, 0.32)
    else:
        home_prob = random.uniform(0.15, 0.28)
        draw_prob = random.uniform(0.20, 0.28)
    
    away_prob = 1 - home_prob - draw_prob
    
    # Convert to decimal odds with bookmaker margin (5-8%)
    margin = random.uniform(1.05, 1.08)
    h_odds = round(margin / home_prob, 2)
    d_odds = round(margin / draw_prob, 2)
    a_odds = round(margin / away_prob, 2)
    
    return h_odds, d_odds, a_odds

def generate_fixtures():
    """Generate random EPL fixtures with dynamic odds"""
    team_names = list(EPL_TEAMS_BASE.keys())
    random.shuffle(team_names)
    
    fixtures = []
    teams = get_randomized_teams()
    
    # Generate 8 random fixtures
    used_teams = set()
    base_date = datetime.now(timezone.utc)
    
    kickoff_times = ["12:30", "15:00", "17:30", "20:00"]
    
    for i in range(8):
        # Pick two teams that haven't played yet
        available = [t for t in team_names if t not in used_teams]
        if len(available) < 2:
            used_teams.clear()
            available = team_names.copy()
        
        random.shuffle(available)
        home_team = available[0]
        away_team = available[1]
        used_teams.add(home_team)
        used_teams.add(away_team)
        
        # Generate match date (spread over next 7 days)
        match_date = base_date + timedelta(days=i // 2, hours=random.randint(0, 8))
        kickoff = random.choice(kickoff_times)
        date_str = f"{match_date.strftime('%Y-%m-%d')} {kickoff}"
        
        # Generate odds based on team strengths
        home_strength = teams[home_team]["offense"] + teams[home_team]["form"] - teams[home_team]["injury"]
        away_strength = teams[away_team]["offense"] + teams[away_team]["form"] - teams[away_team]["injury"]
        h_odds, d_odds, a_odds = generate_odds(home_strength, away_strength)
        
        fixtures.append({
            "home": home_team,
            "away": away_team,
            "date": date_str,
            "h_odds": h_odds,
            "d_odds": d_odds,
            "a_odds": a_odds
        })
    
    return fixtures, teams

# Generate fresh data on each server restart
MOCK_GAMES, EPL_TEAMS = generate_fixtures()

PRESET_MODELS = [
    {
        "id": "preset-balanced",
        "name": "Balanced Pro",
        "description": "Equal weighting across all factors - great for beginners",
        "model_type": "preset",
        "weights": {"team_offense": 20, "team_defense": 20, "recent_form": 20, "injuries": 20, "home_advantage": 20},
    },
    {
        "id": "preset-form-focused",
        "name": "Form Hunter",
        "description": "Emphasizes recent form and momentum",
        "model_type": "preset",
        "weights": {"team_offense": 15, "team_defense": 15, "recent_form": 40, "injuries": 10, "home_advantage": 20},
    },
    {
        "id": "preset-stats-heavy",
        "name": "Stats Machine",
        "description": "Heavy focus on offensive and defensive metrics",
        "model_type": "preset",
        "weights": {"team_offense": 35, "team_defense": 35, "recent_form": 10, "injuries": 10, "home_advantage": 10},
    },
]

# ============ HELPER FUNCTIONS ============
def calculate_team_score(team_name: str, weights: dict, is_home: bool) -> float:
    """Calculate projected score for a team based on model weights"""
    team = EPL_TEAMS.get(team_name, {})
    if not team:
        return 1.5
    
    # Normalize weights to sum to 100
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 1.5
    
    norm_weights = {k: v / total_weight for k, v in weights.items()}
    
    # Calculate base score (0-3 goals range)
    offense_contrib = (team.get("offense", 70) / 100) * norm_weights.get("team_offense", 0.2) * 3
    defense_opp_weakness = 1 - (team.get("defense", 70) / 100)  # opponent's scoring potential
    form_contrib = (team.get("form", 70) / 100) * norm_weights.get("recent_form", 0.2) * 2
    injury_penalty = (team.get("injury", 10) / 100) * norm_weights.get("injuries", 0.2)
    home_bonus = 0.3 * norm_weights.get("home_advantage", 0.2) if is_home else 0
    
    score = offense_contrib + form_contrib + home_bonus - injury_penalty
    return round(max(0.5, min(4.0, score)), 2)

def calculate_confidence(model_prob: float, market_prob: float) -> int:
    """Calculate confidence score 1-10 based on edge"""
    edge = (model_prob - market_prob) / market_prob * 100
    if edge <= 0:
        return max(1, int(5 + edge / 5))
    elif edge < 5:
        return 6
    elif edge < 10:
        return 7
    elif edge < 15:
        return 8
    elif edge < 25:
        return 9
    else:
        return 10

def calculate_outcome_probabilities(home_score: float, away_score: float) -> dict:
    """Convert projected scores to outcome probabilities"""
    diff = home_score - away_score
    
    # Simple probability model based on score difference
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

# ============ API ROUTES ============

@api_router.get("/")
async def root():
    return {"message": "BetGenius EPL API", "version": "1.0.0"}

# ---- Teams ----
@api_router.get("/teams")
async def get_teams():
    teams = []
    for name, data in EPL_TEAMS.items():
        teams.append({
            "name": name,
            "short_name": data["short"],
            "offense_rating": data["offense"],
            "defense_rating": data["defense"],
            "form_rating": data["form"],
            "injury_impact": data["injury"]
        })
    return teams

@api_router.post("/refresh-data")
async def refresh_data():
    """Regenerate all fixtures and team data"""
    global MOCK_GAMES, EPL_TEAMS
    MOCK_GAMES, EPL_TEAMS = generate_fixtures()
    return {"message": "Data refreshed", "games": len(MOCK_GAMES), "teams": len(EPL_TEAMS)}

# ---- Games ----
@api_router.get("/games")
async def get_games():
    games = []
    for i, g in enumerate(MOCK_GAMES):
        home_data = EPL_TEAMS.get(g["home"], {})
        away_data = EPL_TEAMS.get(g["away"], {})
        games.append({
            "id": f"game-{i+1}",
            "home_team": g["home"],
            "away_team": g["away"],
            "match_date": g["date"],
            "home_odds": g["h_odds"],
            "draw_odds": g["d_odds"],
            "away_odds": g["a_odds"],
            "home_team_data": home_data,
            "away_team_data": away_data,
            "result": None,
            "home_score": None,
            "away_score": None
        })
    return games

# ---- Models ----
@api_router.get("/models")
async def get_models():
    # Get preset models
    models = []
    for p in PRESET_MODELS:
        models.append({
            "id": p["id"],
            "name": p["name"],
            "description": p["description"],
            "model_type": p["model_type"],
            "weights": p["weights"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        })
    
    # Get custom models from DB
    custom_models = await db.models.find({}, {"_id": 0}).to_list(100)
    models.extend(custom_models)
    
    return models

@api_router.post("/models", status_code=201)
async def create_model(model_input: BettingModelCreate):
    model = BettingModel(
        name=model_input.name,
        description=model_input.description,
        model_type=ModelType.CUSTOM,
        weights=model_input.weights
    )
    doc = model.model_dump()
    await db.models.insert_one(doc)
    # Return the document without MongoDB's _id field
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.get("/models/{model_id}")
async def get_model(model_id: str):
    # Check presets first
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            return p
    
    # Check custom models
    model = await db.models.find_one({"id": model_id}, {"_id": 0})
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model

@api_router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    # Can't delete preset models
    if model_id.startswith("preset-"):
        raise HTTPException(status_code=400, detail="Cannot delete preset models")
    
    result = await db.models.delete_one({"id": model_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted"}

# ---- Picks (Value Finder) ----
@api_router.post("/picks/generate")
async def generate_picks(model_id: str):
    """Generate picks for all games using the specified model"""
    # Get model
    model = None
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            model = p
            break
    
    if not model:
        model = await db.models.find_one({"id": model_id}, {"_id": 0})
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    weights = model["weights"]
    picks = []
    
    for i, g in enumerate(MOCK_GAMES):
        home_score = calculate_team_score(g["home"], weights, is_home=True)
        away_score = calculate_team_score(g["away"], weights, is_home=False)
        
        probs = calculate_outcome_probabilities(home_score, away_score)
        
        # Convert market odds to implied probabilities
        market_probs = {
            "home": 1 / g["h_odds"],
            "draw": 1 / g["d_odds"],
            "away": 1 / g["a_odds"]
        }
        
        # Find best value bet
        best_outcome = max(probs.keys(), key=lambda k: probs[k] - market_probs[k])
        edge = (probs[best_outcome] - market_probs[best_outcome]) / market_probs[best_outcome] * 100
        
        market_odds = {"home": g["h_odds"], "draw": g["d_odds"], "away": g["a_odds"]}[best_outcome]
        confidence = calculate_confidence(probs[best_outcome], market_probs[best_outcome])
        
        pick = {
            "id": f"pick-{model_id}-game-{i+1}",
            "game_id": f"game-{i+1}",
            "model_id": model_id,
            "model_name": model["name"],
            "home_team": g["home"],
            "away_team": g["away"],
            "match_date": g["date"],
            "predicted_outcome": best_outcome,
            "projected_home_score": home_score,
            "projected_away_score": away_score,
            "market_odds": market_odds,
            "confidence_score": confidence,
            "edge_percentage": round(edge, 1),
            "model_probability": round(probs[best_outcome] * 100, 1),
            "market_probability": round(market_probs[best_outcome] * 100, 1),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        picks.append(pick)
    
    # Sort by confidence
    picks.sort(key=lambda x: x["confidence_score"], reverse=True)
    return picks

# ---- Journal ----
@api_router.get("/journal")
async def get_journal():
    entries = await db.journal.find({}, {"_id": 0}).to_list(100)
    return entries

@api_router.post("/journal", status_code=201)
async def create_journal_entry(entry_input: JournalEntryCreate):
    """Add a pick to the journal with stake and odds"""
    # Parse pick_id to get game info
    parts = entry_input.pick_id.split("-")
    model_id = "-".join(parts[1:-2])
    game_idx = int(parts[-1]) - 1
    
    if game_idx < 0 or game_idx >= len(MOCK_GAMES):
        raise HTTPException(status_code=400, detail="Invalid pick")
    
    game = MOCK_GAMES[game_idx]
    
    # Get model name
    model_name = "Custom Model"
    for p in PRESET_MODELS:
        if p["id"] == model_id:
            model_name = p["name"]
            break
    if model_name == "Custom Model":
        custom_model = await db.models.find_one({"id": model_id}, {"_id": 0})
        if custom_model:
            model_name = custom_model["name"]
    
    entry = JournalEntry(
        pick_id=entry_input.pick_id,
        game_id=f"game-{game_idx+1}",
        model_name=model_name,
        home_team=game["home"],
        away_team=game["away"],
        match_date=game["date"],
        predicted_outcome="home",  # Simplified - would come from pick data
        stake=entry_input.stake,
        odds_taken=entry_input.odds_taken
    )
    
    doc = entry.model_dump()
    await db.journal.insert_one(doc)
    # Return the document without MongoDB's _id field
    return {k: v for k, v in doc.items() if k != '_id'}

@api_router.patch("/journal/{entry_id}/settle")
async def settle_bet(entry_id: str, settle_request: SettleBetRequest):
    """Settle a bet with the actual result"""
    entry = await db.journal.find_one({"id": entry_id}, {"_id": 0})
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if entry["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bet already settled")
    
    # Calculate profit/loss
    won = entry["predicted_outcome"] == settle_request.result
    if won:
        profit_loss = entry["stake"] * (entry["odds_taken"] - 1)
        status = BetStatus.WON
    else:
        profit_loss = -entry["stake"]
        status = BetStatus.LOST
    
    update_data = {
        "status": status.value,
        "profit_loss": round(profit_loss, 2),
        "result": settle_request.result,
        "settled_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.journal.update_one({"id": entry_id}, {"$set": update_data})
    
    updated_entry = {**entry, **update_data}
    return updated_entry

@api_router.delete("/journal/{entry_id}")
async def delete_journal_entry(entry_id: str):
    result = await db.journal.delete_one({"id": entry_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return {"message": "Entry deleted"}

# ---- Stats ----
@api_router.get("/stats")
async def get_stats():
    """Get overall betting statistics"""
    entries = await db.journal.find({}, {"_id": 0}).to_list(1000)
    
    total_bets = len(entries)
    pending_bets = len([e for e in entries if e.get("status") == "pending"])
    won_bets = len([e for e in entries if e.get("status") == "won"])
    lost_bets = len([e for e in entries if e.get("status") == "lost"])
    
    total_staked = sum(e.get("stake", 0) for e in entries if e.get("status") != "pending")
    total_profit = sum(e.get("profit_loss", 0) for e in entries)
    
    win_rate = (won_bets / (won_bets + lost_bets) * 100) if (won_bets + lost_bets) > 0 else 0
    roi = (total_profit / total_staked * 100) if total_staked > 0 else 0
    
    return {
        "total_bets": total_bets,
        "pending_bets": pending_bets,
        "won_bets": won_bets,
        "lost_bets": lost_bets,
        "win_rate": round(win_rate, 1),
        "total_staked": round(total_staked, 2),
        "total_profit": round(total_profit, 2),
        "roi": round(roi, 1)
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
