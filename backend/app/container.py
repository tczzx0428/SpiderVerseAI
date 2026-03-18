from __future__ import annotations
"""DI Container: assembles all use cases and their dependencies.

Usage in routes:
    from app.container import build_container
    c = build_container(db)
    result = c.list_apps.execute(page=1, size=20)
"""
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.strategies.password_auth import PasswordAuth
from app.core.strategies.streamlit_runtime import StreamlitRuntime
from app.core.usecases.admin.create_user import BatchCreateUsers, CreateUser
from app.core.usecases.admin.get_dashboard_stats import GetDashboardStats
from app.core.usecases.admin.manage_skills import DeleteSkill, ListSkillsAdmin, UpsertSkill
from app.core.usecases.admin.manage_team_config import UpdateTeamConfig
from app.core.usecases.admin.update_user import DeleteUser, UpdateUser
from app.core.usecases.app.create_app import CreateApp
from app.core.usecases.app.delete_app import DeleteApp
from app.core.usecases.app.deploy_app import DeployApp
from app.core.usecases.app.get_app import GetApp, GetAppBySlug
from app.core.usecases.app.get_app_logs import GetAppLogs
from app.core.usecases.app.list_apps import ListApps
from app.core.usecases.app.restart_app import RestartApp
from app.core.usecases.app.stop_app import StopApp
from app.core.usecases.app.update_app import UpdateApp
from app.core.usecases.app.upload_code import UploadCode
from app.core.usecases.auth.change_password import ChangePassword
from app.core.usecases.auth.get_team_config import GetTeamConfig
from app.core.usecases.auth.list_skills import ListSkills
from app.core.usecases.auth.login import Login
from app.core.usecases.auth.verify_app_access import VerifyAppAccess
from app.core.usecases.config.manage_template import GetTemplate, GetTemplateHistory, UpdateTemplate
from app.core.usecases.history.download_file import DownloadFile
from app.core.usecases.history.get_app_history import GetAppHistory
from app.core.usecases.history.list_all_files import ListAllFiles
from app.core.usecases.history.list_all_runs import ListAllRuns
from app.core.usecases.history.list_grouped_runs import ListGroupedRuns
from app.core.usecases.history.record_run import RecordRun
from app.core.usecases.history.record_view import RecordView
from app.core.usecases.prompt.manage_prompts import CreatePrompt, DeletePrompt, ListPrompts, UpdatePrompt
from app.core.usecases.stats.get_stats import GetStats
from app.infra.auth.jwt_auth import JwtAuthProvider
from app.infra.db.repos.app_repo import SqlAlchemyAppRepo
from app.infra.db.repos.config_repo import SqlAlchemyConfigRepo
from app.infra.db.repos.prompt_repo import SqlAlchemyPromptRepo
from app.infra.db.repos.user_repo import SqlAlchemyUserRepo
from app.infra.services.docker_runtime import DockerContainerRuntime
from app.infra.services.nginx_route_manager import NginxRouteManager
from app.infra.storage.filesystem import LocalFileStorage

# Default template stored in config.py router — import it
from app.core.usecases.config.manage_template import TEMPLATE_KEY  # noqa: F401

# We store the default template as a module-level constant to avoid circular imports
# It's loaded from the original routers/config.py DEFAULT_TEMPLATE
_DEFAULT_TEMPLATE = None


def _get_default_template() -> str:
    global _DEFAULT_TEMPLATE
    if _DEFAULT_TEMPLATE is None:
        # Read from the default_code_rules file or fallback to inline
        from pathlib import Path
        rules_path = Path(__file__).parent / "core" / "shared" / "default_code_rules.md"
        if rules_path.exists():
            _DEFAULT_TEMPLATE = rules_path.read_text(encoding="utf-8")
        else:
            _DEFAULT_TEMPLATE = "# 代码规范模板\n\n请在管理后台配置。"
    return _DEFAULT_TEMPLATE


# Singletons for infra services that don't need per-request state
_docker_runtime = None
_route_manager = None
_storage = None
_auth_provider = None
_streamlit_runtime = None


def _get_docker_runtime() -> DockerContainerRuntime:
    global _docker_runtime
    if _docker_runtime is None:
        _docker_runtime = DockerContainerRuntime()
    return _docker_runtime


def _get_route_manager() -> NginxRouteManager:
    global _route_manager
    if _route_manager is None:
        _route_manager = NginxRouteManager()
    return _route_manager


def _get_storage() -> LocalFileStorage:
    global _storage
    if _storage is None:
        _storage = LocalFileStorage()
    return _storage


def _get_auth_provider() -> JwtAuthProvider:
    global _auth_provider
    if _auth_provider is None:
        _auth_provider = JwtAuthProvider()
    return _auth_provider


def _get_streamlit_runtime() -> StreamlitRuntime:
    global _streamlit_runtime
    if _streamlit_runtime is None:
        _streamlit_runtime = StreamlitRuntime()
    return _streamlit_runtime


@dataclass
class Container:
    # App use cases
    list_apps: ListApps
    create_app: CreateApp
    get_app: GetApp
    get_app_by_slug: GetAppBySlug
    update_app: UpdateApp
    upload_code: UploadCode
    deploy_app: DeployApp
    stop_app: StopApp
    restart_app: RestartApp
    delete_app: DeleteApp
    get_app_logs: GetAppLogs

    # History use cases
    list_grouped_runs: ListGroupedRuns
    list_all_runs: ListAllRuns
    list_all_files: ListAllFiles
    get_app_history: GetAppHistory
    record_view: RecordView
    record_run: RecordRun
    download_file: DownloadFile

    # Auth use cases
    login: Login
    change_password: ChangePassword
    verify_app_access: VerifyAppAccess
    get_team_config: GetTeamConfig
    list_skills: ListSkills

    # Admin use cases
    create_user: CreateUser
    batch_create_users: BatchCreateUsers
    update_user: UpdateUser
    delete_user: DeleteUser
    upsert_skill: UpsertSkill
    delete_skill: DeleteSkill
    list_skills_admin: ListSkillsAdmin
    update_team_config: UpdateTeamConfig
    get_dashboard_stats: GetDashboardStats

    # Config use cases
    get_template: GetTemplate
    update_template: UpdateTemplate
    get_template_history: GetTemplateHistory

    # Stats use cases
    get_stats: GetStats

    # Prompt use cases
    list_prompts: ListPrompts
    create_prompt: CreatePrompt
    update_prompt: UpdatePrompt
    delete_prompt: DeletePrompt


def build_container(db: Session) -> Container:
    """Build a Container with all use cases wired to the given DB session."""
    # Repos (per-request, tied to db session)
    app_repo = SqlAlchemyAppRepo(db)
    user_repo = SqlAlchemyUserRepo(db)
    config_repo = SqlAlchemyConfigRepo(db)
    prompt_repo = SqlAlchemyPromptRepo(db)

    # Infra singletons
    docker_rt = _get_docker_runtime()
    route_mgr = _get_route_manager()
    storage = _get_storage()
    auth_prov = _get_auth_provider()
    streamlit_rt = _get_streamlit_runtime()

    # Auth strategy
    password_auth = PasswordAuth(user_repo, auth_prov)

    default_tpl = _get_default_template()

    return Container(
        # App
        list_apps=ListApps(app_repo, user_repo),
        create_app=CreateApp(app_repo, user_repo),
        get_app=GetApp(app_repo, user_repo),
        get_app_by_slug=GetAppBySlug(app_repo, user_repo),
        update_app=UpdateApp(app_repo, user_repo),
        upload_code=UploadCode(app_repo, storage),
        deploy_app=DeployApp(app_repo, docker_rt, route_mgr, streamlit_rt),
        stop_app=StopApp(app_repo, docker_rt, route_mgr),
        restart_app=RestartApp(app_repo, docker_rt, route_mgr),
        delete_app=DeleteApp(app_repo, docker_rt, route_mgr, storage),
        get_app_logs=GetAppLogs(app_repo),
        # History
        list_grouped_runs=ListGroupedRuns(app_repo),
        list_all_runs=ListAllRuns(app_repo),
        list_all_files=ListAllFiles(app_repo),
        get_app_history=GetAppHistory(app_repo),
        record_view=RecordView(app_repo),
        record_run=RecordRun(app_repo),
        download_file=DownloadFile(app_repo),
        # Auth
        login=Login(password_auth, auth_prov),
        change_password=ChangePassword(user_repo, auth_prov),
        verify_app_access=VerifyAppAccess(auth_prov),
        get_team_config=GetTeamConfig(config_repo),
        list_skills=ListSkills(config_repo),
        # Admin
        create_user=CreateUser(user_repo, auth_prov),
        batch_create_users=BatchCreateUsers(user_repo, auth_prov),
        update_user=UpdateUser(user_repo),
        delete_user=DeleteUser(user_repo),
        upsert_skill=UpsertSkill(config_repo),
        delete_skill=DeleteSkill(config_repo),
        list_skills_admin=ListSkillsAdmin(config_repo),
        update_team_config=UpdateTeamConfig(config_repo),
        get_dashboard_stats=GetDashboardStats(app_repo, user_repo),
        # Config
        get_template=GetTemplate(config_repo, default_tpl),
        update_template=UpdateTemplate(config_repo, default_tpl),
        get_template_history=GetTemplateHistory(config_repo),
        # Stats
        get_stats=GetStats(app_repo, user_repo),
        # Prompt
        list_prompts=ListPrompts(prompt_repo),
        create_prompt=CreatePrompt(prompt_repo),
        update_prompt=UpdatePrompt(prompt_repo),
        delete_prompt=DeletePrompt(prompt_repo),
    )
