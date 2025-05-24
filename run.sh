#!/bin/bash

# Install backend dependencies
echo "Installing backend dependencies..."
cd backend
pip install -r requirements.txt

# Start backend server in the background
echo "Starting backend server..."
python run.py &
BACKEND_PID=$!

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd ../frontend
npm install

# Start frontend server
echo "Starting frontend server..."
npm run dev

# Kill backend server when script is terminated
trap "kill $BACKEND_PID" EXIT