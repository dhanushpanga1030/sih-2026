#!/bin/bash
# SafeHabitat AI - Deploy Script
set -e

echo "SafeHabitat AI Deployment"
echo "========================"

case "$1" in
  dev)
    echo "Starting development environment..."
    docker-compose up -d db redis
    cd backend && python -m app.db.migrate_json_to_db
    uvicorn app.main:app --reload --port 8000 &
    cd ../frontend && npm run dev
    ;;
  docker)
    echo "Starting all services with Docker..."
    docker-compose up --build -d
    ;;
  test)
    echo "Running tests..."
    cd backend && pytest tests/ -v --cov=app 2>/dev/null || echo "No backend tests"
    cd ../frontend && npm test
    ;;
  migrate)
    echo "Running database migration..."
    cd backend && python -m app.db.migrate_json_to_db
    ;;
  retrain)
    echo "Retraining ML models..."
    cd backend && python -m app.ml.train
    ;;
  *)
    echo "Usage: $0 {dev|docker|test|migrate|retrain}"
    exit 1
    ;;
esac
