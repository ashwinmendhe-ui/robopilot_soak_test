# ROBOPILOT Soak Test / Stability Test Tool

## 📌 Overview

This project is a **Python-based automation tool** used to run long-duration **soak/stability testing** for the ROBOPILOT streaming service.

The tool continuously:

- Logs in and gets Bearer token
- Resolves Company, Site, Mission, and Device
- Starts stream
- Checks stream status after start
- Checks stream status during working time
- Confirms temporary false stream status using retry checks
- Stops stream
- Checks stream status after stop
- Writes CSV and TXT logs
- Repeats until configured duration is completed

---

## 🎯 Objective

- Validate stream stability over long duration
- Detect stream start/stop failures
- Detect unexpected stream drop during working time
- Avoid false failure due to temporary network/API status fluctuation
- Capture logs for analysis and debugging
- Support GO2 and Drone scenarios via config files

---

## ⚙️ Features

- Config-driven execution
- Multiple config file support
- Bearer token authentication with refresh support
- Mission/device resolution using names
- Random working and idle durations
- Short/long timing profiles
- Mid-stream validation
- Consecutive false-status confirmation
- Graceful `Ctrl + C` shutdown
- CSV result logging
- TXT debug logging
- Dynamic log filenames with mission, device, and timestamp
- Latest-first CSV generation for easier review

---

## 📂 Project Structure

```text
robopilot_soak_test/
├── README.md
├── main.py
├── auth.py
├── stream_api.py
├── logger_util.py
├── utils.py
├── config.test.json
├── config_drone.json
├── config_go2.json
├── requirements.txt
├── .gitignore
├── logs/
└── tests/
    ├── unit/
    │   ├── test_utils.py
    │   ├── test_auth.py
    │   ├── test_stream_api.py
    │   └── test_logger_util.py
    └── integration/
        ├── test_login_api.py
        ├── test_mission_api.py
        ├── test_device_api.py
        └── test_stream_flow.py
```

> Note: `__pycache__/`, `.venv/`, and `logs/` should not be committed to Git.

---

## 🧰 Prerequisites

- Python **3.9+**
- Git
- Internet/API access to ROBOPILOT backend

Check Python version:

```bash
python --version
```

or:

```bash
python3 --version
```

---

## ⬇️ Get Latest Code from GitHub

### Repository

```text
https://github.com/DhiveTeam/robopilot_soak_test
```

---

### Clone Project First Time

```bash
git clone https://github.com/DhiveTeam/robopilot_soak_test.git
cd robopilot_soak_test
```

---

### Check Remote

```bash
git remote -v
```

Expected:

```text
origin  https://github.com/DhiveTeam/robopilot_soak_test.git (fetch)
origin  https://github.com/DhiveTeam/robopilot_soak_test.git (push)
```

If your remote name is `DhiveTeam`, pull using:

```bash
git pull DhiveTeam main
```

If your remote name is `origin`, pull using:

```bash
git pull origin main
```

---

### Get Latest Changes Before Running Test

```bash
git pull origin main
```

or, if your remote name is `DhiveTeam`:

```bash
git pull DhiveTeam main
```

If `requirements.txt` changed, reinstall dependencies:

```bash
pip install -r requirements.txt
```

---

## 🐍 Python Installation

## macOS

Install Python using Homebrew:

```bash
brew install python
```

Verify:

```bash
python3 --version
pip3 --version
```

---

## Ubuntu

Install Python, pip, venv, and Git:

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv git -y
```

Verify:

```bash
python3 --version
pip3 --version
git --version
```

---

## Windows

Download Python from:

```text
https://www.python.org/downloads/
```

During installation, enable:

```text
Add Python to PATH
```

Install Git from:

```text
https://git-scm.com/download/win
```

Verify in Command Prompt or PowerShell:

```powershell
python --version
pip --version
git --version
```

---

## 🚀 Setup

## macOS / Ubuntu Setup

Create virtual environment:

```bash
python3 -m venv .venv
```

Activate virtual environment:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Windows Setup

Create virtual environment:

```powershell
python -m venv .venv
```

Activate virtual environment:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Use one of the config files:

```text
config_go2.json
config_drone.json
config.test.json
```

---

### Duration Format

Recommended format:

```json
"test": {
  "duration": {
    "days": 0,
    "hours": 0,
    "minutes": 30
  },
  "request_timeout_seconds": 30,
  "start_check_retries": 6,
  "stop_check_retries": 6,
  "check_interval_seconds": 5,
  "mid_stream_check_interval_seconds": 15,
  "false_confirm_retries": 3,
  "false_confirm_interval_seconds": 5,
  "cycle_buffer_seconds": 30
}
```

---

### False Stream Status Confirmation

To avoid false failures due to temporary network/API fluctuation:

```json
"false_confirm_retries": 3,
"false_confirm_interval_seconds": 5
```

Meaning:

```text
First false detected
→ wait 5 seconds and check again
→ wait 5 seconds and check again
→ wait 5 seconds and check again
```

Only if all confirmation checks are still false, the cycle is marked as failed.

---

### Timing Profiles

```json
"timing_profiles": {
  "working_time": {
    "short_min_seconds": 30,
    "short_max_seconds": 120,
    "long_min_seconds": 300,
    "long_max_seconds": 900
  },
  "idle_time": {
    "short_min_seconds": 10,
    "short_max_seconds": 60,
    "long_min_seconds": 180,
    "long_max_seconds": 600
  }
}
```

---

### Logging Format

```json
"logging": {
  "csv_path": "logs/{mission_name}_{device_name}_{timestamp}.csv",
  "txt_path": "logs/{mission_name}_{device_name}_{timestamp}.log"
}
```

Example output:

```text
logs/TestforGO2_Unitree_GO2_2026-04-24_16-30-15.csv
logs/TestforGO2_Unitree_GO2_2026-04-24_16-30-15.log
```

---

## 📥 Inputs / Selection

## GO2

```json
"selection": {
  "company_name": "현대건설",
  "site_name": "힐스테이트 도안2단지",
  "mission_name": "TestforGO2",
  "device_name": "Unitree GO2"
}
```

Run with:

```bash
python3 main.py config_go2.json
```

On Windows:

```powershell
python main.py config_go2.json
```

---

## Drone

```json
"selection": {
  "company_name": "현대건설",
  "site_name": "힐스테이트 도안2단지",
  "mission_name": "TestForDrone",
  "device_name": "DJI M4E"
}
```

Run with:

```bash
python3 main.py config_drone.json
```

On Windows:

```powershell
python main.py config_drone.json
```

---

## ▶️ Run Commands

## GO2

macOS / Ubuntu:

```bash
python3 main.py config_go2.json
```

Windows:

```powershell
python main.py config_go2.json
```

---

## Drone

macOS / Ubuntu:

```bash
python3 main.py config_drone.json
```

Windows:

```powershell
python main.py config_drone.json
```

---

## 📊 Output Location

All output files are stored inside:

```text
logs/
```

---

## TXT Log

Example:

```text
logs/TestforGO2_Unitree_GO2_2026-04-24_16-30-15.log
```

Contains:

- Test start information
- Total soak duration
- Resolved company/site/mission/device
- Cycle start/end logs
- Start stream result
- Mid-stream status checks
- False-status confirmation retry logs
- Stop stream result
- Errors and failures

---

## CSV Log

Example:

```text
logs/TestforGO2_Unitree_GO2_2026-04-24_16-30-15.csv
```

Contains:

- `cycle_no`
- `expected_cycle_time`
- `actual_cycle_time`
- `time_difference`
- `start_time_kst`
- `end_time_kst`
- `company_name`
- `site_name`
- `mission_name`
- `device_name`
- `action`
- `result`
- `http_status`
- `working_mode`
- `working_seconds`
- `idle_mode`
- `idle_seconds`
- `token_refreshed`
- `message`
- `error_details`
- `timestamp_utc`

---

## Latest-first CSV

At the end of execution, an additional latest-first CSV is generated:

```text
logs/TestforGO2_Unitree_GO2_2026-04-24_16-30-15_latest_first.csv
```

This helps review the latest cycles first.

---

## 🔁 Test Flow

```text
Login
  ↓
Resolve Company / Site / Mission / Device
  ↓
Start Stream
  ↓
Verify Stream Active
  ↓
Monitor Stream During Working Time
  ↓
If status is false:
    Confirm with multiple retry checks
  ↓
Stop Stream
  ↓
Verify Stream Stopped
  ↓
Write CSV/TXT Logs
  ↓
Idle
  ↓
Repeat Until Duration Ends
```

---

## 🛑 Manual Stop

Press:

```text
Ctrl + C
```

The script will:

- Detect manual stop
- Stop active stream if running
- Write final CSV row
- Mark `action = manual_stop`
- Mark `result = stopped`
- Create latest-first CSV
- Exit safely

---

## 🚫 Git Ignore

Add this to `.gitignore`:

```gitignore
# Python cache
__pycache__/
*.pyc

# Virtual environment
.venv/

# Soak test logs
logs/
```

If logs are already tracked:

```bash
git rm -r --cached logs/
```

Then commit:

```bash
git add .
git commit -m "Remove generated logs from tracking"
```

---

## ☁️ Long Duration Run

For long soak tests such as 24 hours or 7 days, run on a stable VM/EC2 instead of a local machine.

Recommended: use `tmux`.

Install tmux on Ubuntu:

```bash
sudo apt install tmux -y
```

Start session:

```bash
tmux new -s soak-test
```

Run test:

```bash
python3 main.py config_go2.json
```

Detach session:

```text
Ctrl + B, then D
```

Reattach session:

```bash
tmux attach -t soak-test
```

---

## 🧪 Troubleshooting

## Python not found

Try:

```bash
python3 --version
```

If Windows, reinstall Python and enable:

```text
Add Python to PATH
```

---

## Module not found

Activate virtual environment and reinstall dependencies:

macOS / Ubuntu:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## Logs not generated

Create logs folder:

```bash
mkdir logs
```

---

## Stream stopped unexpectedly

Check TXT log for:

```text
Stream stopped unexpectedly
```

This usually means the backend or streaming service stopped the stream before the expected working time.

---

## Git pull failed

Check remote:

```bash
git remote -v
```

If remote is `origin`:

```bash
git pull origin main
```

If remote is `DhiveTeam`:

```bash
git pull DhiveTeam main
```

---

## ✅ Current Status

| Area | Status |
|---|---|
| Core automation | Completed |
| Config-driven execution | Completed |
| Auth/token handling | Completed |
| Mission/device resolution | Completed |
| Stream start/stop | Completed |
| Status validation | Completed |
| Mid-stream monitoring | Completed |
| False-status confirmation | Completed |
| CSV/TXT logging | Completed |
| Dynamic log filenames | Completed |
| Latest-first CSV | Completed |
| Unit tests | Completed |
| Integration tests | Completed |
| Long-duration soak test | In validation |

---

## 👨‍💻 Author

ROBOPILOT Stability Testing Tool
