#!/bin/bash
# Script to tail expense tracker logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOGS_DIR="$PROJECT_ROOT/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

echo "Tailing Expense Tracker logs..."
echo "Log directory: $LOGS_DIR"
echo "Press Ctrl+C to stop"
echo "================================"

# Check if log files exist
if [ -f "$LOGS_DIR/expense_tracker.log" ]; then
    echo "Tailing expense_tracker.log..."
    tail -f "$LOGS_DIR/expense_tracker.log"
else
    echo "No log files found yet. Logs will appear here once the application runs."
    echo "Waiting for logs..."
    # Wait for log file to be created
    while [ ! -f "$LOGS_DIR/expense_tracker.log" ]; do
        sleep 1
    done
    tail -f "$LOGS_DIR/expense_tracker.log"
fi