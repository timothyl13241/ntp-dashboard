import re

# Minimum number of whitespace-separated fields required in a chronyc clients
# output data line. The format has 9 required fields (indices 0–8) and one
# Optional field (index 9, cmd_last) which is accessed conditionally.
_MIN_CLIENT_FIELDS = 9


def extract_chronyc_error(output):
    """Return chronyc daemon/client error text from output, if present."""
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"^[45]\d{2}\s+\S", line):
            return line
    return None


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
        m = re.match(
            r"""
            ^
            ([#^=])
            ([\*\+\-\?x~\s])
            \s+
            (\S+)
            \s+(\d+)
            \s+(\d+)
            \s+(\d+)
            \s+(\S+)
            \s+(.+)
            $
            """,
            line,
            re.VERBOSE,
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
        if len(parts) >= _MIN_CLIENT_FIELDS:
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
