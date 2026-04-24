# ROBOPILOT Soak Test / Stability Test Tool

---

## 📌 Overview

This project is a **Python-based automation tool** used to run long-duration **soak/stability testing** for the ROBOPILOT streaming service.

The script continuously:

* Logs in and gets Bearer token
* Resolves Company, Site, Mission, and Device
* Starts stream
* Checks stream status after start
* Checks stream status during working time
* Stops stream
* Checks stream status after stop
* Writes CSV and TXT logs
* Repeats until configured duration is completed

---

## 🎯 Objective

* Validate stream stability over long duration
* Detect stream start/stop failures
* Detect unexpected stream drop during working time
* Capture logs for analysis
* Support GO2 and Drone scenarios via config

---

## ⚙️ Features

* Config-driven execution
* Multiple config file support
* Bearer token authentication with auto refresh
* Random working and idle durations
* Mid-stream validation
* Graceful Ctrl+C stop
* CSV + TXT logging
* Dynamic log filenames with timestamp

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

> Note: `__pycache__/` and logs should NOT be committed.

---

## 🧰 Prerequisites

* Python **3.9+**

Check version:

```bash
python --version
```

---

## 🐍 Python Installation

### macOS

```bash
brew install python
```

---

### Ubuntu

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv -y
```

---

### Windows

Download from:
https://www.python.org/downloads/

✔️ Enable: **Add Python to PATH**

---

## 🚀 Setup

### macOS / Ubuntu

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### Duration Format (Recommended)

```json
"test": {
  "duration": {
    "days": 0,
    "hours": 0,
    "minutes": 30
  },
  "cycle_buffer_seconds": 30
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

## 📥 Inputs (Selection)

### GO2

```json
"selection": {
  "company_name": "현대건설",
  "site_name": "힐스테이트 도안2단지",
  "mission_name": "TestforGO2",
  "device_name": "Unitree GO2"
}
```

---

### Drone

```json
"selection": {
  "company_name": "현대건설",
  "site_name": "힐스테이트 도안2단지",
  "mission_name": "TestForDrone",
  "device_name": "DJI M4E"
}
```

---

## ▶️ Run Commands

### GO2

```bash
python main.py config_go2.json
```

---

### Drone

```bash
python main.py config_drone.json
```

---

## 📊 Output Location

All outputs are stored in:

```text
logs/
```

---

### 📄 TXT Log (Execution Details)

```text
logs/<mission>_<device>_<timestamp>.log
```

Contains:

* Start/end logs
* Cycle execution
* Stream start/stop
* Mid-stream checks
* Errors

---

### 📊 CSV Log (Results)

```text
logs/<mission>_<device>_<timestamp>.csv
```

Contains:

* cycle_no
* expected vs actual time
* time difference
* working/idle durations
* result (success/failure)
* error details

---

## 🔁 Test Flow

```text
Login
 → Resolve Context
 → Start Stream
 → Verify Start
 → Working Loop (status checks)
 → Stop Stream
 → Verify Stop
 → Log Results
 → Idle
 → Repeat
```

---

## 🛑 Manual Stop

Press:

```text
Ctrl + C
```

System will:

* Stop active stream
* Save CSV entry
* Exit safely

---

## 🚫 Git Ignore

Add:

```gitignore
__pycache__/
*.pyc
.venv/
logs/
```

If logs already tracked:

```bash
git rm -r --cached logs/
```

---

## ☁️ Long Duration Run (Recommended)

Use VM / EC2 with `tmux`:

```bash
tmux new -s soak-test
python main.py config_go2.json
```

Detach:

```text
Ctrl + B → D
```

---

## 🧪 Troubleshooting

### Python not found

Use:

```bash
python3 --version
```

---

### Logs not generated

Create folder:

```bash
mkdir logs
```

---

### Stream stopped unexpectedly

Check TXT log for:

```text
Stream stopped unexpectedly
```

---

## 👨‍💻 Author

ROBOPILOT Stability Testing Tool
