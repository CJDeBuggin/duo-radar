# Watcher backup

Two machines take turns checking Apple's pickup endpoint once a minute (one at second 0, one at second 30) and sync over a public ntfy status topic so they don't send duplicate alerts. On Windows, `run_loop.pyw` relaunches `watcher.py` if it exits and logs to `watcher.log`.

Next to the script, create:

1. `topic.txt` — private ntfy alert topic
2. `status_topic.txt` — ntfy status topic the two machines use to coordinate
3. `role.txt` — `primary` on the home PC, `backup` on the second machine

Then `mkdir site` and `pip install requests` if needed.
