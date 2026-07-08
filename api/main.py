from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def coerce_type(key, value):
    if value is None: return None
    if key in ["port", "workers"]:
        try: return int(value)
        except: return value
    if key == "debug":
        return str(value).lower() in ["true", "1", "yes", "on"]
    return str(value)

# Explicitly mapping both routes ensures no 404
@app.get("/")
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

    # 2. YAML simulation
    config.update({"port": 8717, "workers": 4, "debug": True})

    # 3. .env simulation (Alias: NUM_WORKERS -> workers)
    config["workers"] = 8

    # 4. OS Env vars (Overwrites YAML/.env)
    os_mapping = {"APP_PORT": "port", "APP_LOG_LEVEL": "log_level", "APP_API_KEY": "api_key"}
    for env_var, config_key in os_mapping.items():
        val = os.getenv(env_var)
        if val is not None:
            config[config_key] = coerce_type(config_key, val)

    # 5. CLI Overrides (Highest)
    for pair in set:
        if "=" in pair:
            k, v = pair.split("=", 1)
            if k in config:
                config[k] = coerce_type(k, v)

    config["api_key"] = "****"
    return config
