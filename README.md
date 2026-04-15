# ROBOPILOT Soak Test (Stability Test Tool)

---

## 📌 Overview

This project is a **Python-based automation tool** designed to perform a **Soak Test / Stability Test** on the ROBOPILOT streaming service.

The script continuously:
- Starts a stream  
- Verifies streaming status  
- Stops the stream  
- Logs results  
- Repeats the process for a long duration (e.g., 7 days)

---

## 🎯 Objective

- Validate system stability over long-duration execution  
- Detect failures in start/stop streaming  
- Monitor streaming reliability  
- Capture logs for analysis  

---

## ⚙️ Features

- Automated Start/Stop Stream Testing  
- Random interval execution (30 sec – 15 min)  
- Bearer token authentication with auto refresh  
- Stream status verification  
- Continuous execution (configurable duration)  
- CSV + TXT logging  
- Config-driven (no code changes required)  

---

## 📂 Project Structure

```
robopilot_soak_test/
├── main.py
├── config.json
├── auth.py
├── stream_api.py
├── logger_util.py
├── utils.py
├── requirements.txt
├── logs/
└── .gitignore
```

---

## 🔧 Configuration

Update `config.json` before running:

```json
{
  "base_url": "http://52.64.157.221:6789/api",
  "auth": {
    "email": "your_email",
    "password": "your_password",
    "refresh_after_hours": 48
  },
  "selection": {
    "company_id": "UUID",
    "site_id": "UUID",
    "mission_id": "UUID",
    "device_id": "UUID",
    "device_name": "Drone-01"
  }
}
```

---

## 🔐 Authentication

- Uses `POST /v1/auth/login`  
- Stores Bearer token in memory  
- Automatically refreshes token before expiry  

---

## 🔁 Test Flow

```
Login → Start Stream → Verify → Wait (random)
→ Stop Stream → Verify → Log → Repeat
```

---

## 📊 Logging

### CSV Log
`logs/soak_test_results.csv`

### TXT Log
`logs/soak_test.log`

---

## 🚀 Setup & Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## ☁️ Deployment Recommendation

- Use VM / EC2 for long-duration execution  
- Avoid local machine  
- Use tmux / screen for stability  

---

## 👨‍💻 Author

ROBOPILOT Stability Testing Tool

## Dir tree structure
robopilot_soak_test/
├── main.py
├── auth.py
├── stream_api.py
├── logger_util.py
├── utils.py
├── config.json
├── tests/
│   ├── unit/
│   │   ├── test_utils.py
│   │   ├── test_auth.py
│   │   ├── test_stream_api.py
│   │   └── test_logger_util.py
│   └── integration/
│       ├── test_login_api.py
│       ├── test_mission_lookup.py
│       ├── test_device_lookup.py
│       └── test_stream_flow.py
├── requirements.txt
└── .gitignore

## Given inputs
Company, Site, Robot, Mission

    - Drone: FPT, Duy Tan, M4E Display Name, TestForDrone

    - GO2: 현대건설, 힐스테이트 도안2단지, Unitree GO2, TestForGO2