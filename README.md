
# SPAFS Crisis Dashboard – Deploy Guide (API-only HDX)

This Streamlit app shows daily-updating indicators for Sudan and is branded for the Sudan Platform for Agriculture and Food Security (SPAFS). It uses **HDX CKAN Datastore API only** (no CSV files).

## Quick start
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment variables (optional but recommended)
```
# Branding / actions
SPAFS_DONATE_URL=https://spafs.org/donate
SPAFS_RSVP_URL=https://spafs.org/rsvp
SPAFS_CONTACT_EMAIL=hello@spafs.org
SPAFS_LOGO=/app/spafs_logo.png              # if you add a logo file
SPAFS_SNAPSHOT_PATH=/app/snapshots.csv      # time-series persistence

# Email alerts (optional)
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=your_user
SMTP_PASS=your_password
ALERT_TO=alerts@spafs.org
ALERT_FROM=dashboard@spafs.org
ALERT_THRESHOLD_IDPS=150000
ALERT_THRESHOLD_REFUGEES=100000
```

## Hosting on Streamlit Cloud (fastest)
1. Push `app.py` and `requirements.txt` to a GitHub repo.
2. On Streamlit Cloud: Create new app → select your repo.
3. Add the environment variables above (at least the SPAFS_* ones).
4. Deploy — you’ll get a public URL like `https://spafs-dashboard.streamlit.app`.
5. Later, point a subdomain like `dashboard.spafs.org` to that URL (set a CNAME in your DNS).

## What’s included (latest build)
- English/Arabic language toggle
- **HDX Datastore API** for IDPs (IOM DTM) — no CSVs
- UNHCR refugees from Sudan (by asylum country; ISO3)
- Host Country Stats: Egypt (EGY), Chad (TCD), South Sudan (SSD)
- Email alert scaffolding for significant jumps in IDPs or refugees (uses SMTP envs)
- Daily snapshots to support future trend charts
- SPAFS branding placeholders and links
