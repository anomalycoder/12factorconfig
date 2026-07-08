from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# God-Mode CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def coerce_type(key, value):
    if value is None: return None
    if key in ["port", "workers"]:
        return int(value)
    if key == "debug":
        return str(value).lower() in ["true", "1", "yes", "on"]
    return str(value)

@app.get("/effective-config")
async def effective_config(set: list[str] = []):
    # 1. Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. config.development.yaml layer (Simulated)
    config.update({"port": 8717, "workers": 4, "debug": True})

    # 3. .env layer (Simulated)
    # Alias: NUM_WORKERS maps to workers
    config["workers"] = 8

    # 4. OS Env layer (APP_* prefix)
    os_vars = {
        "port": os.getenv("APP_PORT"),
        "log_level": os.getenv("APP_LOG_LEVEL"),
        "api_key": os.getenv("APP_API_KEY")
    }
    for k, v in os_vars.items():
        if v: config[k] = coerce_type(k, v)

    # 5. CLI Overrides (?set=key=value)
    for pair in set:
        if "=" in pair:
            k, v = pair.split("=", 1)
            if k in config:
                config[k] = coerce_type(k, v)

    # Final Masking
    config["api_key"] = "****"
    
    return config
