import os
import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def coerce_type(key, val):
    if key in ["port", "workers"]:
        return int(val)
    if key == "debug":
        if isinstance(val, bool): return val
        return str(val).lower() in ("true", "1", "yes", "on")
    return str(val)

@app.get("/")
@app.get("/effective-config")
@app.get("/api/effective-config")
def get_effective_config(set: Optional[List[str]] = Query(None)):
    # LAYER 1: Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }

    # Resolve absolute paths to guarantee Vercel finds the files
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # LAYER 2: YAML Config
    yaml_paths = [os.path.join(BASE_DIR, "config.development.yaml"), "config.development.yaml"]
    for yp in yaml_paths:
        if os.path.exists(yp):
            with open(yp, "r") as f:
                config.update(yaml.safe_load(f) or {})
            break

    # LAYER 3: .env file mapping
    env_paths = [os.path.join(BASE_DIR, ".env"), ".env"]
    for ep in env_paths:
        if os.path.exists(ep):
            with open(ep, "r") as f:
                for line in f:
                    if "=" in line and not line.strip().startswith("#"):
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        # Alias Check
                        if k == "NUM_WORKERS":
                            config["workers"] = v
                        else:
                            config[k.lower()] = v
            break

    # LAYER 4: OS Environment Variables
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            config_key = k[4:].lower()
            config[config_key] = v

    # LAYER 5: CLI Overrides
    if set:
        for override in set:
            if "=" in override:
                k, v = override.split("=", 1)
                config[k] = v

    # Final Step: Coercion and Masking
    final_config = {}
    for k, v in config.items():
        final_config[k] = coerce_type(k, v)

    final_config["api_key"] = "****"

    return final_config
