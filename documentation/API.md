# BetGenius API Reference

Complete REST API documentation for the BetGenius backend.

**Base URL**: `http://localhost:8001/api`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Models API](#models-api)
3. [Games API](#games-api)
4. [Picks API](#picks-api)
5. [Journal API](#journal-api)
6. [Statistics API](#statistics-api)
7. [Data Models](#data-models)
8. [Error Responses](#error-responses)

---

## Authentication

**Status**: No authentication required for MVP.

All endpoints are publicly accessible. Future versions will implement JWT-based authentication.

---

## Models API

Manage betting prediction models (preset and custom).

### List All Models

```http
GET /api/models
```

**Response**: `200 OK`
```json
[
  {
    "id": "preset-balanced",
    "name": "Balanced Pro",
    "description": "Equal 20% weighting across all factors",
    "model_type": "preset",
    "weights": {
      "team_offense": 20.0,
      "team_defense": 20.0,
      "recent_form": 20.0,
      "injuries": 20.0,
      "home_advantage": 20.0
    },
    "created_at": "2024-01-01T00:00:00Z",
    "is_active": true
  }
]
```

### Create Custom Model

```http
POST /api/models
Content-Type: application/json
```

**Request Body**:
```json
{
  "name": "My Custom Model",
  "description": "Heavy form emphasis",
  "weights": {
    "team_offense": 15.0,
    "team_defense": 15.0,
    "recent_form": 40.0,
    "injuries": 10.0,
    "home_advantage": 20.0
  }
}
```

**Response**: `201 Created`
```json
{
  "id": "abc-123-def-456",
  "name": "My Custom Model",
  "description": "Heavy form emphasis",
  "model_type": "custom",
  "weights": { /* as sent */ },
  "created_at": "2024-12-21T15:30:00Z",
  "is_active": true
}
```

### Get Single Model

```http
GET /api/models/{model_id}
```

**Response**: `200 OK` or `404 Not Found`

### Delete Model

```http
DELETE /api/models/{model_id}
```

**Response**: `200 OK`
```json
{
  "message": "Model deleted successfully"
}
```

**Note**: Preset models cannot be deleted.

---

## Games API

Retrieve current fixtures and team data.

### List Current Fixtures

```http
GET /api/games
```

**Response**: `200 OK`
```json
[
  {
    "id": "game-123",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "match_date": "2024-12-22T15:00:00Z",
    "home_odds": 2.10,
    "draw_odds": 3.40,
    "away_odds": 3.50,
    "home_team_data": {
      "name": "Arsenal",
      "short_name": "ARS",
      "offense_rating": 87.3,
      "defense_rating": 84.1,
      "form_rating": 82.5,
      "injury_impact": 8.2
    },
    "away_team_data": { /* similar structure */ },
    "result": null,
    "home_score": null,
    "away_score": null
  }
]
```

### List All Teams

```http
GET /api/teams
```

**Response**: `200 OK`
```json
[
  {
    "name": "Arsenal",
    "short_name": "ARS",
    "offense_rating": 87.3,
    "defense_rating": 84.1,
    "form_rating": 82.5,
    "injury_impact": 8.2
  }
]
```

### Refresh Fixtures

```http
POST /api/refresh-data
```

Regenerates all fixtures with new randomized team stats.

**Response**: `200 OK`
```json
{
  "message": "Data refreshed successfully",
  "games_count": 8
}
```

---

## Picks API

Generate betting picks using prediction models.

### Generate Picks

```http
POST /api/picks/generate?model_id={model_id}
```

**Query Parameters**:
- `model_id` (required): ID of the model to use

**Response**: `200 OK`
```json
[
  {
    "id": "pick-789",
    "game_id": "game-123",
    "model_id": "preset-balanced",
    "model_name": "Balanced Pro",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "match_date": "2024-12-22T15:00:00Z",
    "predicted_outcome": "home",
    "projected_home_score": 2.3,
    "projected_away_score": 1.4,
    "market_odds": 2.10,
    "confidence_score": 8,
    "edge_percentage": 12.5,
    "created_at": "2024-12-21T15:45:00Z"
  }
]
```

**Picks are sorted by confidence score (highest first).**

---

## Journal API

Track betting journal entries.

### List All Journal Entries

```http
GET /api/journal
```

**Response**: `200 OK`
```json
[
  {
    "id": "entry-456",
    "pick_id": "pick-789",
    "game_id": "game-123",
    "model_name": "Balanced Pro",
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "match_date": "2024-12-22T15:00:00Z",
    "predicted_outcome": "home",
    "stake": 100.0,
    "odds_taken": 2.10,
    "status": "pending",
    "profit_loss": 0.0,
    "result": null,
    "created_at": "2024-12-21T15:50:00Z",
    "settled_at": null
  }
]
```

### Add Journal Entry

```http
POST /api/journal
Content-Type: application/json
```

**Request Body**:
```json
{
  "pick_id": "pick-789",
  "stake": 100.0,
  "odds_taken": 2.10
}
```

**Response**: `201 Created`
```json
{
  "id": "entry-456",
  "pick_id": "pick-789",
  /* ... full entry data ... */
  "status": "pending"
}
```

### Settle Bet

```http
PATCH /api/journal/{entry_id}/settle
Content-Type: application/json
```

**Request Body**:
```json
{
  "result": "home"  // "home", "draw", or "away"
}
```

**Response**: `200 OK`
```json
{
  "id": "entry-456",
  "status": "won",
  "profit_loss": 110.0,
  "result": "home",
  "settled_at": "2024-12-22T17:00:00Z"
}
```

**Profit/Loss Calculation**:
- **Win**: `stake × (odds - 1)`
- **Loss**: `-stake`

### Delete Journal Entry

```http
DELETE /api/journal/{entry_id}
```

**Response**: `200 OK`
```json
{
  "message": "Entry deleted successfully"
}
```

---

## Statistics API

Get aggregate betting statistics.

### Get Stats

```http
GET /api/stats
```

**Response**: `200 OK`
```json
{
  "total_bets": 25,
  "won_bets": 15,
  "lost_bets": 8,
  "pending_bets": 2,
  "win_rate": 65.22,
  "total_staked": 2500.0,
  "total_profit_loss": 425.50,
  "roi": 17.02,
  "average_odds": 2.45
}
```

**Metrics Explained**:
- `win_rate`: (won_bets / settled_bets) × 100
- `roi`: (total_profit_loss / total_staked) × 100
- `settled_bets`: won_bets + lost_bets

---

## Data Models

### ModelWeights

```typescript
interface ModelWeights {
  team_offense: number;    // 0-100
  team_defense: number;    // 0-100
  recent_form: number;     // 0-100
  injuries: number;        // 0-100
  home_advantage: number;  // 0-100
}
```

### BettingModel

```typescript
interface BettingModel {
  id: string;
  name: string;
  description: string;
  model_type: "preset" | "custom";
  weights: ModelWeights;
  created_at: string;  // ISO 8601
  is_active: boolean;
}
```

### Game

```typescript
interface Game {
  id: string;
  home_team: string;
  away_team: string;
  match_date: string;  // ISO 8601
  home_odds: number;
  draw_odds: number;
  away_odds: number;
  home_team_data: TeamData;
  away_team_data: TeamData;
  result: "home" | "draw" | "away" | null;
  home_score: number | null;
  away_score: number | null;
}
```

### Pick

```typescript
interface Pick {
  id: string;
  game_id: string;
  model_id: string;
  model_name: string;
  home_team: string;
  away_team: string;
  match_date: string;
  predicted_outcome: "home" | "draw" | "away";
  projected_home_score: number;
  projected_away_score: number;
  market_odds: number;
  confidence_score: number;  // 1-10
  edge_percentage: number;
  created_at: string;
}
```

### JournalEntry

```typescript
interface JournalEntry {
  id: string;
  pick_id: string;
  game_id: string;
  model_name: string;
  home_team: string;
  away_team: string;
  match_date: string;
  predicted_outcome: "home" | "draw" | "away";
  stake: number;
  odds_taken: number;
  status: "pending" | "won" | "lost" | "void";
  profit_loss: number;
  result: "home" | "draw" | "away" | null;
  created_at: string;
  settled_at: string | null;
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|--------|
| `200` | Success | Request completed successfully |
| `201` | Created | Resource created successfully |
| `400` | Bad Request | Invalid input data |
| `404` | Not Found | Resource does not exist |
| `422` | Validation Error | Request body validation failed |
| `500` | Server Error | Internal server error |

### Example Error Responses

**404 Not Found**:
```json
{
  "detail": "Model not found"
}
```

**422 Validation Error**:
```json
{
  "detail": [
    {
      "loc": ["body", "stake"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

---

## Rate Limiting

**Status**: No rate limiting in MVP.

Future versions will implement rate limiting:
- 100 requests per minute per IP
- 1000 requests per hour per IP

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

These interfaces allow you to:
- Browse all endpoints
- Test API calls directly
- View request/response schemas
- Try out authentication

---

## Example Usage

### Using curl

```bash
# Get all models
curl http://localhost:8001/api/models

# Create custom model
curl -X POST http://localhost:8001/api/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Form Hunter",
    "weights": {
      "team_offense": 15,
      "team_defense": 15,
      "recent_form": 40,
      "injuries": 10,
      "home_advantage": 20
    }
  }'

# Generate picks
curl -X POST "http://localhost:8001/api/picks/generate?model_id=preset-balanced"

# Add to journal
curl -X POST http://localhost:8001/api/journal \
  -H "Content-Type: application/json" \
  -d '{
    "pick_id": "pick-789",
    "stake": 100,
    "odds_taken": 2.10
  }'

# Settle bet
curl -X PATCH http://localhost:8001/api/journal/entry-456/settle \
  -H "Content-Type: application/json" \
  -d '{"result": "home"}'

# Get stats
curl http://localhost:8001/api/stats
```

### Using JavaScript (Axios)

```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8001/api';

// Get all models
const models = await axios.get(`${API_BASE}/models`);

// Create custom model
const newModel = await axios.post(`${API_BASE}/models`, {
  name: 'Form Hunter',
  weights: {
    team_offense: 15,
    team_defense: 15,
    recent_form: 40,
    injuries: 10,
    home_advantage: 20
  }
});

// Generate picks
const picks = await axios.post(
  `${API_BASE}/picks/generate?model_id=preset-balanced`
);

// Add to journal
const entry = await axios.post(`${API_BASE}/journal`, {
  pick_id: 'pick-789',
  stake: 100,
  odds_taken: 2.10
});

// Settle bet
const settled = await axios.patch(
  `${API_BASE}/journal/entry-456/settle`,
  { result: 'home' }
);

// Get stats
const stats = await axios.get(`${API_BASE}/stats`);
```

---

<div align="center">
  <p>For more details, see <a href="./DOCUMENTATION.md">DOCUMENTATION.md</a></p>
</div>
