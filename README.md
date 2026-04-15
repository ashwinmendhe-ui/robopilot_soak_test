# ROBOPILOT Soak Test (Stability Test Tool)---## 📌 OverviewThis project is a **Python-based automation tool** designed to perform a **Soak Test / Stability Test** on the ROBOPILOT streaming service.The script continuously:- Starts a stream  - Verifies streaming status  - Stops the stream  - Logs results  - Repeats the process for a long duration (e.g., 7 days)---## 🎯 Objective- Validate system stability over long-duration execution  - Detect failures in start/stop streaming  - Monitor streaming reliability  - Capture logs for analysis  ---## ⚙️ Features- Automated Start/Stop Stream Testing  - Random interval execution (30 sec – 15 min)  - Bearer token authentication with auto refresh  - Stream status verification  - Continuous execution (configurable duration)  - CSV + TXT logging  - Config-driven (no code changes required)  ---## 📂 Project Structure
robopilot_soak_test/
├── main.py                # Main execution script
├── config.json           # Configuration file
├── auth.py               # Authentication handling
├── stream_api.py         # API calls (start/stop/status)
├── logger_util.py        # Logging (CSV + TXT)
├── utils.py              # Helper functions
├── requirements.txt      # Dependencies
├── logs/                 # Output logs
└── .gitignore
---## 🔧 ConfigurationUpdate `config.json` before running:```json{  "base_url": "http://52.64.157.221:6789/api",  "auth": {    "email": "your_email",    "password": "your_password",    "refresh_after_hours": 48  },  "selection": {    "company_id": "UUID",    "site_id": "UUID",    "mission_id": "UUID",    "device_id": "UUID",    "device_name": "Drone-01"  }}

🔐 Authentication


Uses POST /v1/auth/login


Stores Bearer token in memory


Automatically refreshes token before expiry (default: every 48 hours)



🔁 Test Flow
Login → Start Stream → Verify → Wait (random)→ Stop Stream → Verify → Log → Repeat

📊 Logging
CSV Log (Structured)
Stored in:
logs/soak_test_results.csv
Includes:


Timestamp


Cycle number


Device ID


Action (start/stop/verify)


Result (success/failure)


HTTP status


Wait duration


Token refresh status


Error details



TXT Log (Detailed)
Stored in:
logs/soak_test.log
Includes:


Execution flow logs


Errors


Debug messages



🚀 Setup & Run
1. Create virtual environment
python3 -m venv .venvsource .venv/bin/activate   # Mac/Linux
2. Install dependencies
pip install -r requirements.txt
3. Run script
python main.py

⏱️ Recommended Test Setup
Initial testing
"duration_days": 1,"min_wait_seconds": 30,"max_wait_seconds": 60
Actual soak test
"duration_days": 7,"min_wait_seconds": 30,"max_wait_seconds": 900

☁️ Deployment Recommendation
For long-duration execution (1 week):


Use VM / EC2 instance


Avoid local machine (sleep/network issues)


Run using:


tmux / screen


or systemd service





⚠️ Notes


API payloads may require adjustment based on backend response


Stream status verification logic may need tuning


Ensure correct UUIDs for company/site/device



📌 Future Improvements


Cloud logging (CloudWatch / ELK)


Alerting on failures (Email / Slack)


Multi-device testing


Docker container support


Dashboard for results



👨‍💻 Author
Developed as part of ROBOPILOT stability testing initiative.
---## ✅ Now this is:- Proper Markdown ✅  - Clean spacing ✅  - GitHub-ready ✅  - Manager/demo-friendly ✅  ---If you want next step, we can:- Add **Docker support (1 command run anywhere)**- Or prepare **EC2 deployment step-by-step guide** 🚀