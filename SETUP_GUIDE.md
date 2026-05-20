# Container Flow Visualiser — Demo Setup Guide

This folder is a self-contained demo version of the Port Container Flow Visualiser.
It uses synthetic sample data and has no database dependency.
The goal is to deploy it publicly on Streamlit Community Cloud so it can be
embedded on your personal website via an iframe.

---

## What's in this folder

| File | Purpose |
|---|---|
| `container_visualiser_demo.py` | The Streamlit app (no DB, no secrets needed) |
| `demo_data.py` | Generates ~2,000 realistic synthetic containers |
| `requirements.txt` | Python dependencies for deployment |
| `.streamlit/config.toml` | Forces dark theme automatically |
| `SETUP_GUIDE.md` | This file |

---

## Step 1 — Test locally first (optional but recommended)

```bash
cd path\to\container.visualisation.demo
pip install -r requirements.txt
streamlit run container_visualiser_demo.py
```

Open `http://localhost:8501` in your browser. You should see the Sankey diagram
with synthetic data. The default date range is the last 30 days — the sample data
always covers the last 90 days so there will always be data to show.

---

## Step 2 — Push to a public GitHub repo

1. Create a free account at https://github.com if you don't have one.
2. Create a **new public repository** (e.g. `container-flow-visualiser-demo`).
3. Copy only this folder's contents (not the whole Sys-Automation repo) into
   a local folder and initialise git:

```bash
git init
git add .
git commit -m "Initial demo app"
git remote add origin https://github.com/YOUR_USERNAME/container-flow-visualiser-demo.git
git push -u origin main
```

> **Important:** Do NOT include the original `container_visualiser.py` or the
> `.streamlit/secrets.toml` file from the production app. This repo only needs
> the files listed above.

---

## Step 3 — Deploy on Streamlit Community Cloud (free)

1. Go to **https://share.streamlit.io** and sign in with your GitHub account.
2. Click **"New app"**.
3. Select your repository (`container-flow-visualiser-demo`).
4. Set **Main file path** to: `container_visualiser_demo.py`
5. Leave the **Secrets** section completely blank (the demo needs no credentials).
6. Click **Deploy**.

Streamlit will install the dependencies from `requirements.txt` and launch the app.
This takes about 2–3 minutes the first time.

Once deployed you will get a permanent URL like:
```
https://your-username-container-flow-visualiser-demo-xxxx.streamlit.app
```

You can customise the URL slug in the app settings on the Streamlit dashboard.

**The app is now live 24/7 — you never need to run anything locally again.**
Streamlit hosts it on their servers. It restarts automatically if it goes idle.

---

## Step 4 — Embed on your personal website

Paste this snippet wherever you want the visualiser to appear on your site.
Replace the `src` URL with your actual deployed URL.

```html
<iframe
  src="https://YOUR-APP-URL.streamlit.app/?embed=true"
  width="100%"
  height="900"
  style="border: none; border-radius: 12px;"
  loading="lazy"
></iframe>
```

The `?embed=true` query parameter hides Streamlit's toolbar and footer so it
looks like a native part of your page rather than an embedded app.

Adjust `height` to taste — 850–950px works well for the default chart height.

---

## Notes

- **Sample data refreshes relative to today.** When the Streamlit server restarts
  (e.g. after a period of inactivity), `demo_data.py` regenerates dates relative
  to the current date, so the 30-day default filter always shows data.
- **Fixed random seed** means the structure (vessels, routes, volumes) is always
  the same — only the dates shift.
- The demo banner at the top of the page clearly states this is synthetic data,
  which is important for transparency on a public portfolio site.
- All sidebar filters (date range, vessel, flow direction, cargo category, berth
  grouping, volume threshold, layout) are fully interactive.
