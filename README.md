# Domestic Stock Selection Agent

KOSPI/KOSDAQ daily stock selector for a local Windows PC.

The agent runs after the regular Korean market close, screens stocks by:

1. Daily trading value >= KRW 1 trillion
2. Annual operating profit positive for the most recent 3 fiscal years
3. Daily price change >= 5%

Selected stocks are stored in SQLite, shown on a local dashboard, and sent by Telegram.

## Stack

- FastAPI + Jinja2
- SQLite
- KIS Developers API for daily quote data
- OpenDART API for annual operating profit
- NAVER Search API for recent related news
- Telegram Bot API for notification

## Setup

```powershell
Copy-Item .env.example .env
```

Fill `.env` with your API keys.

Install Python dependencies:

```powershell
py -m pip install -r requirements.txt
```

If `py` is not available, install Python 3.11+ first.

## Run the web dashboard

```powershell
py -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

## Run daily selection manually

Sample mode:

```powershell
py -m app.agent --sample
```

Real API mode:

```powershell
py -m app.agent
```

## Update KOSPI/KOSDAQ universe

```powershell
powershell -ExecutionPolicy Bypass -File scripts\update_universe.ps1
```

The script writes `data/universe.csv` with KOSPI/KOSDAQ tickers from the KRX KIND listing download and excludes KONEX, SPAC-like names, non-6-digit tickers, and preferred shares by default.

## Windows Task Scheduler

Register a weekday 15:45 KST task:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_task.ps1
```

Register and start the local web dashboard at Windows logon:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\register_web_startup.ps1
```

## VPS Deployment

Recommended target:

- Ubuntu 24.04
- 1 GB RAM VPS
- Python 3.12+
- Telegram group chat ID in `TELEGRAM_CHAT_ID`
- Basic Auth enabled with `WEB_AUTH_USERNAME` and `WEB_AUTH_PASSWORD`

### 1. Prepare server

```bash
sudo apt update
sudo apt install -y git python3 python3-venv
sudo useradd --system --create-home --shell /usr/sbin/nologin stockagent || true
sudo mkdir -p /opt/stock-agent
sudo chown "$USER":"$USER" /opt/stock-agent
```

Clone or copy the repository:

```bash
git clone https://github.com/byuuujbu/Stock-5-.git /opt/stock-agent
cd /opt/stock-agent
```

Install dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
chmod +x scripts/*.sh
mkdir -p data logs
```

### 2. Configure environment

```bash
cp .env.example .env
nano .env
chmod 600 .env
```

Required production values:

```env
APP_BASE_URL=http://SERVER_IP:8000
APP_SAMPLE_MODE=false
WEB_AUTH_USERNAME=stock5ri
WEB_AUTH_PASSWORD=1q2w3e4r
KIS_APP_KEY=
KIS_APP_SECRET=
DART_API_KEY=
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

For Telegram group delivery, set `TELEGRAM_CHAT_ID` to the group chat ID.

### 3. Build universe

```bash
./scripts/update_universe.sh
```

### 4. Install web service

Edit `deploy/stock-agent.service` if the app path is not `/opt/stock-agent`.

```bash
sudo cp deploy/stock-agent.service /etc/systemd/system/stock-agent.service
sudo chown -R stockagent:stockagent /opt/stock-agent
sudo systemctl daemon-reload
sudo systemctl enable --now stock-agent
sudo systemctl status stock-agent
```

Open firewall port 8000 if needed:

```bash
sudo ufw allow 8000/tcp
```

Dashboard:

```text
http://SERVER_IP:8000
```

Browser should ask for Basic Auth credentials.

### 5. Install daily cron

Set server timezone:

```bash
sudo timedatectl set-timezone Asia/Seoul
timedatectl
```

Open crontab:

```bash
sudo -u stockagent crontab -e
```

Paste:

```cron
45 15 * * 1-5 cd /opt/stock-agent && /opt/stock-agent/scripts/run_daily.sh
30 14 * * 1-5 cd /opt/stock-agent && /opt/stock-agent/scripts/update_universe.sh >> logs/universe.out.log 2>> logs/universe.err.log
```

### 6. Useful operations

Restart web:

```bash
sudo systemctl restart stock-agent
```

View web logs:

```bash
journalctl -u stock-agent -n 100 --no-pager
```

View daily run logs:

```bash
ls -lt /opt/stock-agent/logs
tail -n 100 /opt/stock-agent/logs/*.err.log
```

Manual daily run:

```bash
cd /opt/stock-agent
./scripts/run_daily.sh
```

The task runs:

```powershell
scripts\run_daily.ps1
```

## Required API notes

- OpenDART financial statement endpoint: `https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json`
- NAVER news search endpoint: `https://openapi.naver.com/v1/search/news.json`
- KIS daily candle endpoint used by default: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`

KIS field names can change by endpoint or environment. The adapter keeps those mappings isolated in `app/providers/kis.py`.

The KIS adapter uses daily candles rather than current price so the selector uses regular-session close data. It calculates daily change from the latest candle close and previous candle close. If the API response does not include accumulated trading value, it falls back to `close * accumulated volume`.

Scheduled runs write logs under `logs/`.
