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

> **Note:** `chronyc clients` requires chrony to be configured with the
> `clientloglimit` directive (and `cmdallow` for remote access). If chrony is
> not installed the dashboard still loads but shows an error message in each
> section instead of live data.

## Running as a non-root user

It is recommended to run the dashboard under a dedicated unprivileged service account rather than as root.

### 1. Create a dedicated service user

```bash
sudo useradd --system --no-create-home --shell /usr/sbin/nologin ntpdashboard
```

### 2. Allow the user to run `chronyc`

On Debian/Ubuntu, chrony uses an authenticated Unix socket owned by the `_chrony` group:

```bash
ls -l /run/chrony/
# -rw-r----- 1 root _chrony /run/chrony/chronyc.sock
```

Add the dashboard user to the `_chrony` group:

```bash
sudo usermod -aG _chrony ntpdashboard
```

Verify with:

```bash
groups ntpdashboard
```

### 3. Change ownership of the application

```bash
sudo chown -R ntpdashboard:ntpdashboard /opt/ntp-dashboard
```

### 4. Configure and enable the systemd service

An example unit file is provided at `ntp-dashboard.service`. Copy it to the systemd directory and enable it:

```bash
sudo cp ntp-dashboard.service /etc/systemd/system/ntp-dashboard.service
sudo systemctl daemon-reload
sudo systemctl enable --now ntp-dashboard
```

To restart after a configuration change:

```bash
sudo systemctl daemon-reload
sudo systemctl restart ntp-dashboard
```

## File Structure

```
ntp-dashboard/
├── app.py                  # Flask application & chronyc parsers
├── requirements.txt        # Python dependencies
├── ntp-dashboard.service   # Example systemd unit file
├── templates/
│   └── index.html          # Bootstrap 5 dashboard template
└── README.md
```
