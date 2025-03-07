from os import getenv
from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.joinpath(".env"))

hoogle_root_dir = getenv("HOOGLE_ROOT_DIR")

if hoogle_root_dir is None:
    print("HOOGLE_ROOT_DIR not found, defaulting to ~")
    hoogle_root_dir = Path.home()

hoogle_root_dir = Path(hoogle_root_dir).joinpath(".hoogle")

hoogle_root_dir.mkdir(exist_ok=True)

hoogle_server = FastAPI()

@hoogle_server.get("/root")
async def root():
    return {"root": hoogle_root_dir}

@hoogle_server.get("/user_dirs")
async def user_dirs():
    return {"folders": list(hoogle_root_dir.iterdir())}