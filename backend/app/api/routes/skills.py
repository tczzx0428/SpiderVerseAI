from __future__ import annotations
import io
import json
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user, require_admin
from app.core.entities.skill import SkillEntity
from app.infra.db.models.user import User
from app.infra.db.models.config import SystemConfig
from app.infra.db.repos.skill_repo import SkillRepo
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/skills", tags=["skills"])

VALID_CATEGORIES = ["dev-tools", "text", "data", "automation", "other"]
SKILLS_STORAGE_DIR = Path("/tmp/sv_skills")


def _get_skill_dir(name: str) -> Path:
    return SKILLS_STORAGE_DIR / name


def _get_repo(db: Session = Depends(get_db)) -> SkillRepo:
    return SkillRepo(db)


def _skill_to_dict(s: SkillEntity) -> dict:
    # List files on disk
    skill_dir = _get_skill_dir(s.name)
    files: list[dict] = []
    if skill_dir.exists():
        for f in sorted(skill_dir.rglob("*")):
            if f.is_file():
                rel = str(f.relative_to(skill_dir))
                files.append({"name": rel, "size": f.stat().st_size})
    return {
        "name": s.name,
        "content": s.content,
        "description": s.description,
        "category": s.category,
        "author_id": s.author_id,
        "author_name": s.author_name,
        "downloads": s.installs,
        "pinned": s.pinned,
        "version": s.version,
        "changelog": s.changelog,
        "source": s.source,
        "files": files,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _extract_zip_to_skill_dir(name: str, zip_bytes: bytes) -> str:
    """Extract zip to skill dir. Returns SKILL.md content if present."""
    skill_dir = _get_skill_dir(name)
    if skill_dir.exists():
        shutil.rmtree(skill_dir)
    skill_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        # Check for nested single directory (common zip pattern)
        top_items = set()
        for info in zf.infolist():
            parts = info.filename.split("/")
            top_items.add(parts[0])

        # If all files are under one directory, strip that prefix
        strip_prefix = ""
        if len(top_items) == 1:
            single_dir = top_items.pop()
            # Check if it's really a directory prefix
            all_under = all(
                info.filename.startswith(single_dir + "/") or info.filename == single_dir + "/"
                for info in zf.infolist()
            )
            if all_under:
                strip_prefix = single_dir + "/"

        for info in zf.infolist():
            if info.is_dir():
                continue
            target_name = info.filename
            if strip_prefix and target_name.startswith(strip_prefix):
                target_name = target_name[len(strip_prefix):]
            if not target_name:
                continue
            # Security: prevent path traversal
            if ".." in target_name:
                continue
            target_path = skill_dir / target_name
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(target_path, "wb") as dst:
                dst.write(src.read())

    # Read SKILL.md content for preview
    skill_md = skill_dir / "SKILL.md"
    if skill_md.exists():
        return skill_md.read_text(encoding="utf-8", errors="replace")
    # Fallback: try any .md file
    md_files = list(skill_dir.glob("*.md"))
    if md_files:
        return md_files[0].read_text(encoding="utf-8", errors="replace")
    return ""


@router.get("")
def list_skills(
    q: str = Query("", description="Search keyword"),
    category: str = Query("", description="Filter by category"),
    sort: str = Query("default", description="Sort: default, newest, most_downloads, recently_updated"),
    favorites_only: bool = Query(False, description="Only show favorites"),
    db: Session = Depends(get_db),
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    skills = repo.list_all()
    user_favs = set(_get_user_favorites(db, current_user.id))
    if q:
        q_lower = q.lower()
        def _matches(s: SkillEntity) -> bool:
            if q_lower in s.name.lower() or q_lower in s.description.lower() or q_lower in s.content.lower():
                return True
            # Search inside SKILL.md on disk
            skill_md = _get_skill_dir(s.name) / "SKILL.md"
            if skill_md.exists():
                try:
                    if q_lower in skill_md.read_text(encoding="utf-8", errors="replace").lower():
                        return True
                except Exception:
                    pass
            return False
        skills = [s for s in skills if _matches(s)]
    if category:
        skills = [s for s in skills if s.category == category]
    if favorites_only:
        skills = [s for s in skills if s.name in user_favs]
    if sort == "newest":
        skills.sort(key=lambda s: (s.created_at or datetime.min), reverse=True)
    elif sort == "most_downloads":
        skills.sort(key=lambda s: s.installs, reverse=True)
    elif sort == "recently_updated":
        skills.sort(key=lambda s: (s.updated_at or datetime.min), reverse=True)
    else:
        skills.sort(key=lambda s: (-int(s.pinned), -s.installs, s.name))
    result = []
    user_dl_times = _get_user_download_times(db, current_user.id)
    for s in skills:
        d = _skill_to_dict(s)
        d["favorited"] = s.name in user_favs
        votes = _get_skill_votes(db, s.name)
        d["ups"] = len(votes["up"])
        d["downs"] = len(votes["down"])
        d["my_vote"] = "up" if current_user.id in votes["up"] else "down" if current_user.id in votes["down"] else "none"
        # has_update: favorited skill updated after user's last download
        d["has_update"] = False
        if s.name in user_favs and s.updated_at and s.name in user_dl_times:
            try:
                last_dl = datetime.fromisoformat(user_dl_times[s.name])
                if s.updated_at > last_dl:
                    d["has_update"] = True
            except (ValueError, TypeError):
                pass
        result.append(d)
    return result


# ── Specification (admin-editable, stored in SystemConfig) ──

SPEC_KEY = "skills_specification"


@router.get("/specification")
def get_specification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    m = db.query(SystemConfig).filter(SystemConfig.key == SPEC_KEY).first()
    return {"content": m.value if m else ""}


class SpecBody(BaseModel):
    content: str


@router.put("/specification")
def update_specification(
    body: SpecBody,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    now = datetime.utcnow()
    m = db.query(SystemConfig).filter(SystemConfig.key == SPEC_KEY).first()
    if m:
        m.value = body.content
        m.updated_at = now
    else:
        m = SystemConfig(key=SPEC_KEY, value=body.content, updated_by=admin.id, updated_at=now)
        db.add(m)
    db.commit()
    return {"content": m.value}


@router.get("/categories")
def list_categories(current_user: User = Depends(get_current_user)):
    return [
        {"value": "dev-tools", "label": "开发工具"},
        {"value": "text", "label": "文本处理"},
        {"value": "data", "label": "数据分析"},
        {"value": "automation", "label": "自动化"},
        {"value": "other", "label": "其他"},
    ]


@router.get("/stats/overview")
def skill_stats(
    repo: SkillRepo = Depends(_get_repo),
    admin: User = Depends(require_admin),
):
    skills = repo.list_all()
    total = len(skills)
    total_downloads = sum(s.installs for s in skills)
    # Category breakdown
    cat_counts: dict[str, int] = {}
    for s in skills:
        cat_counts[s.category] = cat_counts.get(s.category, 0) + 1
    # Top downloaded
    top = sorted(skills, key=lambda s: s.installs, reverse=True)[:5]
    # Most active authors
    author_counts: dict[str, int] = {}
    for s in skills:
        a = s.author_name or "system"
        author_counts[a] = author_counts.get(a, 0) + 1
    top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "total_skills": total,
        "total_downloads": total_downloads,
        "category_breakdown": cat_counts,
        "top_downloaded": [{"name": s.name, "downloads": s.installs} for s in top],
        "top_authors": [{"name": a, "count": c} for a, c in top_authors],
    }


@router.get("/{name}")
def get_skill(
    name: str,
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    return _skill_to_dict(skill)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_skill(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("other"),
    source: str = Form("internal"),
    version: str = Form("1.0.0"),
    changelog: str = Form(""),
    file: UploadFile = File(...),
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    name = name.strip().lower().replace(" ", "-")
    if not name:
        raise HTTPException(status_code=400, detail="Skill 名称不能为空")
    existing = repo.get(name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Skill '{name}' 已存在")

    # Read uploaded file
    file_bytes = file.file.read()
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="请上传 .zip 文件")
    try:
        content = _extract_zip_to_skill_dir(name, file_bytes)
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="无效的 zip 文件")

    entity = SkillEntity(
        name=name,
        content=content,
        description=description,
        category=category if category in VALID_CATEGORIES else "other",
        author_id=current_user.id,
        author_name=current_user.username,
        version=version,
        changelog=changelog,
        source=source if source in ("internal", "external") else "internal",
    )
    saved = repo.upsert(entity)
    return _skill_to_dict(saved)


@router.put("/{name}")
def update_skill(
    name: str,
    description: str = Form(None),
    category: str = Form(None),
    source: str = Form(None),
    version: str = Form(None),
    changelog: str = Form(None),
    file: Optional[UploadFile] = File(None),
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    existing = repo.get(name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    if existing.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有作者或管理员可以编辑")

    # Update files if new zip provided
    if file and file.filename:
        file_bytes = file.file.read()
        if not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="请上传 .zip 文件")
        try:
            content = _extract_zip_to_skill_dir(name, file_bytes)
            existing.content = content
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="无效的 zip 文件")

    if description is not None:
        existing.description = description
    if category is not None and category in VALID_CATEGORIES:
        existing.category = category
    if source is not None and source in ("internal", "external"):
        existing.source = source
    if version is not None:
        existing.version = version
    if changelog is not None:
        existing.changelog = changelog
    saved = repo.upsert(existing)
    return _skill_to_dict(saved)


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(
    name: str,
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    existing = repo.get(name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    if existing.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只有作者或管理员可以删除")
    repo.delete(name)
    # Clean up files
    skill_dir = _get_skill_dir(name)
    if skill_dir.exists():
        shutil.rmtree(skill_dir)


@router.get("/{name}/download")
def download_skill(
    name: str,
    db: Session = Depends(get_db),
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")

    skill_dir = _get_skill_dir(name)
    if not skill_dir.exists() or not any(skill_dir.iterdir()):
        # No files on disk — generate a zip with just the content as SKILL.md
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("SKILL.md", skill.content or "")
        buf.seek(0)
    else:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in skill_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(skill_dir))
        buf.seek(0)

    # Increment download count & record user download time
    repo.increment_installs(name)
    _record_user_download(db, current_user.id, name)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}.zip"'},
    )


@router.get("/{name}/files/{file_path:path}")
def preview_file(
    name: str,
    file_path: str,
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    if ".." in file_path:
        raise HTTPException(status_code=400, detail="非法路径")
    target = _get_skill_dir(name) / file_path
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="二进制文件，无法预览")
    return {"name": file_path, "content": content}


class SkillPinBody(BaseModel):
    pinned: bool


class SkillFavBody(BaseModel):
    favorite: bool


def _get_user_favorites(db: Session, user_id: int) -> list[str]:
    """Get a user's favorite skill names."""
    key = f"skill_favorites:{user_id}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not m:
        return []
    try:
        return json.loads(m.value)
    except (json.JSONDecodeError, TypeError):
        return []


def _get_user_download_times(db: Session, user_id: int) -> dict[str, str]:
    """Get user's last download time per skill: {skill_name: iso_timestamp}"""
    key = f"skill_downloads:{user_id}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not m:
        return {}
    try:
        return json.loads(m.value)
    except (json.JSONDecodeError, TypeError):
        return {}


def _record_user_download(db: Session, user_id: int, skill_name: str):
    key = f"skill_downloads:{user_id}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    now = datetime.utcnow()
    downloads: dict[str, str] = {}
    if m:
        try:
            downloads = json.loads(m.value)
        except (json.JSONDecodeError, TypeError):
            downloads = {}
        downloads[skill_name] = now.isoformat()
        m.value = json.dumps(downloads, ensure_ascii=False)
        m.updated_at = now
    else:
        downloads[skill_name] = now.isoformat()
        m = SystemConfig(key=key, value=json.dumps(downloads, ensure_ascii=False), updated_by=user_id, updated_at=now)
        db.add(m)
    db.commit()


def _set_user_favorites(db: Session, user_id: int, favorites: list[str]):
    key = f"skill_favorites:{user_id}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    now = datetime.utcnow()
    if m:
        m.value = json.dumps(favorites, ensure_ascii=False)
        m.updated_at = now
    else:
        m = SystemConfig(key=key, value=json.dumps(favorites, ensure_ascii=False), updated_by=user_id, updated_at=now)
        db.add(m)
    db.commit()


@router.put("/{name}/pin")
def pin_skill(
    name: str,
    body: SkillPinBody,
    repo: SkillRepo = Depends(_get_repo),
    admin: User = Depends(require_admin),
):
    existing = repo.get(name)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    existing.pinned = body.pinned
    saved = repo.upsert(existing)
    return _skill_to_dict(saved)


@router.put("/{name}/favorite")
def toggle_favorite(
    name: str,
    body: SkillFavBody,
    db: Session = Depends(get_db),
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    favs = _get_user_favorites(db, current_user.id)
    if body.favorite and name not in favs:
        favs.append(name)
    elif not body.favorite and name in favs:
        favs.remove(name)
    _set_user_favorites(db, current_user.id, favs)
    return {"name": name, "favorited": body.favorite}


# ── Voting ──

class SkillCommentBody(BaseModel):
    content: str


def _get_skill_comments(db: Session, skill_name: str) -> list[dict]:
    key = f"skill_comments:{skill_name}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not m:
        return []
    try:
        return json.loads(m.value)
    except (json.JSONDecodeError, TypeError):
        return []


def _set_skill_comments(db: Session, skill_name: str, comments: list[dict], user_id: int):
    key = f"skill_comments:{skill_name}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    now = datetime.utcnow()
    val = json.dumps(comments, ensure_ascii=False)
    if m:
        m.value = val
        m.updated_at = now
    else:
        m = SystemConfig(key=key, value=val, updated_by=user_id, updated_at=now)
        db.add(m)
    db.commit()


@router.get("/{name}/comments")
def list_comments(
    name: str,
    repo: SkillRepo = Depends(_get_repo),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    return _get_skill_comments(db, name)


@router.post("/{name}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(
    name: str,
    body: SkillCommentBody,
    repo: SkillRepo = Depends(_get_repo),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    text = body.content.strip()
    if not text:
        raise HTTPException(status_code=400, detail="评论内容不能为空")
    if len(text) > 200:
        raise HTTPException(status_code=400, detail="评论不能超过 200 字")
    comments = _get_skill_comments(db, name)
    comments.append({
        "user_id": current_user.id,
        "user_name": current_user.username,
        "content": text,
        "created_at": datetime.utcnow().isoformat(),
    })
    _set_skill_comments(db, name, comments, current_user.id)
    return comments


@router.delete("/{name}/comments/{index}")
def delete_comment(
    name: str,
    index: int,
    repo: SkillRepo = Depends(_get_repo),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    comments = _get_skill_comments(db, name)
    if index < 0 or index >= len(comments):
        raise HTTPException(status_code=404, detail="评论不存在")
    c = comments[index]
    if c["user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="只能删除自己的评论")
    comments.pop(index)
    _set_skill_comments(db, name, comments, current_user.id)
    return comments


# ── Voting ──

class SkillVoteBody(BaseModel):
    vote: str  # "up", "down", or "none"


def _get_skill_votes(db: Session, skill_name: str) -> dict:
    """Get votes for a skill: {up: [user_ids], down: [user_ids]}"""
    key = f"skill_votes:{skill_name}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not m:
        return {"up": [], "down": []}
    try:
        return json.loads(m.value)
    except (json.JSONDecodeError, TypeError):
        return {"up": [], "down": []}


def _set_skill_votes(db: Session, skill_name: str, votes: dict, user_id: int):
    key = f"skill_votes:{skill_name}"
    m = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    now = datetime.utcnow()
    val = json.dumps(votes, ensure_ascii=False)
    if m:
        m.value = val
        m.updated_at = now
    else:
        m = SystemConfig(key=key, value=val, updated_by=user_id, updated_at=now)
        db.add(m)
    db.commit()


@router.put("/{name}/vote")
def vote_skill(
    name: str,
    body: SkillVoteBody,
    db: Session = Depends(get_db),
    repo: SkillRepo = Depends(_get_repo),
    current_user: User = Depends(get_current_user),
):
    skill = repo.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill 不存在: {name}")
    if body.vote not in ("up", "down", "none"):
        raise HTTPException(status_code=400, detail="vote 必须为 up, down 或 none")
    votes = _get_skill_votes(db, name)
    uid = current_user.id
    # Remove existing vote
    votes["up"] = [u for u in votes["up"] if u != uid]
    votes["down"] = [u for u in votes["down"] if u != uid]
    # Add new vote
    if body.vote == "up":
        votes["up"].append(uid)
    elif body.vote == "down":
        votes["down"].append(uid)
    _set_skill_votes(db, name, votes, uid)
    return {"name": name, "ups": len(votes["up"]), "downs": len(votes["down"]), "my_vote": body.vote}
