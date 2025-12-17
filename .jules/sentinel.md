## 2024-02-14 - Overly Permissive CORS Configuration
**Vulnerability:** The FastAPI application in `lemming/api.py` was configured with `allow_origins=["*"]` along with `allow_credentials=True`. This is a dangerous configuration that allows any website to make authenticated requests to the API if the server reflects the origin (which Starlette does in this config) or simply misleads developers into thinking it's safe.
**Learning:** Default templates or quick-start guides often use `allow_origins=["*"]` for convenience, but this should never be used in production, especially with credentials. It defeats the purpose of SOP.
**Prevention:** Use an environment variable (e.g., `ALLOWED_ORIGINS`) to strictly define allowed origins. Default to localhost only for development.
