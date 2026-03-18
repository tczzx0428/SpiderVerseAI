"""批次时间戳分组逻辑 — 从 apps.py + stats.py 提取的单一来源。

核心逻辑：
1. 识别主批次时间戳（batch_result_* 或 batch_*_all/_part 或 outputs/子目录）
2. 将非主批次时间戳归并到 60 分钟内最近的主批次
3. 最终分组数 = 运行次数
"""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_TS_RE = re.compile(r"(\d{8}_\d{6})")
_BATCH_PREFIX_RE = re.compile(r"^batch_(?:result_)?(\d{8}_\d{6})")


def extract_timestamp(text: str) -> str | None:
    """从文件名或字符串中提取 YYYYMMDD_HHMMSS 格式的时间戳。"""
    m = _TS_RE.search(text)
    return m.group(1) if m else None


def is_batch_marker(filename: str) -> bool:
    """判断文件名是否为主批次标记文件。"""
    return bool(filename.startswith("batch_result_") or _BATCH_PREFIX_RE.match(filename))


def find_parent_batch(ts_key: str, batch_ts_list: list[str]) -> str | None:
    """将非主批次时间戳归属到最近的前序主批次（60 分钟内）。"""
    if not batch_ts_list:
        return None
    try:
        t = datetime.strptime(ts_key, "%Y%m%d_%H%M%S")
    except ValueError:
        return None
    best = None
    best_delta = None
    for bts in batch_ts_list:
        try:
            bt = datetime.strptime(bts, "%Y%m%d_%H%M%S")
        except ValueError:
            continue
        delta = (t - bt).total_seconds()
        if 0 <= delta <= 3600:
            if best_delta is None or delta < best_delta:
                best = bts
                best_delta = delta
    return best


def scan_data_dir(data_dir: Path) -> tuple[list[tuple[str, dict]], set[str]]:
    """扫描 data_dir 下的 results/, history/batch/, outputs/ 目录。

    Returns:
        raw_files: [(ts_key, file_info_dict), ...]
        batch_ts_set: 主批次时间戳集合
    """
    raw_files: list[tuple[str, dict]] = []
    batch_ts_set: set[str] = set()

    results_dir = data_dir / "results"
    if results_dir.exists():
        for f in results_dir.iterdir():
            if not f.is_file() or f.name.startswith("."):
                continue
            ts = extract_timestamp(f.name)
            if not ts:
                continue
            stat = f.stat()
            raw_files.append((ts, {
                "name": f.name,
                "path": str(f.relative_to(data_dir)),
                "size": stat.st_size,
                "category": "result",
            }))
            if f.name.startswith("batch_result_"):
                batch_ts_set.add(ts)

    batch_dir = data_dir / "history" / "batch"
    if batch_dir.exists():
        for f in batch_dir.iterdir():
            if not f.is_file() or f.name.startswith("."):
                continue
            ts = extract_timestamp(f.name)
            if not ts:
                continue
            stat = f.stat()
            raw_files.append((ts, {
                "name": f.name,
                "path": str(f.relative_to(data_dir)),
                "size": stat.st_size,
                "category": "detail",
            }))
            if _BATCH_PREFIX_RE.match(f.name):
                batch_ts_set.add(ts)

    outputs_dir = data_dir / "outputs"
    if outputs_dir.exists():
        for entry in outputs_dir.iterdir():
            if entry.is_dir():
                ts = extract_timestamp(entry.name)
                if not ts:
                    continue
                for f in entry.iterdir():
                    if not f.is_file() or f.name.startswith("."):
                        continue
                    stat = f.stat()
                    raw_files.append((ts, {
                        "name": f.name,
                        "path": str(f.relative_to(data_dir)),
                        "size": stat.st_size,
                        "category": "output",
                    }))
                batch_ts_set.add(ts)
            elif entry.is_file() and not entry.name.startswith("."):
                ts = extract_timestamp(entry.name)
                if not ts:
                    continue
                stat = entry.stat()
                raw_files.append((ts, {
                    "name": entry.name,
                    "path": str(entry.relative_to(data_dir)),
                    "size": stat.st_size,
                    "category": "output",
                }))
                batch_ts_set.add(ts)

    return raw_files, batch_ts_set


def group_by_batch(raw_files: list[tuple[str, dict]], batch_ts_set: set[str]) -> dict[str, list[dict]]:
    """将文件按批次时间戳分组，非主批次文件归并到最近的主批次。"""
    batch_ts_list = sorted(batch_ts_set)
    ts_files: dict[str, list[dict]] = defaultdict(list)

    for ts_key, info in raw_files:
        if ts_key in batch_ts_set:
            ts_files[ts_key].append(info)
        else:
            parent = find_parent_batch(ts_key, batch_ts_list)
            if parent:
                ts_files[parent].append(info)
            else:
                ts_files[ts_key].append(info)

    return dict(ts_files)


def count_run_groups(data_dir: Path) -> tuple[int, set[str]]:
    """统计 data_dir 下的运行分组数，返回 (分组数, 时间戳集合)。

    用于 stats 统计，不需要完整的文件信息。
    """
    all_ts: set[str] = set()
    batch_ts_set: set[str] = set()

    results_dir = data_dir / "results"
    if results_dir.exists():
        for f in results_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                ts = extract_timestamp(f.name)
                if ts:
                    all_ts.add(ts)
                    if f.name.startswith("batch_result_"):
                        batch_ts_set.add(ts)

    batch_dir = data_dir / "history" / "batch"
    if batch_dir.exists():
        for f in batch_dir.iterdir():
            if f.is_file() and not f.name.startswith("."):
                ts = extract_timestamp(f.name)
                if ts:
                    all_ts.add(ts)
                    if _BATCH_PREFIX_RE.match(f.name):
                        batch_ts_set.add(ts)

    outputs_dir = data_dir / "outputs"
    if outputs_dir.exists():
        for entry in outputs_dir.iterdir():
            if entry.is_dir():
                ts = extract_timestamp(entry.name)
                if ts:
                    all_ts.add(ts)
                    batch_ts_set.add(ts)
            elif entry.is_file() and not entry.name.startswith("."):
                ts = extract_timestamp(entry.name)
                if ts:
                    all_ts.add(ts)
                    batch_ts_set.add(ts)

    batch_ts_list = sorted(batch_ts_set)
    final_groups: set[str] = set()

    for ts_key in all_ts:
        if ts_key in batch_ts_set:
            final_groups.add(ts_key)
        else:
            parent = find_parent_batch(ts_key, batch_ts_list)
            if parent:
                final_groups.add(parent)
            else:
                final_groups.add(ts_key)

    return len(final_groups), final_groups
