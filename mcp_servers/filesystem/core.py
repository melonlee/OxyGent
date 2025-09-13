"""
文件系统核心功能

提供文件系统操作的核心功能，包括安全控制、路径验证等基础设施
"""

import os
import stat
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# 加载.env文件中的环境变量
load_dotenv()

# Initialize FastMCP server instance
mcp = FastMCP()

# 全局配置
_config = {
    "max_file_size": 100 * 1024 * 1024,  # 100MB 最大文件大小
    "allowed_extensions": None,  # None 表示允许所有扩展名
    "forbidden_extensions": [".exe", ".bat", ".cmd", ".sh", ".ps1"],  # 禁止的扩展名
    "allowed_paths": [],  # 允许的路径列表，空表示允许所有路径
    "forbidden_paths": ["/etc", "/sys", "/proc", "/dev"],  # 禁止的路径列表
    "enable_hidden_files": False,  # 是否允许操作隐藏文件
    "enable_system_files": False,  # 是否允许操作系统文件
}


def set_config(key: str, value) -> None:
    """设置配置项"""
    global _config
    _config[key] = value


def get_config(key: str, default=None):
    """获取配置项"""
    return _config.get(key, default)


def is_safe_path(file_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    检查路径是否安全

    Args:
        file_path: 要检查的路径

    Returns:
        (is_safe, reason): 是否安全和原因
    """
    try:
        path = Path(file_path).resolve()
        path_str = str(path)

        # 检查是否是绝对路径
        if not path.is_absolute():
            return False, "路径必须是绝对路径"

        # 检查禁止的路径
        forbidden_paths = get_config("forbidden_paths", [])
        for forbidden in forbidden_paths:
            if path_str.startswith(forbidden):
                return False, f"禁止访问路径: {forbidden}"

        # 检查允许的路径（如果配置了）
        allowed_paths = get_config("allowed_paths", [])
        if allowed_paths:
            allowed = False
            for allowed_path in allowed_paths:
                if path_str.startswith(allowed_path):
                    allowed = True
                    break
            if not allowed:
                return False, "路径不在允许的范围内"

        # 检查隐藏文件
        if not get_config("enable_hidden_files", False):
            if any(part.startswith(".") for part in path.parts):
                return False, "不允许操作隐藏文件"

        return True, "路径安全"

    except Exception as e:
        return False, f"路径验证失败: {str(e)}"


def is_allowed_extension(file_path: Union[str, Path]) -> Tuple[bool, str]:
    """
    检查文件扩展名是否被允许

    Args:
        file_path: 文件路径

    Returns:
        (is_allowed, reason): 是否允许和原因
    """
    try:
        path = Path(file_path)
        extension = path.suffix.lower()

        # 检查禁止的扩展名
        forbidden_extensions = get_config("forbidden_extensions", [])
        if extension in forbidden_extensions:
            return False, f"禁止的文件扩展名: {extension}"

        # 检查允许的扩展名（如果配置了）
        allowed_extensions = get_config("allowed_extensions")
        if allowed_extensions is not None:
            if extension not in allowed_extensions:
                return False, f"不允许的文件扩展名: {extension}"

        return True, "扩展名允许"

    except Exception as e:
        return False, f"扩展名检查失败: {str(e)}"


def get_file_info(file_path: Union[str, Path]) -> Dict:
    """
    获取文件信息

    Args:
        file_path: 文件路径

    Returns:
        文件信息字典
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return {"error": "文件不存在"}

        stat_info = path.stat()

        info = {
            "path": str(path.absolute()),
            "name": path.name,
            "size": stat_info.st_size,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "is_symlink": path.is_symlink(),
            "created_time": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
            "modified_time": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
            "accessed_time": datetime.fromtimestamp(stat_info.st_atime).isoformat(),
        }

        # 添加权限信息
        if platform.system() != "Windows":
            info["permissions"] = oct(stat_info.st_mode)[-3:]
            info["owner_uid"] = stat_info.st_uid
            info["group_gid"] = stat_info.st_gid

        # 添加文件类型信息
        if path.is_file():
            info["extension"] = path.suffix
            info["stem"] = path.stem

        return info

    except Exception as e:
        return {"error": f"获取文件信息失败: {str(e)}"}


def format_size(size_bytes: int) -> str:
    """
    格式化文件大小

    Args:
        size_bytes: 字节数

    Returns:
        格式化的大小字符串
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1

    return f"{size_bytes:.2f} {size_names[i]}"


def validate_operation(
    operation: str, file_path: Union[str, Path], check_exists: bool = True
) -> Tuple[bool, str]:
    """
    验证文件操作是否可以执行

    Args:
        operation: 操作类型
        file_path: 文件路径
        check_exists: 是否检查文件存在性

    Returns:
        (is_valid, reason): 是否有效和原因
    """
    # 检查路径安全性
    is_safe, reason = is_safe_path(file_path)
    if not is_safe:
        return False, reason

    # 检查扩展名
    is_allowed, reason = is_allowed_extension(file_path)
    if not is_allowed:
        return False, reason

    path = Path(file_path)

    # 检查文件是否存在（如果需要）
    if check_exists and operation in ["read", "delete", "move", "copy"]:
        if not path.exists():
            return False, "文件或目录不存在"

    # 检查文件大小限制（对于写操作）
    if operation in ["write", "create"] and path.exists():
        max_size = get_config("max_file_size", 100 * 1024 * 1024)
        if path.stat().st_size > max_size:
            return False, f"文件大小超过限制: {format_size(max_size)}"

    return True, "操作有效"
