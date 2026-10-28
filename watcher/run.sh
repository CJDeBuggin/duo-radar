#!/bin/bash
cd /workspace/instock
pgrep -f "python3 /workspace/instock/watcher.py" >/dev/null && exit 0
while true; do python3 /workspace/instock/watcher.py >> watcher.log 2>&1; sleep 5; done
