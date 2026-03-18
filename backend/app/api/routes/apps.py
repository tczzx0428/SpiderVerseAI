from __future__ import annotations
import os
import tempfile

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_container, get_current_user, get_db
from app.api.schemas.app import AppCreate, AppListResponse, AppUpdate
from app.api.schemas.user import UserOut
from app.container import Container, build_container
from app.infra.db.database import SessionLocal
from app.infra.db.models.user import User

router = APIRouter(prefix="/api/apps", tags=["apps"])

MAX_ZIP_SIZE = 100 * 1024 * 1024


@router.get("", response_model=AppListResponse)
def list_apps(page: int = 1, size: int = 20, status: str = None,
              c: Container = Depends(get_container)):
    result = c.list_apps.execute(page=page, size=size, status=status)
    for item in result["items"]:
        if item["owner"]:
            item["owner"] = UserOut.model_validate(item["owner"])
    return result


@router.post("", status_code=201)
def create_app(body: AppCreate, c: Container = Depends(get_container),
               current_user: User = Depends(get_current_user)):
    result = c.create_app.execute(body.name, body.slug, body.description, current_user.id)
    if result["owner"]:
        result["owner"] = UserOut.model_validate(result["owner"])
    return result


@router.get("/by-slug/{slug}")
def get_app_by_slug(slug: str, c: Container = Depends(get_container),
                    current_user: User = Depends(get_current_user)):
    result = c.get_app_by_slug.execute(slug)
    if result["owner"]:
        result["owner"] = UserOut.model_validate(result["owner"])
    return result


@router.get("/history/runs")
def list_all_runs(c: Container = Depends(get_container),
                  current_user: User = Depends(get_current_user)):
    return c.list_all_runs.execute(current_user.username, current_user.role)


@router.get("/history/files")
def list_all_files(c: Container = Depends(get_container),
                   current_user: User = Depends(get_current_user)):
    return c.list_all_files.execute(current_user.id, current_user.role)


@router.get("/history/grouped")
def list_grouped_runs(c: Container = Depends(get_container),
                      current_user: User = Depends(get_current_user)):
    return c.list_grouped_runs.execute(current_user.id, current_user.role)


@router.post("/internal/view/{app_id}")
def record_view(app_id: int, body: dict = None,
                c: Container = Depends(get_container)):
    username = (body or {}).get("username", "anonymous")
    return c.record_view.execute(app_id, username)


@router.post("/internal/run/{app_id}")
def record_run(app_id: int, body: dict = None,
               c: Container = Depends(get_container)):
    username = (body or {}).get("username", "anonymous")
    return c.record_run.execute(app_id, username)


@router.get("/{app_id}")
def get_app(app_id: int, c: Container = Depends(get_container),
            current_user: User = Depends(get_current_user)):
    result = c.get_app.execute(app_id)
    if result["owner"]:
        result["owner"] = UserOut.model_validate(result["owner"])
    return result


@router.patch("/{app_id}")
def update_app(app_id: int, body: AppUpdate, c: Container = Depends(get_container),
               admin: User = Depends(get_current_user)):
    result = c.update_app.execute(app_id, body.name, body.description, body.owner_id)
    if result["owner"]:
        result["owner"] = UserOut.model_validate(result["owner"])
    return result


@router.post("/{app_id}/upload")
async def upload_zip(app_id: int, file: UploadFile,
                     c: Container = Depends(get_container),
                     current_user: User = Depends(get_current_user)):
    if file.content_type not in ("application/zip", "application/x-zip-compressed"):
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="只支持 .zip 格式")

    content = await file.read()
    if len(content) > MAX_ZIP_SIZE:
        raise HTTPException(status_code=400, detail="文件过大，最大支持 100 MB")

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        return c.upload_code.execute(app_id, tmp_path, current_user.id, current_user.role)
    finally:
        os.unlink(tmp_path)


@router.post("/{app_id}/deploy", status_code=202)
def deploy(app_id: int, background_tasks: BackgroundTasks,
           c: Container = Depends(get_container),
           current_user: User = Depends(get_current_user)):
    result = c.deploy_app.validate(app_id, current_user.id, current_user.role)

    def run_deploy():
        bg_db = SessionLocal()
        try:
            bg_c = build_container(bg_db)
            bg_c.deploy_app.run_deploy(app_id)
        finally:
            bg_db.close()

    background_tasks.add_task(run_deploy)
    return result


@router.post("/{app_id}/stop")
def stop_app(app_id: int, c: Container = Depends(get_container),
             current_user: User = Depends(get_current_user)):
    return c.stop_app.execute(app_id, current_user.id, current_user.role)


@router.post("/{app_id}/restart")
def restart_app(app_id: int, c: Container = Depends(get_container),
                current_user: User = Depends(get_current_user)):
    return c.restart_app.execute(app_id, current_user.id, current_user.role)


@router.delete("/{app_id}", status_code=204)
def delete_app(app_id: int, c: Container = Depends(get_container),
               current_user: User = Depends(get_current_user)):
    c.delete_app.execute(app_id, current_user.id, current_user.role)


@router.get("/{app_id}/history")
def get_history(app_id: int, c: Container = Depends(get_container),
                current_user: User = Depends(get_current_user)):
    return c.get_app_history.execute(app_id, current_user.username, current_user.role)


@router.get("/{app_id}/outputs/{run_id}/{filename}")
def download_output(app_id: int, run_id: str, filename: str,
                    c: Container = Depends(get_container),
                    current_user: User = Depends(get_current_user)):
    path = c.download_file.get_output_path(app_id, run_id, filename,
                                           current_user.id, current_user.role)
    return FileResponse(path=path, filename=filename)


@router.get("/{app_id}/files/{file_path:path}")
def download_data_file(app_id: int, file_path: str,
                       c: Container = Depends(get_container),
                       current_user: User = Depends(get_current_user)):
    path = c.download_file.get_data_file_path(app_id, file_path,
                                              current_user.id, current_user.role)
    return FileResponse(path=path, filename=path.name)


@router.get("/{app_id}/logs")
def get_logs(app_id: int, c: Container = Depends(get_container),
             current_user: User = Depends(get_current_user)):
    return c.get_app_logs.execute(app_id)
