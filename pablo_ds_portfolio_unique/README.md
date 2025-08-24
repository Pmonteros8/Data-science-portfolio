
# Streaming & Consumer Trends — Dashboard

An interactive Streamlit app that analyzes macroeconomic pressures (interest rates, CPI) alongside streaming industry trends (adoption, viewing share, pricing, subscriptions).

## Quick Start (Local)

```bash
git clone <your-repo-url>.git
cd streaming-consumer-repo
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamingconsumer.py
```

The app will look for default datasets under `data/`, but you can upload your own CSVs from the sidebar.

## Included Data (sample/optional)
- `data/consumer_shift_dataset.csv` — annual adoption, viewing, costs, CPI (2015–2025).
- `data/streaming_pivot.csv` — date×service price series from Kaggle.
- `data/fedfunds_clean.csv` — monthly Fed Funds rate (2018–2025).
- `data/CUUR0000SERA02.csv` — CPI for Cable/Satellite/Live Streaming TV (source series).
- `data/consumer_shift_onepager.pdf` — one-page summary for case studies.

## Deploy to Streamlit Cloud

1. Push this folder to GitHub.
2. In Streamlit Cloud, create a new app:
   - Repository: `your-user/your-repo`
   - Branch: `main`
   - File: `streamingconsumer.py`
3. (Optional) Add secrets in **Settings → Secrets** if you later connect to APIs.

## Generic PaaS Deployment (Procfile)
A simple `Procfile` is included for platforms that expect a web process:
```
web: streamlit run streamingconsumer.py --server.port $PORT --server.address 0.0.0.0
```

## Customize
- Replace example data with your own time series for production-grade analysis.
- Update visuals or add new sections in `streamingconsumer.py`.
- Keep `requirements.txt` pinned if you want reproducible builds.

## License
MIT (add your preferred license here).
