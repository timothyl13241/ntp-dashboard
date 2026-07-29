import datetime as dt
import json
import os
import socket

from flask import Flask, render_template

app = Flask(__name__)

STATUS_FILE = os.environ.get("NTP_STATUS_FILE", "/run/ntp-dashboard/status.json")


def _load_status_max_age():
    """Return the configured staleness threshold in seconds."""
    value = os.environ.get("NTP_STATUS_MAX_AGE", "180")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid NTP_STATUS_MAX_AGE={value!r}; expected an integer number of seconds"
        ) from exc


STATUS_MAX_AGE = _load_status_max_age()
# Negative STATUS_MAX_AGE values disable stale-file checks.


def _parse_timestamp(value):
    """Parse an ISO timestamp string into an aware datetime."""
    if not value:
        raise ValueError("Missing collected_at timestamp")
    # Python 3.8 `fromisoformat()` does not accept a trailing Z UTC suffix.
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed


def _error_payload(message, hostname=None):
    """Return a status payload that surfaces the same error in all sections."""
    return {
        "hostname": hostname or socket.gethostname(),
        "tracking": {},
        "sources": [],
        "clients": [],
        "tracking_err": message,
        "sources_err": message,
        "clients_err": message,
    }


def load_status():
    """Load dashboard status from the collector JSON file."""
    if not os.path.exists(STATUS_FILE):
        return _error_payload(f"Status file not found: {STATUS_FILE}")

    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return _error_payload(f"Unable to read status file: {exc}")

    try:
        collected_at = _parse_timestamp(payload.get("collected_at"))
    except (TypeError, ValueError) as exc:
        return _error_payload(f"Invalid status file timestamp: {exc}", payload.get("hostname"))

    age = (dt.datetime.now(dt.timezone.utc) - collected_at).total_seconds()
    if STATUS_MAX_AGE >= 0 and age > STATUS_MAX_AGE:
        return _error_payload(
            f"Status file is stale ({int(age)} seconds old)",
            payload.get("hostname"),
        )

    errors = payload.get("errors")
    if not isinstance(errors, dict):
        return _error_payload("Status file is missing the errors object", payload.get("hostname"))

    tracking_data = payload.get("tracking")
    sources_data = payload.get("sources")
    clients_data = payload.get("clients")

    return {
        "hostname": payload.get("hostname") or socket.gethostname(),
        "tracking": tracking_data if isinstance(tracking_data, dict) else {},
        "sources": sources_data if isinstance(sources_data, list) else [],
        "clients": clients_data if isinstance(clients_data, list) else [],
        "tracking_err": errors.get("tracking"),
        "sources_err": errors.get("sources"),
        "clients_err": errors.get("clients"),
    }


@app.route("/")
def index():
    status = load_status()
    tracking = status["tracking"]

    sync_status = "Unknown"
    sync_class = "secondary"
    if status["tracking_err"]:
        sync_status = f"Error: {status['tracking_err']}"
        sync_class = "danger"
    elif tracking:
        leap = tracking.get("leap_status", "").lower()
        stratum = tracking.get("stratum", "16")
        if leap == "normal" and stratum not in ("0", "16"):
            sync_status = "Synchronized"
            sync_class = "success"
        elif stratum in ("0", "16"):
            sync_status = "Not Synchronized"
            sync_class = "warning"
        else:
            sync_status = leap.capitalize() if leap else "Unknown"
            sync_class = "warning"

    return render_template(
        "index.html",
        hostname=status["hostname"],
        sync_status=sync_status,
        sync_class=sync_class,
        tracking=tracking,
        tracking_err=status["tracking_err"],
        sources=status["sources"],
        sources_err=status["sources_err"],
        clients=status["clients"],
        clients_err=status["clients_err"],
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
