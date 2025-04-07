from os import getenv
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, status
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime
import io
import zipfile
from src.auth.auth import router
import os

load_dotenv(Path(__file__).parent.parent.joinpath(".env"))

hoogle_root_dir = getenv("HOOGLE_ROOT_DIR")

if hoogle_root_dir is None:
    print("HOOGLE_ROOT_DIR not found, defaulting to ~")
    hoogle_root_dir = Path.home()

hoogle_root_dir = Path(hoogle_root_dir).joinpath(".hoogle")

hoogle_root_dir.mkdir(exist_ok=True)

hoogle_server = FastAPI(openapi_tags=[{
    "name": "auth_required",
    "description": "These endpoint require users to be logged in."
}])
hoogle_server.include_router(router)

origins = [
    "http://localhost:3000"
]

hoogle_server.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Error(BaseModel):
    error: str

@hoogle_server.post("/upload/{path}", status_code=status.HTTP_201_CREATED, responses={status.HTTP_400_BAD_REQUEST: {"model": Error}, status.HTTP_409_CONFLICT: {"model": Error}}, tags=["auth_required"])
async def upload_file(path: Path, file: UploadFile, force: bool = False):
    local_parent_path = hoogle_root_dir.joinpath(path) # TODO dodac jeszcze jednego joinpath jak beda uzytkownicy - wezmie sie id uzytkownika z jwt

    if not local_parent_path.exists():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(Error(error=f"Folder '{path}' does not exist for current user")))

    local_file_path = local_parent_path.joinpath(file.filename)

    if not force and local_file_path.exists():
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=jsonable_encoder(Error(error=f"File '{file.filename}' already exists in '{path}'. Consider using force=true if you want to override")))

    with local_file_path.open("bw") as local_file:
        local_file.write(file.file.read())

@hoogle_server.get("/file", status_code=status.HTTP_200_OK, responses={status.HTTP_404_NOT_FOUND: {"model": Error}, status.HTTP_400_BAD_REQUEST: {"model": Error}}, tags=["auth_required"])
async def download_file(path: Path):
    local_file_path = hoogle_root_dir.joinpath(path)

    if not local_file_path.exists():
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(Error(error=f"File '{path}' does not exist")))

    if local_file_path.is_dir():
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, _, files in os.walk(local_file_path):
                for file in files:
                    file_path = Path(root) / file
                    archive_path = file_path.relative_to(local_file_path)
                    zip_file.write(file_path, archive_path.as_posix())


        memory_file.seek(0)
        return StreamingResponse(
            memory_file,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment;filename={local_file_path.name}.zip"
            },
        ) 
    
    return FileResponse(local_file_path)

@hoogle_server.delete("/file", status_code=status.HTTP_204_NO_CONTENT, responses={status.HTTP_404_NOT_FOUND: {"model": Error}, status.HTTP_400_BAD_REQUEST: {"model": Error}}, tags=["auth_required"])
async def delete_file(path: Path):
    local_file_path = hoogle_root_dir.joinpath(path)

    if not local_file_path.exists():
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(Error(error=f"File '{path}' does not exist")))

    if local_file_path.is_dir():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(Error(error=f"'{path}' is a directory")))
    
    local_file_path.unlink()

class FileInfo(BaseModel):
    name: str
    size: int
    created: str
    folder: bool

class ListDirResponse(BaseModel):
    files: list[FileInfo]

@hoogle_server.get("/list_dir", status_code=status.HTTP_200_OK, responses={status.HTTP_200_OK: {"model": ListDirResponse}, status.HTTP_404_NOT_FOUND: {"model": Error}, status.HTTP_400_BAD_REQUEST: {"model": Error}}, tags=["auth_required"])
async def list_dir(path: Path):
    local_folder_path = hoogle_root_dir.joinpath(path)

    if not local_folder_path.exists():
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=jsonable_encoder(Error(error=f"Folder '{path}' does not exist")))

    if not local_folder_path.is_dir():
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder(Error(error=f"'{path}' is a file")))
    
    return ListDirResponse(files=[FileInfo(name=file.name, size=file.stat().st_size, created=datetime.fromtimestamp(file.stat().st_mtime).isoformat(), folder=file.is_dir()) for file in local_folder_path.iterdir()])