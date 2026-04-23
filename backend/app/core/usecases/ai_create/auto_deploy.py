from __future__ import annotations
import os
import tempfile
import zipfile
import threading

from app.config import settings
from app.container import Container, build_container
from app.infra.db.database import SessionLocal
from app.infra.db.repos.ai_creation_repo import AICreationRepo


class AutoDeployService:
    def __init__(self) -> None:
        self._active_tasks: dict[int, threading.Thread] = {}

    def start_deploy(self, creation_id: int, user_id: int,
                     requirements: dict, generated_code: dict[str, str]) -> None:
        def run():
            db = SessionLocal()
            try:
                repo = AICreationRepo(db)
                self._do_deploy(creation_id, user_id, requirements, generated_code, repo)
            except Exception as e:
                try:
                    repo.update_status(creation_id, "failed", error=str(e))
                except Exception:
                    pass
            finally:
                db.close()

        thread = threading.Thread(target=run, daemon=True)
        self._active_tasks[creation_id] = thread
        thread.start()

    def _do_deploy(self, creation_id: int, user_id: int,
                   requirements: dict, code: dict[str, str],
                   repo: AICreationRepo) -> None:

        app_name = requirements.get("app_name", "AI创建应用")
        slug = f"ai-{creation_id}-{self._slugify(app_name)}"

        try:
            repo.update_status(creation_id, "generating", progress=10,
                               message="正在创建应用记录...")

            c = build_container(repo._db)

            app_result = c.create_app.execute(
                name=app_name,
                slug=slug,
                description=requirements.get("app_description", ""),
                owner_id=user_id,
            )
            app_id = app_result["id"]

            repo.update_status(creation_id, "generating", progress=20,
                               message="正在打包代码...", app_id=app_id)

            tmp_dir = tempfile.mkdtemp()
            zip_path = ""
            try:
                for filename, content in code.items():
                    filepath = os.path.join(tmp_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)

                zip_path = os.path.join(tmp_dir, "code.zip")
                with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                    for filename in code.keys():
                        zf.write(os.path.join(tmp_dir, filename), filename)

                repo.update_status(creation_id, "generating", progress=35,
                                   message="正在上传代码...")

                c.upload_code.execute(
                    app_id=app_id,
                    zip_path=zip_path,
                    current_user_id=user_id,
                    current_user_role="admin",
                )

            finally:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)

            repo.update_status(creation_id, "building", progress=50,
                               message="正在构建和部署应用...")

            c.deploy_app.validate(app_id, user_id, "admin")
            c.deploy_app.run_deploy(app_id)

            repo.update_status(creation_id, "running", progress=100,
                               message="部署完成！")

        except Exception as e:
            repo.update_status(creation_id, "failed",
                               error=f"部署失败: {str(e)}")
            raise

    @staticmethod
    def _slugify(name: str) -> str:
        import re
        name = name.lower().strip()
        name = re.sub(r'[^\w\u4e00-\u9fff-]', '-', name)
        name = re.sub(r'-+', '-', name)
        return name[:30].rstrip('-') or 'app'