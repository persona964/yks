# YKS Tracker

Minimal web app to track YKS study progress. Backend is a FastAPI service using SQLite, frontend is React served as static files.

## Running

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Open `frontend/index.html` in a browser. The app will fetch data from the API.
