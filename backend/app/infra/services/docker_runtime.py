from __future__ import annotations
import socket
from pathlib import Path

import docker

from app.config import settings
from app.core.strategies.app_runtime import IAppRuntime


class DockerContainerRuntime:
    def __init__(self) -> None:
        self._client = docker.from_env()

    def build_and_run(self, app_id: int, slug: str, build_path: str,
                      runtime: IAppRuntime | None = None) -> dict:
        image_tag = f"tool-platform/app-{app_id}:{slug}"
        container_name = f"app_{app_id}_{slug}"
        bp = Path(build_path)

        # Inject Dockerfile from runtime strategy
        if runtime:
            dockerfile_content = runtime.generate_dockerfile(slug, build_path)
            bp.joinpath("Dockerfile").write_text(dockerfile_content)
            for fname, content in runtime.get_entrypoint_files():
                (bp / fname).write_text(content, encoding="utf-8")
            container_port = runtime.get_container_port()
        else:
            container_port = 8501

        # Build image
        build_logs = []
        try:
            _, log_iter = self._client.images.build(
                path=build_path, tag=image_tag, rm=True, forcerm=True,
            )
            for chunk in log_iter:
                if "stream" in chunk:
                    build_logs.append(chunk["stream"])
                if "error" in chunk:
                    build_logs.append(f"ERROR: {chunk['error']}\n")
        except docker.errors.BuildError as e:
            for line in e.build_log:
                if "stream" in line:
                    build_logs.append(line["stream"])
                if "error" in line:
                    build_logs.append(f"ERROR: {line['error']}\n")
            raise RuntimeError("".join(build_logs)) from e

        host_port = self._find_free_port()

        # Remove old container
        try:
            old = self._client.containers.get(container_name)
            old.stop()
            old.remove()
        except docker.errors.NotFound:
            pass

        # Prepare data directory
        data_dir_host = Path(settings.host_upload_dir) / str(app_id) / "data"
        data_dir_container = Path(settings.upload_dir) / str(app_id) / "data"
        data_dir_container.mkdir(parents=True, exist_ok=True)

        container = self._client.containers.run(
            image=image_tag, name=container_name, detach=True,
            ports={f"{container_port}/tcp": host_port},
            volumes={str(data_dir_host): {"bind": "/app/data", "mode": "rw"}},
            environment={"HOST_IP": settings.host_ip, "PE_APP_ID": str(app_id)},
            labels={"tool-platform.app_id": str(app_id), "tool-platform.slug": slug},
            restart_policy={"Name": "unless-stopped"},
        )

        return {
            "container_id": container.id,
            "container_name": container_name,
            "host_port": host_port,
            "build_log": "".join(build_logs),
        }

    def stop(self, container_name: str) -> None:
        try:
            self._client.containers.get(container_name).stop()
        except docker.errors.NotFound:
            pass

    def restart(self, container_name: str) -> None:
        try:
            self._client.containers.get(container_name).restart()
        except docker.errors.NotFound:
            raise RuntimeError(f"容器 {container_name} 不存在，请重新部署")

    def remove(self, container_name: str) -> None:
        try:
            c = self._client.containers.get(container_name)
            c.stop()
            c.remove()
        except docker.errors.NotFound:
            pass

    def _find_free_port(self) -> int:
        used_ports: set[int] = set()
        for container in self._client.containers.list():
            for port_bindings in container.ports.values():
                if port_bindings:
                    for binding in port_bindings:
                        try:
                            used_ports.add(int(binding["HostPort"]))
                        except (KeyError, ValueError):
                            pass

        for port in range(settings.port_range_start, settings.port_range_end):
            if port not in used_ports:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    if s.connect_ex(("localhost", port)) != 0:
                        return port
        raise RuntimeError("端口池已耗尽，无可用端口")
