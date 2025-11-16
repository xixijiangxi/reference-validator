#!/bin/bash

echo "Starting Reference Validator Application..."
echo ""

echo "Starting Backend Server..."
cd backend
python3 -m uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 3

echo "Starting Frontend Server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "Both servers are starting..."
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

wait

