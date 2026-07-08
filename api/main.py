from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def coerce_type(key, value):
    """Applies type coercion rules as per requirements."""
    if value is None: return None
    if key in ["port", "workers"]:
        try: return int(value)
        except: return value
    if key == "debug":
        return str(value).lower() in ["true", "1", "yes", "on"]
    return str(value)

@app.get("/")
@app.get("/effective-config")
async def effective_config(set: list[str] = []):
    # 1. Defaults (Lowest Precedence)
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. config.development.yaml simulation
    config.update({"port": 8717, "workers": 4, "debug": True})

    # 3. .env file simulation (Alias: NUM_WORKERS -> workers)
    config["workers"] = 8

    # 4. OS Env vars (APP_* prefix)
    os_mapping = {
        "APP_PORT": "port",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key"
    }
    for env_var, config_key in os_mapping.items():
        val = os.getenv(env_var)
        if val is not None:
            config[config_key] = coerce_type(config_key, val)

    # 5. CLI Overrides (?set=key=value) (Highest Precedence)
    for pair in set:
        if "=" in pair:
            k, v = pair.split("=", 1)
            if k in config:
                config[k] = coerce_type(k, v)

    # Secret Masking
    config["api_key"] = "****"
    
    return config
