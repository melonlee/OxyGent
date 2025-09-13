"""
高级文件系统操作

提供搜索、压缩、权限管理等高级功能
"""

import os
import re
import zipfile
import tarfile
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Union, Pattern
from datetime import datetime, timedelta

from .core import mcp, validate_operation, get_file_info, format_size


@mcp.tool()
async def search_files(
    search_path: str,
    pattern: str = "*",
    search_type: str = "glob",
    recursive: bool = True,
    max_results: int = 1000,
    include_content: bool = False,
    file_types: Optional[List[str]] = None,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
) -> Dict:
    """
    搜索文件

    Args:
        search_path: 搜索目录路径
        pattern: 搜索模式
        search_type: 搜索类型 ('glob', 'regex', 'content')
        recursive: 是否递归搜索
        max_results: 最大结果数量
        include_content: 是否包含文件内容匹配
        file_types: 文件类型过滤 (如 ['.txt', '.py'])
        min_size: 最小文件大小（字节）
        max_size: 最大文件大小（字节）
        modified_after: 修改时间晚于（ISO格式）
        modified_before: 修改时间早于（ISO格式）

    Returns:
        搜索结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", search_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(search_path)

        if not path.is_dir():
            return {"success": False, "error": "搜索路径不是目录"}

        results = []

        # 编译正则表达式（如果需要）
        regex_pattern = None
        if search_type == "regex":
            try:
                regex_pattern = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                return {"success": False, "error": f"正则表达式错误: {str(e)}"}

        # 解析时间过滤器
        after_time = None
        before_time = None
        if modified_after:
            try:
                after_time = datetime.fromisoformat(
                    modified_after.replace("Z", "+00:00")
                )
            except ValueError:
                return {
                    "success": False,
                    "error": "modified_after 时间格式错误，请使用ISO格式",
                }

        if modified_before:
            try:
                before_time = datetime.fromisoformat(
                    modified_before.replace("Z", "+00:00")
                )
            except ValueError:
                return {
                    "success": False,
                    "error": "modified_before 时间格式错误，请使用ISO格式",
                }

        def matches_criteria(file_path: Path) -> bool:
            """检查文件是否匹配搜索条件"""
            try:
                # 文件类型过滤
                if file_types and file_path.suffix.lower() not in [
                    ext.lower() for ext in file_types
                ]:
                    return False

                # 大小过滤
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    if min_size is not None and file_size < min_size:
                        return False
                    if max_size is not None and file_size > max_size:
                        return False

                # 时间过滤
                if after_time or before_time:
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if after_time and mod_time < after_time:
                        return False
                    if before_time and mod_time > before_time:
                        return False

                return True
            except (OSError, PermissionError):
                return False

        def search_content(file_path: Path, pattern: str) -> List[Dict]:
            """在文件内容中搜索"""
            matches = []
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for line_num, line in enumerate(f, 1):
                        if search_type == "regex":
                            if regex_pattern and regex_pattern.search(line):
                                matches.append(
                                    {
                                        "line_number": line_num,
                                        "line_content": line.strip(),
                                        "match": regex_pattern.search(line).group(),
                                    }
                                )
                        else:
                            if pattern.lower() in line.lower():
                                matches.append(
                                    {
                                        "line_number": line_num,
                                        "line_content": line.strip(),
                                        "match": pattern,
                                    }
                                )
            except (UnicodeDecodeError, PermissionError):
                pass
            return matches

        # 执行搜索
        search_iterator = path.rglob("*") if recursive else path.iterdir()

        for item in search_iterator:
            if len(results) >= max_results:
                break

            try:
                # 基本条件检查
                if not matches_criteria(item):
                    continue

                # 名称模式匹配
                name_matches = False
                if search_type == "glob":
                    name_matches = fnmatch.fnmatch(item.name.lower(), pattern.lower())
                elif search_type == "regex":
                    name_matches = bool(
                        regex_pattern and regex_pattern.search(item.name)
                    )
                elif search_type == "content":
                    name_matches = True  # 内容搜索不依赖文件名
                else:
                    name_matches = pattern.lower() in item.name.lower()

                # 内容匹配（仅对文件）
                content_matches = []
                if (
                    include_content
                    and item.is_file()
                    and (search_type == "content" or name_matches)
                ):
                    content_matches = search_content(item, pattern)
                    if search_type == "content" and not content_matches:
                        continue

                if name_matches or content_matches:
                    file_info = get_file_info(item)
                    if "error" not in file_info:
                        file_info["relative_path"] = str(item.relative_to(path))
                        if content_matches:
                            file_info["content_matches"] = content_matches
                            file_info["match_count"] = len(content_matches)
                        results.append(file_info)

            except (OSError, PermissionError):
                # 跳过无法访问的文件
                continue

        # 统计信息
        total_files = sum(1 for r in results if r["is_file"])
        total_dirs = sum(1 for r in results if r["is_dir"])
        total_matches = sum(r.get("match_count", 1) for r in results)

        return {
            "success": True,
            "search_path": str(path.absolute()),
            "pattern": pattern,
            "search_type": search_type,
            "results": results,
            "statistics": {
                "total_results": len(results),
                "total_files": total_files,
                "total_directories": total_dirs,
                "total_matches": total_matches,
                "truncated": len(results) >= max_results,
            },
            "search_criteria": {
                "recursive": recursive,
                "max_results": max_results,
                "include_content": include_content,
                "file_types": file_types,
                "min_size": min_size,
                "max_size": max_size,
                "modified_after": modified_after,
                "modified_before": modified_before,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"搜索文件失败: {str(e)}"}


@mcp.tool()
async def create_archive(
    source_path: str,
    archive_path: str,
    archive_type: str = "zip",
    compression_level: int = 6,
    include_hidden: bool = False,
    exclude_patterns: Optional[List[str]] = None,
) -> Dict:
    """
    创建压缩档案

    Args:
        source_path: 源文件或目录路径
        archive_path: 档案文件路径
        archive_type: 档案类型 ('zip', 'tar', 'tar.gz', 'tar.bz2')
        compression_level: 压缩级别 (0-9)
        include_hidden: 是否包含隐藏文件
        exclude_patterns: 排除模式列表

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", source_path)
        if not is_valid:
            return {"success": False, "error": f"源路径验证失败: {reason}"}

        is_valid, reason = validate_operation(
            "create", archive_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": f"档案路径验证失败: {reason}"}

        source = Path(source_path)
        archive = Path(archive_path)

        if not source.exists():
            return {"success": False, "error": "源路径不存在"}

        # 创建档案目录
        archive.parent.mkdir(parents=True, exist_ok=True)

        exclude_patterns = exclude_patterns or []
        files_added = 0
        total_size = 0

        def should_exclude(file_path: Path) -> bool:
            """检查文件是否应该被排除"""
            # 检查隐藏文件
            if not include_hidden and any(
                part.startswith(".") for part in file_path.parts
            ):
                return True

            # 检查排除模式
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(str(file_path), pattern):
                    return True

            return False

        if archive_type == "zip":
            with zipfile.ZipFile(
                archive, "w", zipfile.ZIP_DEFLATED, compresslevel=compression_level
            ) as zf:
                if source.is_file():
                    if not should_exclude(source):
                        zf.write(source, source.name)
                        files_added += 1
                        total_size += source.stat().st_size
                else:
                    for file_path in source.rglob("*"):
                        if file_path.is_file() and not should_exclude(file_path):
                            relative_path = file_path.relative_to(source)
                            zf.write(file_path, relative_path)
                            files_added += 1
                            total_size += file_path.stat().st_size

        elif archive_type in ["tar", "tar.gz", "tar.bz2"]:
            mode_map = {"tar": "w", "tar.gz": "w:gz", "tar.bz2": "w:bz2"}

            with tarfile.open(archive, mode_map[archive_type]) as tf:
                if source.is_file():
                    if not should_exclude(source):
                        tf.add(source, source.name)
                        files_added += 1
                        total_size += source.stat().st_size
                else:
                    for file_path in source.rglob("*"):
                        if not should_exclude(file_path):
                            relative_path = file_path.relative_to(source)
                            tf.add(file_path, relative_path)
                            if file_path.is_file():
                                files_added += 1
                                total_size += file_path.stat().st_size
        else:
            return {"success": False, "error": f"不支持的档案类型: {archive_type}"}

        # 获取档案信息
        archive_info = get_file_info(archive)
        compression_ratio = (
            (1 - archive_info["size"] / total_size) * 100 if total_size > 0 else 0
        )

        return {
            "success": True,
            "message": "档案创建成功",
            "archive_info": archive_info,
            "statistics": {
                "files_added": files_added,
                "original_size": total_size,
                "formatted_original_size": format_size(total_size),
                "compressed_size": archive_info["size"],
                "formatted_compressed_size": format_size(archive_info["size"]),
                "compression_ratio": f"{compression_ratio:.1f}%",
            },
            "settings": {
                "archive_type": archive_type,
                "compression_level": compression_level,
                "include_hidden": include_hidden,
                "exclude_patterns": exclude_patterns,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"创建档案失败: {str(e)}"}


@mcp.tool()
async def extract_archive(
    archive_path: str,
    extract_path: str,
    overwrite: bool = False,
    members: Optional[List[str]] = None,
) -> Dict:
    """
    解压档案

    Args:
        archive_path: 档案文件路径
        extract_path: 解压目标路径
        overwrite: 是否覆盖已存在的文件
        members: 要解压的文件列表（None表示全部）

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", archive_path)
        if not is_valid:
            return {"success": False, "error": f"档案路径验证失败: {reason}"}

        is_valid, reason = validate_operation(
            "create", extract_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": f"解压路径验证失败: {reason}"}

        archive = Path(archive_path)
        extract_dir = Path(extract_path)

        if not archive.is_file():
            return {"success": False, "error": "档案文件不存在"}

        # 创建解压目录
        extract_dir.mkdir(parents=True, exist_ok=True)

        files_extracted = 0
        total_size = 0

        # 检测档案类型
        if archive.suffix.lower() == ".zip":
            with zipfile.ZipFile(archive, "r") as zf:
                # 获取要解压的成员
                extract_members = members if members else zf.namelist()

                for member in extract_members:
                    if member not in zf.namelist():
                        continue

                    target_path = extract_dir / member

                    # 检查是否覆盖
                    if target_path.exists() and not overwrite:
                        continue

                    # 安全检查：防止路径遍历攻击
                    if not str(target_path.resolve()).startswith(
                        str(extract_dir.resolve())
                    ):
                        continue

                    zf.extract(member, extract_dir)
                    files_extracted += 1

                    if target_path.is_file():
                        total_size += target_path.stat().st_size

        elif (
            archive.suffix.lower() in [".tar", ".gz", ".bz2"]
            or ".tar." in archive.name.lower()
        ):
            with tarfile.open(archive, "r:*") as tf:
                # 获取要解压的成员
                extract_members = members if members else tf.getnames()

                for member in extract_members:
                    if member not in tf.getnames():
                        continue

                    target_path = extract_dir / member

                    # 检查是否覆盖
                    if target_path.exists() and not overwrite:
                        continue

                    # 安全检查：防止路径遍历攻击
                    if not str(target_path.resolve()).startswith(
                        str(extract_dir.resolve())
                    ):
                        continue

                    tf.extract(member, extract_dir)
                    files_extracted += 1

                    if target_path.is_file():
                        total_size += target_path.stat().st_size
        else:
            return {"success": False, "error": "不支持的档案格式"}

        return {
            "success": True,
            "message": "档案解压成功",
            "extract_path": str(extract_dir.absolute()),
            "statistics": {
                "files_extracted": files_extracted,
                "total_size": total_size,
                "formatted_total_size": format_size(total_size),
            },
            "settings": {"overwrite": overwrite, "members": members},
        }

    except Exception as e:
        return {"success": False, "error": f"解压档案失败: {str(e)}"}


@mcp.tool()
async def set_file_permissions(
    file_path: str, permissions: str, recursive: bool = False
) -> Dict:
    """
    设置文件权限（Unix/Linux系统）

    Args:
        file_path: 文件或目录路径
        permissions: 权限（八进制字符串，如 '755' 或 '644'）
        recursive: 是否递归设置（仅对目录有效）

    Returns:
        操作结果字典
    """
    try:
        import platform

        if platform.system() == "Windows":
            return {"success": False, "error": "Windows系统不支持Unix风格的文件权限"}

        # 验证操作
        is_valid, reason = validate_operation("write", file_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(file_path)

        if not path.exists():
            return {"success": False, "error": "文件或目录不存在"}

        # 验证权限格式
        try:
            perm_int = int(permissions, 8)
            if not (0 <= perm_int <= 0o777):
                return {"success": False, "error": "权限值必须在000-777之间"}
        except ValueError:
            return {
                "success": False,
                "error": "权限格式错误，请使用八进制字符串（如'755'）",
            }

        changed_items = []

        def change_permissions(item_path: Path):
            """更改单个项目的权限"""
            try:
                old_stat = item_path.stat()
                old_perms = oct(old_stat.st_mode)[-3:]

                item_path.chmod(perm_int)

                changed_items.append(
                    {
                        "path": str(item_path.absolute()),
                        "old_permissions": old_perms,
                        "new_permissions": permissions,
                        "is_file": item_path.is_file(),
                        "is_dir": item_path.is_dir(),
                    }
                )
            except PermissionError:
                changed_items.append(
                    {"path": str(item_path.absolute()), "error": "权限被拒绝"}
                )

        # 更改权限
        if path.is_file() or not recursive:
            change_permissions(path)
        else:
            # 递归更改目录权限
            for item in path.rglob("*"):
                change_permissions(item)
            change_permissions(path)  # 最后更改根目录权限

        success_count = sum(1 for item in changed_items if "error" not in item)
        error_count = len(changed_items) - success_count

        return {
            "success": True,
            "message": f"权限设置完成，成功{success_count}个，失败{error_count}个",
            "changed_items": changed_items,
            "statistics": {
                "total_items": len(changed_items),
                "success_count": success_count,
                "error_count": error_count,
            },
            "settings": {"permissions": permissions, "recursive": recursive},
        }

    except Exception as e:
        return {"success": False, "error": f"设置权限失败: {str(e)}"}


@mcp.tool()
async def find_duplicates(
    search_path: str, method: str = "size", recursive: bool = True, min_size: int = 1024
) -> Dict:
    """
    查找重复文件

    Args:
        search_path: 搜索目录路径
        method: 检测方法 ('size', 'hash', 'name')
        recursive: 是否递归搜索
        min_size: 最小文件大小（字节）

    Returns:
        重复文件字典
    """
    try:
        import hashlib
        from collections import defaultdict

        # 验证操作
        is_valid, reason = validate_operation("read", search_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(search_path)

        if not path.is_dir():
            return {"success": False, "error": "搜索路径不是目录"}

        # 收集文件信息
        file_groups = defaultdict(list)
        total_files = 0
        total_size = 0

        search_iterator = path.rglob("*") if recursive else path.iterdir()

        for item in search_iterator:
            if not item.is_file():
                continue

            try:
                file_size = item.stat().st_size
                if file_size < min_size:
                    continue

                total_files += 1
                total_size += file_size

                if method == "size":
                    key = file_size
                elif method == "name":
                    key = item.name.lower()
                elif method == "hash":
                    # 计算文件哈希值
                    hasher = hashlib.md5()
                    with open(item, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            hasher.update(chunk)
                    key = hasher.hexdigest()
                else:
                    return {"success": False, "error": f"不支持的检测方法: {method}"}

                file_info = get_file_info(item)
                if "error" not in file_info:
                    file_info["relative_path"] = str(item.relative_to(path))
                    if method == "hash":
                        file_info["hash"] = key
                    file_groups[key].append(file_info)

            except (OSError, PermissionError):
                continue

        # 筛选出重复文件组
        duplicates = {}
        duplicate_count = 0
        duplicate_size = 0

        for key, files in file_groups.items():
            if len(files) > 1:
                duplicates[str(key)] = {
                    "files": files,
                    "count": len(files),
                    "total_size": sum(f["size"] for f in files),
                    "wasted_space": sum(
                        f["size"] for f in files[1:]
                    ),  # 除第一个外的重复空间
                }
                duplicate_count += len(files)
                duplicate_size += duplicates[str(key)]["wasted_space"]

        return {
            "success": True,
            "search_path": str(path.absolute()),
            "method": method,
            "duplicates": duplicates,
            "statistics": {
                "total_files_scanned": total_files,
                "total_size_scanned": total_size,
                "formatted_total_size": format_size(total_size),
                "duplicate_groups": len(duplicates),
                "duplicate_files": duplicate_count,
                "wasted_space": duplicate_size,
                "formatted_wasted_space": format_size(duplicate_size),
            },
            "settings": {
                "method": method,
                "recursive": recursive,
                "min_size": min_size,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"查找重复文件失败: {str(e)}"}
