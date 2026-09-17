#!/usr/bin/env bash
# Watch one grid run's log and exit -- once -- on the first thing worth a human's attention.
#
#   bash tools/phase9/watch_run.sh <log> [stall_minutes=30] [poll_seconds=60]
#
# Exit codes, each printed as a single line so a background launcher surfaces it as one notification:
#   0  COMPLETE   the runner printed its final [N/N] line
#   1  FAILED RUN a run finished non-ok (a transient that later retries clean still fires: look, then re-arm)
#   2  ALERT      a traceback, refusal, abandonment, or a provider rate-limit / quota signal
#   3  STALLED    the log has not grown for stall_minutes -- a hang, a dead process, or a sleeping laptop
#
# Designed to run for the whole grid rather than for a monitor's fixed window, and to treat silence as a signal
# rather than as success. Only lines written AFTER it starts are judged, so re-arming never re-reports old events.
set -uo pipefail

LOG="${1:?usage: watch_run.sh <log> [stall_minutes] [poll_seconds]}"
STALL_MIN="${2:-30}"
POLL="${3:-60}"

[ -f "$LOG" ] || { echo "ALERT: log not found: $LOG"; exit 2; }

start=$(wc -l < "$LOG")
last_size=$(wc -c < "$LOG")
last_change=$(date +%s)

# Provider throttling signatures. Deliberately NOT a bare "429": run times are logged in seconds, and a run that
# takes 429 s would otherwise raise a false alarm.
THROTTLE='ResourceExhausted|RESOURCE_EXHAUSTED|RateLimitError|rate limit|Too Many Requests|HTTP 429|status 429|quota'
FATAL='Traceback|REFUSING|Killed|MemoryError|abandoned'

while true; do
  new=$(tail -n +"$((start + 1))" "$LOG" 2>/dev/null)

  bad=$(printf '%s\n' "$new" | grep -E -- '-> ' | grep -vE -- '-> ok' | head -1)
  if [ -n "$bad" ]; then echo "FAILED RUN: $bad"; exit 1; fi

  alert=$(printf '%s\n' "$new" | grep -E "$FATAL|$THROTTLE" | head -1)
  if [ -n "$alert" ]; then echo "ALERT: $alert"; exit 2; fi

  done_line=$(printf '%s\n' "$new" | grep -E '\[([0-9]+)/\1\]' | tail -1)
  if [ -n "$done_line" ]; then echo "COMPLETE: $done_line"; exit 0; fi

  size=$(wc -c < "$LOG")
  now=$(date +%s)
  if [ "$size" != "$last_size" ]; then
    last_size=$size; last_change=$now
  elif [ $((now - last_change)) -ge $((STALL_MIN * 60)) ]; then
    echo "STALLED: no log output for ${STALL_MIN} min; last line: $(tail -n 1 "$LOG")"
    exit 3
  fi

  sleep "$POLL"
done
