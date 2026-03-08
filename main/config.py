import os
from dotenv import load_dotenv, dotenv_values

# ─── Load .env file ─────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_env_candidates = [
    os.path.join(_HERE, ".env"),
    os.path.join(os.getcwd(), ".env"),
]

_loaded = False
for _env_path in _env_candidates:
    if os.path.exists(_env_path):
        load_dotenv(_env_path, override=True)
        print(f"[ENV] Loaded .env from: {_env_path}")
        _loaded = True
        break

if not _loaded:
    print("[ENV] No .env file found. Relying on system environment variables.")

# ─── Configuration Variables ────────────────────────────────────────────────
CSV_PATH = os.getenv("CSV_PATH", os.path.join(_HERE, "nobroker_slow_scroll.csv"))
DB_PATH  = os.getenv("DB_PATH", os.path.join(_HERE, "nobroker.db"))

AZURE_OPENAI_API_KEY  = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT      = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1-mini-2")
AZURE_API_VERSION     = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AZURE_MAPS_KEY        = os.getenv("AZURE_MAPS_KEY")

# ─── Validate Required Keys ─────────────────────────────────────────────────
_missing = [
    name for name, val in {
        "AZURE_OPENAI_API_KEY":  AZURE_OPENAI_API_KEY,
        "AZURE_OPENAI_ENDPOINT": AZURE_OPENAI_ENDPOINT,
        "AZURE_MAPS_KEY":        AZURE_MAPS_KEY,
    }.items() if not val
]

if _missing:
    raise EnvironmentError(
        f"\n[STARTUP ERROR] Missing required environment variables: {', '.join(_missing)}\n"
        "Set them in a .env file next to app.py or export them in your shell."
    )

# Inject into os.environ so Agno / Azure SDK pick them up automatically
os.environ["AZURE_OPENAI_API_KEY"]  = AZURE_OPENAI_API_KEY
os.environ["AZURE_OPENAI_ENDPOINT"] = AZURE_OPENAI_ENDPOINT
os.environ["AZURE_MAPS_KEY"]        = AZURE_MAPS_KEY

print(f"[CONFIG] Environment successfully initialized.")