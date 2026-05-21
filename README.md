# 📊🚀 LiteAnalytics & PushFort Core

A ultra-lightweight, self-hosted, and privacy-first all-in-one platform for web analytics and user retention. Replace bloated trackers like Google Analytics 4 and expensive push services like OneSignal with a single, standalone binary execution.

### 🔥 Key Features
* **Dual-Core Infrastructure:** Full web traffic analytics combined with an automated Web Push subscription machine.
* **Lightning Fast Performance:** Backend powered by **FastAPI**. The **SQLite** database automatically utilizes **WAL mode** (Write-Ahead Logging) for concurrent, non-blocking database writes.
* **Invisible Analytics Script:** The `tracker.js` spy script is under **1 KB** in size, written in pure vanilla JS with zero external dependencies.
* **Automated Device Token Collection:** Automatically prompts users for push notification permissions and safely harvests device tokens into your private database.
---

## 🛠️ Quick Start (Local Setup)

### 1. Install Dependencies
Make sure you have Python 3.10+ installed. Clone this repository and install the required packages:
```bash
pip install -r requirements.txt
2. Run the Core Server
Fire up the FastAPI backend using uvicorn:

Bash
uvicorn main:app --reload
Your analytics dashboard is now live at: http://127.0.0.1:8000

🛰️ Connecting the Tracker to Any Website
Simply insert this tiny <script> tag into the HTML of any website you want to track (compatible with custom apps, Webflow, Tilda, WordPress, Shopify, etc.):

HTML
<script src="[http://127.0.0.1:8000/static/tracker.js](http://127.0.0.1:8000/static/tracker.js)" 
        data-project-id="test_project">
</script>
Note: Replace http://127.0.0.1:8000 with your actual production domain (e.g., your Amvera or VPS instance URL).

Tracking Custom Events & Clicks
To capture important user conversions (like clicking a "Buy" button or submitting a form), just add the la-click class and a data-la-target attribute to any HTML element:

HTML
<button class="la-click" data-la-target="main_cta_purchase">Purchase Now</button>
📦 One-Click Deployment (Docker / Amvera)
To deploy the infrastructure into a cloud environment, you can use the included Dockerfile:

Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
All data will persist inside the analytics.db file. Mount this file or its directory to ensure your analytical data survives container restarts.

📜 License
This project is open-source and available under the MIT License. Feel free to use, modify, fork, and exploit it to gather your data.