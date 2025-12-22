# BetGenius - EPL Sports Betting Analytics MVP

## Original Problem Statement
Design a Minimum Viable Product (MVP) for a sports betting analytics app that allows users to:
1. **Model Engine ("Create")** - Build betting models with 5 weighted inputs
2. **Value Finder ("Pick")** - Identify value bets by comparing projected vs market odds
3. **Journaling Loop ("Journal")** - Track bet lifecycle from pick to result

## User Requirements
- English Premier League (EPL) focus
- Mock/simulated data (no live API)
- No authentication
- No payment/paywall (skipped for MVP)
- Dark theme

## Architecture Completed

### Backend (FastAPI + MongoDB)
- `/api/models` - CRUD for betting models (preset + custom)
- `/api/games` - 8 mock EPL fixtures with realistic odds
- `/api/picks/generate` - Calculate picks using model weights
- `/api/journal` - Bet tracking with settle functionality
- `/api/stats` - Aggregate betting statistics

### Frontend (React + Tailwind + Shadcn)
- **Dashboard** - Stats overview, active models, upcoming matches, recent bets
- **Models Tab** - 3 preset models + custom model builder with 5 sliders
- **Value Finder** - Pick generator with confidence scores (1-10)
- **Journal** - Bet lifecycle management with settle/delete

### Model Logic Implementation
- 5 weighted inputs: Team Offense, Team Defense, Recent Form, Injuries, Home Advantage
- Projected score calculation based on weights + team ratings
- Confidence score (1-10) based on edge vs market odds
- P/L calculation on bet settlement

## Next Action Items

### Phase 2 Features
1. Real-time odds integration (The Odds API)
2. Historical backtesting with performance graphs
3. User authentication with saved models/journal
4. Stripe payment for premium features

### Enhancement Suggestions
1. Add model performance tracking over time
2. Implement bankroll management (Kelly Criterion)
3. Multi-sport expansion (NBA, NFL)
4. Push notifications for high-confidence picks
5. Social features - share picks with friends

## Deferred (Paywall Triggers - Future)
- Trigger A: Multiple custom models (currently unlimited)
- Trigger B: Advanced inputs (xG, possession stats)
- Trigger C: Historical backtesting beyond 1 week
