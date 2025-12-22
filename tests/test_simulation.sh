#!/bin/bash

# BetGenius Simulation Test Script
# This script demonstrates the new simulation/backtesting features

echo "🎯 BetGenius Simulation Test Suite"
echo "===================================="
echo ""

# Base URL
API="http://localhost:8001/api"

# Test 1: Get all models
echo "1️⃣  Fetching available models..."
curl -s "$API/models" | jq '[.[] | {id, name, type: .model_type}]'
echo ""

# Test 2: Get historical games count
echo "2️⃣  Checking historical games..."
HIST_COUNT=$(curl -s "$API/games?include_historical=true" | jq '[.[] | select(.is_completed == true)] | length')
echo "✅ Found $HIST_COUNT completed historical games"
echo ""

# Test 3: Run simulation on Balanced Pro
echo "3️⃣  Running simulation: Balanced Pro"
curl -s -X POST "$API/simulate" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-balanced"}' | jq '{
    model: .model_name,
    games: .total_games,
    correct: .correct_predictions,
    accuracy: .accuracy_percentage,
    roi: .simulated_roi,
    profit: .net_profit,
    best_confidence_level: (.confidence_breakdown | to_entries | max_by(.value.accuracy) | .key)
  }'
echo ""

# Test 4: Run simulation on Form Hunter
echo "4️⃣  Running simulation: Form Hunter"
curl -s -X POST "$API/simulate" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-form-focused"}' | jq '{
    model: .model_name,
    games: .total_games,
    accuracy: .accuracy_percentage,
    roi: .simulated_roi,
    profit: .net_profit
  }'
echo ""

# Test 5: Run simulation on Stats Machine
echo "5️⃣  Running simulation: Stats Machine"
curl -s -X POST "$API/simulate" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-stats-heavy"}' | jq '{
    model: .model_name,
    games: .total_games,
    accuracy: .accuracy_percentage,
    roi: .simulated_roi,
    profit: .net_profit
  }'
echo ""

# Test 6: Show detailed prediction breakdown
echo "6️⃣  Sample predictions (first 3):"
curl -s -X POST "$API/simulate" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-balanced"}' | jq '.predictions[0:3] | .[] | {
    game: "\(.home_team) vs \(.away_team)",
    predicted: .predicted_outcome,
    actual: .actual_result,
    correct: .correct,
    score: "\(.home_score_actual)-\(.away_score_actual)",
    confidence: .confidence
  }'
echo ""

# Test 7: Confidence breakdown analysis
echo "7️⃣  Confidence Level Performance:"
curl -s -X POST "$API/simulate" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-balanced"}' | jq '.confidence_breakdown | to_entries | map({
    level: .key,
    accuracy: .value.accuracy,
    games: .value.total
  }) | sort_by(.level | tonumber)'
echo ""

# Test 8: Outcome type analysis
echo "8️⃣  Outcome Type Performance:"
curl -s -X POST "$API/simulate" \
  -H "Content-Type: application/json" \
  -d '{"model_id": "preset-balanced"}' | jq '.outcome_breakdown'
echo ""

echo "✅ Simulation tests complete!"
echo ""
echo "📊 Try it yourself:"
echo "   curl -X POST $API/simulate -H 'Content-Type: application/json' -d '{\"model_id\": \"preset-balanced\"}' | jq '.'"
echo ""
echo "🌐 Open the UI: http://localhost:3000"
echo "📖 API Docs: http://localhost:8001/docs"
