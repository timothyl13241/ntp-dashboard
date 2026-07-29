# ntp-dashboard

Flask Frontend for Chrony NTP Server

A lightweight web dashboard that displays real-time Chrony NTP statistics using Bootstrap 5 styling.

## Screenshot

![Chrony NTP Dashboard](https://github.com/user-attachments/assets/8edc1c39-334a-4d56-ad04-ceb3eb978c21)

## Features

- Hostname display
- Current synchronization status (colour-coded)
- Stratum & Reference ID
- System offset, root delay and dispersion
- Upstream NTP sources (`chronyc sources -v`)
- Connected NTP clients (`chronyc clients`)

## Architecture

The dashboard uses a privileged collector that writes a JSON snapshot to disk, and the Flask app serves that cached data as an unprivileged user.

```text
chronyd
   |
root collector (systemd timer)
   |
/run/ntp-dashboard/status.json
   |
Flask dashboard (ntpdashboard)
```

## Requirements

- Python 3.8+
- [chrony](https://chrony-project.org/) installed and running on the host
- `chronyc` accessible in `PATH`

## Setup

```bash
# Clone the repository
git clone https://github.com/timothyl13241/ntp-dashboard.git
cd ntp-dashboard

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Running

```bash
python app.py
```

The dashboard is served on **http://0.0.0.0:5000** by default.

For local development without a live collector, you can point the app at a fixture file:

```bash
export NTP_STATUS_FILE=/path/to/status.json
python app.py
```

> **Note:** `chronyc clients` requires chrony to be configured with the
> `clientloglimit` directive (and `cmdallow` for remote access). If chrony is
> not installed the dashboard still loads but shows an error message in each
> section instead of live data.

## Running as a non-root user

It is recommended to run the dashboard under a dedicated unprivileged service account rather than as root. In this architecture, only the collector needs permission to talk to chronyd; the Flask app reads `/run/ntp-dashboard/status.json`.

### 1. Create a dedicated service user

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin ntpdashboard
```

### 2. Allow the collector to run `chronyc`

On Debian/Ubuntu, chrony typically uses an authenticated Unix socket owned by the `_chrony` group:

```bash
ls -l /run/chrony/
```

Verify the control socket name and permissions on your host, then ensure the privileged collector runs with enough access. The provided `ntp-collector.service` runs as `root`, so the Flask app itself does not need `_chrony` membership.

### 3. Change ownership of the application

```bash
sudo chown -R ntpdashboard:ntpdashboard /opt/ntp-dashboard
```

### 4. Install the collector and service units

Copy the application and unit files into place:

```bash
sudo install -m 0755 ntp-collector.py /usr/local/bin/ntp-collector.py
sudo cp ntp-dashboard.service /etc/systemd/system/ntp-dashboard.service
sudo cp ntp-collector.service /etc/systemd/system/ntp-collector.service
sudo cp ntp-collector.timer /etc/systemd/system/ntp-collector.timer
sudo systemctl daemon-reload
```

### 5. Start the collector and dashboard

Enable the timer and start the dashboard service:

```bash
sudo systemctl enable --now ntp-collector.timer
sudo systemctl start ntp-collector.service
sudo systemctl enable --now ntp-dashboard
```

To refresh the cache manually:

```bash
sudo systemctl start ntp-collector.service
```

To restart the dashboard after updating the application:

```bash
sudo systemctl restart ntp-dashboard
```

If you modify any unit file, reload systemd first:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ntp-collector.service
sudo systemctl restart ntp-dashboard
```

## File Structure

```
ntp-dashboard/
├── app.py                  # Flask application that reads cached status JSON
├── chrony_parse.py         # Shared chronyc output parsers
├── ntp-collector.py        # Privileged collector script
├── ntp-collector.service   # Collector one-shot service
├── ntp-collector.timer     # Collector refresh timer
├── ntp-dashboard.service   # Example systemd unit file
├── requirements.txt        # Python dependencies
├── templates/
│   └── index.html          # Bootstrap 5 dashboard template
└── README.md
```
