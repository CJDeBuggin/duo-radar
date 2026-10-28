# Watcher backup

Restore the stock checker:

1. Copy this folder to `/workspace/instock`.
2. Create `topic.txt` there holding the private ntfy alert topic.
3. Create `status_topic.txt` holding the status topic (`duo-status-7f3d73a348ae`).
4. `mkdir site`
5. `pip install requests` if needed.
6. Run `cd /workspace/instock && setsid nohup ./run.sh >/dev/null 2>&1 &`.
