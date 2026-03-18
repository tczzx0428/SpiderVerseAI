from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expire_seconds: int = 86400
    upload_dir: str = "/uploads/apps"
    host_upload_dir: str = "/uploads/apps"  # 宿主机绝对路径，用于给 App 容器挂卷
    traefik_dynamic_dir: str = "/traefik-dynamic"
    host_ip: str = "host.docker.internal"
    port_range_start: int = 8600
    port_range_end: int = 9600
    team_api_key: str = ""
    team_base_url: str = ""
    codex_model: str = "gpt-5.2-codex"
    openclaw_model: str = "gpt-5.2"
    allowed_origins: str = ""  # Comma-separated allowed CORS origins; empty = "*"

    class Config:
        env_file = ".env"


settings = Settings()
