#!/bin/bash
while true; do
    sleep 120
    cd /shared/ASTRA && python3 astra_live_backend/generate_dashboard.py 2>/dev/null
done
