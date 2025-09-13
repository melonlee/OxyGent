"""
目录操作功能

提供目录的列表、创建、删除、遍历等操作
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union

from .core import mcp, validate_operation, get_file_info, format_size


@mcp.tool()
async def list_directory(
    directory_path: str,
    show_hidden: bool = False,
    recursive: bool = False,
    max_depth: int = 3,
    include_files: bool = True,
    include_dirs: bool = True,
    sort_by: str = "name",
) -> Dict:
    """
    列出目录内容

    Args:
        directory_path: 目录路径
        show_hidden: 是否显示隐藏文件
        recursive: 是否递归列出子目录
        max_depth: 最大递归深度
        include_files: 是否包含文件
        include_dirs: 是否包含目录
        sort_by: 排序方式 ('name', 'size', 'modified', 'created')

    Returns:
        目录内容字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", directory_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(directory_path)

        if not path.exists():
            return {"success": False, "error": "目录不存在"}

        if not path.is_dir():
            return {"success": False, "error": "指定路径不是目录"}

        def collect_items(current_path: Path, current_depth: int = 0) -> List[Dict]:
            """递归收集目录项"""
            items = []

            if current_depth >= max_depth and recursive:
                return items

            try:
                for item in current_path.iterdir():
                    # 检查隐藏文件
                    if not show_hidden and item.name.startswith("."):
                        continue

                    # 检查类型过滤
                    if item.is_file() and not include_files:
                        continue
                    if item.is_dir() and not include_dirs:
                        continue

                    # 获取项目信息
                    item_info = get_file_info(item)
                    if "error" not in item_info:
                        item_info["relative_path"] = str(item.relative_to(path))
                        item_info["depth"] = current_depth
                        items.append(item_info)

                    # 递归处理子目录
                    if recursive and item.is_dir() and current_depth < max_depth:
                        sub_items = collect_items(item, current_depth + 1)
                        items.extend(sub_items)

            except PermissionError:
                # 跳过没有权限的目录
                pass

            return items

        # 收集所有项目
        items = collect_items(path)

        # 排序
        sort_key_map = {
            "name": lambda x: x["name"].lower(),
            "size": lambda x: x["size"],
            "modified": lambda x: x["modified_time"],
            "created": lambda x: x["created_time"],
        }

        if sort_by in sort_key_map:
            items.sort(key=sort_key_map[sort_by])

        # 统计信息
        total_files = sum(1 for item in items if item["is_file"])
        total_dirs = sum(1 for item in items if item["is_dir"])
        total_size = sum(item["size"] for item in items if item["is_file"])

        return {
            "success": True,
            "directory": str(path.absolute()),
            "items": items,
            "statistics": {
                "total_items": len(items),
                "total_files": total_files,
                "total_directories": total_dirs,
                "total_size": total_size,
                "formatted_total_size": format_size(total_size),
            },
            "settings": {
                "show_hidden": show_hidden,
                "recursive": recursive,
                "max_depth": max_depth,
                "include_files": include_files,
                "include_dirs": include_dirs,
                "sort_by": sort_by,
            },
        }

    except Exception as e:
        return {"success": False, "error": f"列出目录失败: {str(e)}"}


@mcp.tool()
async def create_directory(
    directory_path: str, parents: bool = True, exist_ok: bool = True
) -> Dict:
    """
    创建目录

    Args:
        directory_path: 目录路径
        parents: 是否创建父目录
        exist_ok: 如果目录已存在是否报错

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation(
            "create", directory_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(directory_path)

        # 检查目录是否已存在
        if path.exists():
            if path.is_dir():
                if exist_ok:
                    return {
                        "success": True,
                        "message": "目录已存在",
                        "directory_info": get_file_info(path),
                    }
                else:
                    return {"success": False, "error": "目录已存在"}
            else:
                return {"success": False, "error": "路径已存在但不是目录"}

        # 创建目录
        path.mkdir(parents=parents, exist_ok=exist_ok)

        # 获取目录信息
        dir_info = get_file_info(path)

        return {"success": True, "message": "目录创建成功", "directory_info": dir_info}

    except Exception as e:
        return {"success": False, "error": f"创建目录失败: {str(e)}"}


@mcp.tool()
async def delete_directory(
    directory_path: str, recursive: bool = False, force: bool = False
) -> Dict:
    """
    删除目录

    Args:
        directory_path: 目录路径
        recursive: 是否递归删除（删除非空目录）
        force: 是否强制删除（忽略权限问题）

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("delete", directory_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(directory_path)

        if not path.exists():
            return {"success": False, "error": "目录不存在"}

        if not path.is_dir():
            return {"success": False, "error": "指定路径不是目录"}

        # 获取删除前的目录信息
        dir_info = get_file_info(path)

        # 检查目录是否为空
        if not recursive:
            try:
                if any(path.iterdir()):
                    return {
                        "success": False,
                        "error": "目录不为空，使用 recursive=True 来删除非空目录",
                    }
            except PermissionError:
                if not force:
                    return {
                        "success": False,
                        "error": "没有权限访问目录，使用 force=True 来强制删除",
                    }

        # 删除目录
        if recursive:
            if force:
                # 强制删除：修改所有文件权限
                def force_remove_readonly(func, path, _):
                    os.chmod(path, 0o777)
                    func(path)

                shutil.rmtree(path, onerror=force_remove_readonly)
            else:
                shutil.rmtree(path)
        else:
            path.rmdir()

        return {
            "success": True,
            "message": "目录删除成功",
            "deleted_directory_info": dir_info,
        }

    except Exception as e:
        return {"success": False, "error": f"删除目录失败: {str(e)}"}


@mcp.tool()
async def copy_directory(
    source_path: str,
    destination_path: str,
    overwrite: bool = False,
    preserve_metadata: bool = True,
) -> Dict:
    """
    复制目录

    Args:
        source_path: 源目录路径
        destination_path: 目标目录路径
        overwrite: 是否覆盖已存在的目标目录
        preserve_metadata: 是否保留文件元数据

    Returns:
        操作结果字典
    """
    try:
        # 验证源目录操作
        is_valid, reason = validate_operation("copy", source_path)
        if not is_valid:
            return {"success": False, "error": f"源目录验证失败: {reason}"}

        # 验证目标目录操作
        is_valid, reason = validate_operation(
            "copy", destination_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": f"目标目录验证失败: {reason}"}

        source = Path(source_path)
        destination = Path(destination_path)

        if not source.is_dir():
            return {"success": False, "error": "源路径不是目录"}

        # 检查目标目录是否已存在
        if destination.exists():
            if not overwrite:
                return {
                    "success": False,
                    "error": "目标目录已存在，使用 overwrite=True 来覆盖",
                }
            else:
                # 删除已存在的目标目录
                shutil.rmtree(destination)

        # 获取源目录信息
        source_info = get_file_info(source)

        # 复制目录
        if preserve_metadata:
            shutil.copytree(source, destination, copy_function=shutil.copy2)
        else:
            shutil.copytree(source, destination)

        # 获取目标目录信息
        dest_info = get_file_info(destination)

        return {
            "success": True,
            "message": "目录复制成功",
            "source_info": source_info,
            "destination_info": dest_info,
        }

    except Exception as e:
        return {"success": False, "error": f"复制目录失败: {str(e)}"}


@mcp.tool()
async def move_directory(
    source_path: str, destination_path: str, overwrite: bool = False
) -> Dict:
    """
    移动/重命名目录

    Args:
        source_path: 源目录路径
        destination_path: 目标目录路径
        overwrite: 是否覆盖已存在的目标目录

    Returns:
        操作结果字典
    """
    try:
        # 验证源目录操作
        is_valid, reason = validate_operation("move", source_path)
        if not is_valid:
            return {"success": False, "error": f"源目录验证失败: {reason}"}

        # 验证目标目录操作
        is_valid, reason = validate_operation(
            "move", destination_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": f"目标目录验证失败: {reason}"}

        source = Path(source_path)
        destination = Path(destination_path)

        if not source.is_dir():
            return {"success": False, "error": "源路径不是目录"}

        # 检查目标目录是否已存在
        if destination.exists():
            if not overwrite:
                return {
                    "success": False,
                    "error": "目标目录已存在，使用 overwrite=True 来覆盖",
                }
            else:
                # 删除已存在的目标目录
                shutil.rmtree(destination)

        # 获取移动前的目录信息
        source_info = get_file_info(source)

        # 移动目录
        shutil.move(str(source), str(destination))

        # 获取移动后的目录信息
        dest_info = get_file_info(destination)

        return {
            "success": True,
            "message": "目录移动成功",
            "source_info": source_info,
            "destination_info": dest_info,
        }

    except Exception as e:
        return {"success": False, "error": f"移动目录失败: {str(e)}"}


@mcp.tool()
async def get_directory_size(directory_path: str, include_subdirs: bool = True) -> Dict:
    """
    获取目录大小统计

    Args:
        directory_path: 目录路径
        include_subdirs: 是否包含子目录

    Returns:
        目录大小统计字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", directory_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(directory_path)

        if not path.is_dir():
            return {"success": False, "error": "指定路径不是目录"}

        total_size = 0
        file_count = 0
        dir_count = 0

        if include_subdirs:
            # 递归计算所有文件大小
            for item in path.rglob("*"):
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        # 跳过无法访问的文件
                        pass
                elif item.is_dir():
                    dir_count += 1
        else:
            # 只计算直接子项
            for item in path.iterdir():
                if item.is_file():
                    try:
                        total_size += item.stat().st_size
                        file_count += 1
                    except (OSError, PermissionError):
                        pass
                elif item.is_dir():
                    dir_count += 1

        return {
            "success": True,
            "directory": str(path.absolute()),
            "total_size": total_size,
            "formatted_size": format_size(total_size),
            "file_count": file_count,
            "directory_count": dir_count,
            "include_subdirs": include_subdirs,
        }

    except Exception as e:
        return {"success": False, "error": f"获取目录大小失败: {str(e)}"}


@mcp.tool()
async def find_empty_directories(directory_path: str, recursive: bool = True) -> Dict:
    """
    查找空目录

    Args:
        directory_path: 搜索目录路径
        recursive: 是否递归搜索

    Returns:
        空目录列表字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", directory_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(directory_path)

        if not path.is_dir():
            return {"success": False, "error": "指定路径不是目录"}

        empty_dirs = []

        def is_empty_dir(dir_path: Path) -> bool:
            """检查目录是否为空"""
            try:
                return not any(dir_path.iterdir())
            except PermissionError:
                return False

        if recursive:
            # 递归查找所有空目录
            for item in path.rglob("*"):
                if item.is_dir() and is_empty_dir(item):
                    empty_dirs.append(
                        {
                            "path": str(item.absolute()),
                            "relative_path": str(item.relative_to(path)),
                            "info": get_file_info(item),
                        }
                    )
        else:
            # 只查找直接子目录
            for item in path.iterdir():
                if item.is_dir() and is_empty_dir(item):
                    empty_dirs.append(
                        {
                            "path": str(item.absolute()),
                            "relative_path": item.name,
                            "info": get_file_info(item),
                        }
                    )

        return {
            "success": True,
            "search_directory": str(path.absolute()),
            "empty_directories": empty_dirs,
            "count": len(empty_dirs),
            "recursive": recursive,
        }

    except Exception as e:
        return {"success": False, "error": f"查找空目录失败: {str(e)}"}
