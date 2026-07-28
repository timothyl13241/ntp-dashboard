import socket
import subprocess
import re
from flask import Flask, render_template

app = Flask(__name__)


def run_command(cmd):
    """Run a shell command and return stdout, or an error string on failure."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return None, result.stderr.strip() or f"Command exited with code {result.returncode}"
        return result.stdout, None
    except FileNotFoundError:
        return None, "chronyc not found – is chrony installed?"
    except subprocess.TimeoutExpired:
        return None, "Command timed out"
    except Exception as exc:
        return None, str(exc)


def parse_tracking(output):
    """Parse the output of 'chronyc tracking' into a dict."""
    data = {}
    patterns = {
        "reference_id": r"^Reference ID\s+:\s+(.+)$",
        "stratum": r"^Stratum\s+:\s+(\d+)$",
        "ref_time": r"^Ref time \(UTC\)\s+:\s+(.+)$",
        "system_time": r"^System time\s+:\s+(.+)$",
        "last_offset": r"^Last offset\s+:\s+(.+)$",
        "rms_offset": r"^RMS offset\s+:\s+(.+)$",
        "frequency": r"^Frequency\s+:\s+(.+)$",
        "root_delay": r"^Root delay\s+:\s+(.+)$",
        "root_dispersion": r"^Root dispersion\s+:\s+(.+)$",
        "update_interval": r"^Update interval\s+:\s+(.+)$",
        "leap_status": r"^Leap status\s+:\s+(.+)$",
    }
    for line in output.splitlines():
        line = line.strip()
        for key, pattern in patterns.items():
            m = re.match(pattern, line)
            if m:
                data[key] = m.group(1).strip()
    return data


def parse_sources(output):
    """Parse the output of 'chronyc sources -v' into a list of dicts."""
    sources = []
    # Find the data lines – they start after the '===...' separator
    in_data = False
    for line in output.splitlines():
        if re.match(r"^=+$", line.strip()):
            in_data = True
            continue
        if not in_data:
            continue
        line = line.strip()
        if not line:
            continue
        # Format: MS Name/IP  Stratum Poll Reach LastRx Last_sample
        # First two chars are mode/state markers
        m = re.match(
            r"^([#^=])([\*\+\-\?x~\s])\s+(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.+)$",
            line,
        )
        if m:
            sources.append(
                {
                    "mode": m.group(1),
                    "state": m.group(2).strip(),
                    "name": m.group(3),
                    "stratum": m.group(4),
                    "poll": m.group(5),
                    "reach": m.group(6),
                    "last_rx": m.group(7),
                    "last_sample": m.group(8).strip(),
                }
            )
    return sources


def parse_clients(output):
    """Parse the output of 'chronyc clients' into a list of dicts."""
    clients = []
    in_data = False
    for line in output.splitlines():
        if re.match(r"^=+$", line.strip()):
            in_data = True
            continue
        if not in_data:
            continue
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 9:
            clients.append(
                {
                    "hostname": parts[0],
                    "ntp_requests": parts[1],
                    "ntp_drops": parts[2],
                    "ntp_interval": parts[3],
                    "ntp_intl": parts[4],
                    "ntp_last": parts[5],
                    "cmd_requests": parts[6],
                    "cmd_drops": parts[7],
                    "cmd_interval": parts[8],
                    "cmd_last": parts[9] if len(parts) > 9 else "-",
                }
            )
    return clients


@app.route("/")
def index():
    hostname = socket.gethostname()

    # Tracking info
    tracking_out, tracking_err = run_command(["chronyc", "tracking"])
    tracking = {}
    if tracking_out:
        tracking = parse_tracking(tracking_out)

    # Determine sync status from leap_status / stratum
    sync_status = "Unknown"
    sync_class = "secondary"
    if tracking_err:
        sync_status = f"Error: {tracking_err}"
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

    # Sources
    sources_out, sources_err = run_command(["chronyc", "sources", "-v"])
    sources = []
    if sources_out:
        sources = parse_sources(sources_out)

    # Clients
    clients_out, clients_err = run_command(["chronyc", "clients"])
    clients = []
    if clients_out:
        clients = parse_clients(clients_out)

    return render_template(
        "index.html",
        hostname=hostname,
        sync_status=sync_status,
        sync_class=sync_class,
        tracking=tracking,
        tracking_err=tracking_err,
        sources=sources,
        sources_err=sources_err,
        clients=clients,
        clients_err=clients_err,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
