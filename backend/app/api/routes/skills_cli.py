"""CLI-friendly endpoints for openclaw to interact with the Skills marketplace.

Authentication: via `X-CLI-Token` header or `?token=` query param.
The token is stored in system_configs with key = "cli_token".
If no token is configured, CLI endpoints are open (for initial setup).

Usage from openclaw:
    GET  /api/cli/skills                  — list all skills
    GET  /api/cli/skills?q=keyword        — search skills
    GET  /api/cli/skills/{name}           — get skill detail
    GET  /api/cli/skills/{name}/install   — download & auto-extract zip (streams zip bytes)
"""
from __future__ import annotations

import io
import zipfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.api.deps import get_db
from app.infra.db.models.config import SystemConfig
from app.infra.db.repos.skill_repo import SkillRepo
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/cli/skills", tags=["skills-cli"])

SKILLS_STORAGE_DIR = __import__("pathlib").Path("/tmp/sv_skills")

CLI_TOKEN_KEY = "cli_token"


# ── Auth ──

def _verify_cli_token(request: Request, db: Session = Depends(get_db)):
    """Verify CLI token from header or query param. Skip if no token is configured."""
    row = db.query(SystemConfig).filter(SystemConfig.key == CLI_TOKEN_KEY).first()
    if not row or not row.value:
        # No token configured — allow open access
        return
    expected = row.value.strip()
    token = request.headers.get("X-CLI-Token") or request.query_params.get("token")
    if token != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing CLI token")


def _get_repo(db: Session = Depends(get_db)) -> SkillRepo:
    return SkillRepo(db)


def _get_skill_dir(name: str):
    return SKILLS_STORAGE_DIR / name


# ── Endpoints ──

@router.get("", dependencies=[Depends(_verify_cli_token)])
def cli_list_skills(
    q: str = Query("", description="Search keyword"),
    category: str = Query("", description="Filter by category"),
    repo: SkillRepo = Depends(_get_repo),
    db: Session = Depends(get_db),
):
    """List skills in a CLI-friendly compact format."""
    skills = repo.list_all()
    if q:
        q_lower = q.lower()
        skills = [
            s for s in skills
            if q_lower in s.name.lower()
            or q_lower in s.description.lower()
        ]
    if category:
        skills = [s for s in skills if s.category == category]
    skills.sort(key=lambda s: (-int(s.pinned), -s.installs, s.name))
    return [
        {
            "name": s.name,
            "version": s.version or "0.0.0",
            "category": s.category,
            "description": s.description,
            "downloads": s.installs,
            "author": s.author_name or "system",
            "pinned": s.pinned,
        }
        for s in skills
    ]


# ── Bootstrap: serve built-in openclaw-skills-guide (must be before /{name}) ──

import pathlib as _pathlib

_PROJECT_ROOT = _pathlib.Path(__file__).resolve().parents[4]
_BUILTIN_ZIP = _PROJECT_ROOT / "builtin_skills" / "openclaw-skills-guide.zip"


@router.get("/bootstrap/download", dependencies=[])
def cli_bootstrap_download():
    """Download the openclaw-skills-guide zip. No auth required."""
    if not _BUILTIN_ZIP.exists():
        raise HTTPException(status_code=404, detail="Bootstrap skill not found")
    buf = io.BytesIO(_BUILTIN_ZIP.read_bytes())
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="openclaw-skills-guide.zip"'},
    )


@router.get("/{name}", dependencies=[Depends(_verify_cli_token)])
def cli_skill_info(
    name: str,
    repo: SkillRepo = Depends(_get_repo),
):
    """Get detailed info for a single skill."""
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {name}")
    skill_dir = _get_skill_dir(name)
    files = []
    if skill_dir.exists():
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file():
                files.append(str(f.relative_to(skill_dir)))
    return {
        "name": skill.name,
        "version": skill.version or "0.0.0",
        "category": skill.category,
        "description": skill.description,
        "downloads": skill.installs,
        "author": skill.author_name or "system",
        "pinned": skill.pinned,
        "changelog": skill.changelog or "",
        "files": files,
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
        "updated_at": skill.updated_at.isoformat() if skill.updated_at else None,
    }


@router.get("/{name}/install", dependencies=[Depends(_verify_cli_token)])
def cli_install_skill(
    name: str,
    repo: SkillRepo = Depends(_get_repo),
):
    """Download skill as zip. Designed for: curl ... | funzip or pipe to file.

    openclaw can call this and directly extract to ~/.openclaw/skills/
    """
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {name}")

    skill_dir = _get_skill_dir(name)
    buf = io.BytesIO()
    if not skill_dir.exists() or not any(skill_dir.iterdir()):
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("SKILL.md", skill.content or "")
    else:
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(skill_dir))
    buf.seek(0)

    # Increment download count
    repo.increment_installs(name)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
    )
