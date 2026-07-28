# ntp-dashboard

Flask Frontend for Chrony NTP Server

A lightweight web dashboard that displays real-time Chrony NTP statistics using Bootstrap 5 styling.

## Screenshot

![Chrony NTP Dashboard](https://github.com/user-attachments/assets/b1543453-7a8f-4531-8345-64f8059e9512)

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

## File Structure

```
ntp-dashboard/
├── app.py              # Flask application & chronyc parsers
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Bootstrap 5 dashboard template
└── README.md
```
