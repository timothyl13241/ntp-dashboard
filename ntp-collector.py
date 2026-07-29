#!/usr/bin/env python3
import datetime as dt
import grp
import json
import os
import socket
import subprocess
import sys
import tempfile

APP_DIR = os.environ.get("NTP_APP_DIR", os.getcwd())
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from chrony_parse import (
    extract_chronyc_error,
    parse_clients,
    parse_sources,
    parse_tracking,
)

RUN_DIR = os.environ.get("NTP_STATUS_DIR", "/run/ntp-dashboard")
STATUS_FILE = os.environ.get("NTP_STATUS_FILE", os.path.join(RUN_DIR, "status.json"))
STATUS_GROUP = os.environ.get("NTP_STATUS_GROUP", "ntpdashboard")
COMMANDS = {
    "tracking": ["chronyc", "tracking"],
    "sources": ["chronyc", "sources", "-v"],
    "clients": ["chronyc", "clients"],
}


def run_command(cmd):
    """Run a chronyc command and return (stdout, error_string)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except FileNotFoundError:
        return None, "chronyc not found – is chrony installed?"
    except subprocess.TimeoutExpired:
        return None, "Command timed out"
    except Exception as exc:
        return None, str(exc)

    output = result.stdout or ""
    error_text = result.stderr.strip() or output.strip()
    if result.returncode != 0:
        return None, error_text or f"Command exited with code {result.returncode}"

    chronyc_error = extract_chronyc_error(output)
    if chronyc_error:
        return None, chronyc_error

    return output, None


def get_status_group_id():
    """Return the configured status group id, or None if it does not exist."""
    try:
        return grp.getgrnam(STATUS_GROUP).gr_gid
    except KeyError:
        return None


def ensure_runtime_dir(path):
    """Create the runtime directory and apply restrictive permissions."""
    os.makedirs(path, mode=0o750, exist_ok=True)
    gid = get_status_group_id()
    if gid is not None:
        try:
            os.chown(path, -1, gid)
        except PermissionError:
            pass
    os.chmod(path, 0o750)


def build_status():
    """Collect chrony data into a serialisable status payload."""
    payload = {
        "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "tracking": {},
        "sources": [],
        "clients": [],
        "errors": {
            "tracking": None,
            "sources": None,
            "clients": None,
        },
    }

    tracking_out, tracking_err = run_command(COMMANDS["tracking"])
    if tracking_out:
        payload["tracking"] = parse_tracking(tracking_out)
    payload["errors"]["tracking"] = tracking_err

    sources_out, sources_err = run_command(COMMANDS["sources"])
    if sources_out:
        payload["sources"] = parse_sources(sources_out)
    payload["errors"]["sources"] = sources_err

    clients_out, clients_err = run_command(COMMANDS["clients"])
    if clients_out:
        payload["clients"] = parse_clients(clients_out)
    payload["errors"]["clients"] = clients_err

    return payload


def write_status(payload):
    """Atomically write the status JSON to disk."""
    ensure_runtime_dir(os.path.dirname(STATUS_FILE))
    # mkstemp() starts with owner-only permissions until we set the final mode.
    fd, temp_path = tempfile.mkstemp(prefix="status.", suffix=".json", dir=os.path.dirname(STATUS_FILE))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        gid = get_status_group_id()
        if gid is not None:
            try:
                os.chown(temp_path, -1, gid)
            except PermissionError:
                pass
        os.chmod(temp_path, 0o640)
        os.replace(temp_path, STATUS_FILE)
    except Exception:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def main():
    write_status(build_status())


if __name__ == "__main__":
    main()
