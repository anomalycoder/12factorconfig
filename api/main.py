import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)

@app.get("/effective-config")
def get_effective_config(set: Optional[List[str]] = Query(None)):
    # 1. Defaults (Lowest Precedence)
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # 2. YAML Config
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f) or {}
            config.update(yaml_config)
    elif os.path.exists("../config.development.yaml"): 
        # Fallback in case Vercel runs the script from inside the api/ folder
        with open("../config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f) or {}
            config.update(yaml_config)

    # 3. .env file (Safe to skip on Vercel if not present)
    env_paths = [".env", "../.env"]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k == "NUM_WORKERS":
                            config["workers"] = v
                        else:
                            config[k.lower()] = v
            break

    # 4. OS Environment Variables (Vercel UI variables)
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            config_key = k[4:].lower()
            config[config_key] = v

    # 5. CLI Overrides (Highest Precedence)
    if set:
        for override in set:
            if "=" in override:
                k, v = override.split("=", 1)
                config[k] = v

    # Type Coercion & Masking
    final_config = {}
    for k, v in config.items():
        if k in ["port", "workers"]:
            final_config[k] = int(v)
        elif k == "debug":
            final_config[k] = parse_bool(v)
        elif k == "api_key":
            final_config[k] = "****"
        else:
            final_config[k] = str(v)

    final_config["api_key"] = "****"

    return final_config
