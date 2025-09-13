"""
FileSystem MCP Server

这个文件是文件系统操作MCP服务器的入口点。
它导入所有的文件系统工具模块，并提供一个运行MCP服务器的入口点。
"""

import atexit
import asyncio
import sys
import os
import logging

# 尝试使用相对导入（当作为包的一部分导入时）
try:
    from .core import mcp, set_config, get_config
    from .file_operations import (
        read_file,
        write_file,
        create_file,
        delete_file,
        copy_file,
        move_file,
        get_file_stats,
    )
    from .directory_operations import (
        list_directory,
        create_directory,
        delete_directory,
        copy_directory,
        move_directory,
        get_directory_size,
        find_empty_directories,
    )
    from .advanced_operations import (
        search_files,
        create_archive,
        extract_archive,
        set_file_permissions,
        find_duplicates,
    )
except ImportError:
    # 当作为主模块运行时，使用绝对导入
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    )
    from mcp_servers.filesystem.core import mcp, set_config, get_config
    from mcp_servers.filesystem.file_operations import (
        read_file,
        write_file,
        create_file,
        delete_file,
        copy_file,
        move_file,
        get_file_stats,
    )
    from mcp_servers.filesystem.directory_operations import (
        list_directory,
        create_directory,
        delete_directory,
        copy_directory,
        move_directory,
        get_directory_size,
        find_empty_directories,
    )
    from mcp_servers.filesystem.advanced_operations import (
        search_files,
        create_archive,
        extract_archive,
        set_file_permissions,
        find_duplicates,
    )

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_security_config():
    """设置安全配置"""
    # 从环境变量读取配置
    max_file_size = os.getenv("FS_MAX_FILE_SIZE", "104857600")  # 默认100MB
    try:
        set_config("max_file_size", int(max_file_size))
    except ValueError:
        logger.warning(f"Invalid FS_MAX_FILE_SIZE: {max_file_size}, using default")

    # 允许的路径
    allowed_paths = os.getenv("FS_ALLOWED_PATHS", "")
    if allowed_paths:
        paths = [p.strip() for p in allowed_paths.split(",") if p.strip()]
        set_config("allowed_paths", paths)
        logger.info(f"Allowed paths configured: {paths}")

    # 禁止的路径
    forbidden_paths = os.getenv("FS_FORBIDDEN_PATHS", "/etc,/sys,/proc,/dev")
    if forbidden_paths:
        paths = [p.strip() for p in forbidden_paths.split(",") if p.strip()]
        set_config("forbidden_paths", paths)
        logger.info(f"Forbidden paths configured: {paths}")

    # 禁止的扩展名
    forbidden_extensions = os.getenv(
        "FS_FORBIDDEN_EXTENSIONS", ".exe,.bat,.cmd,.sh,.ps1"
    )
    if forbidden_extensions:
        exts = [e.strip() for e in forbidden_extensions.split(",") if e.strip()]
        set_config("forbidden_extensions", exts)
        logger.info(f"Forbidden extensions configured: {exts}")

    # 隐藏文件和系统文件
    enable_hidden = os.getenv("FS_ENABLE_HIDDEN_FILES", "false").lower() == "true"
    set_config("enable_hidden_files", enable_hidden)

    enable_system = os.getenv("FS_ENABLE_SYSTEM_FILES", "false").lower() == "true"
    set_config("enable_system_files", enable_system)

    logger.info("FileSystem MCP Server security configuration loaded")


@mcp.tool()
async def get_server_info() -> dict:
    """
    获取文件系统MCP服务器信息

    Returns:
        服务器信息字典
    """
    import platform

    config = {
        "max_file_size": get_config("max_file_size"),
        "allowed_paths": get_config("allowed_paths", []),
        "forbidden_paths": get_config("forbidden_paths", []),
        "forbidden_extensions": get_config("forbidden_extensions", []),
        "enable_hidden_files": get_config("enable_hidden_files", False),
        "enable_system_files": get_config("enable_system_files", False),
    }

    return {
        "server_name": "FileSystem MCP Server",
        "version": "1.0.0",
        "description": "提供文件系统操作的MCP服务器",
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "available_tools": [
            # 文件操作
            "read_file",
            "write_file",
            "create_file",
            "delete_file",
            "copy_file",
            "move_file",
            "get_file_stats",
            # 目录操作
            "list_directory",
            "create_directory",
            "delete_directory",
            "copy_directory",
            "move_directory",
            "get_directory_size",
            "find_empty_directories",
            # 高级操作
            "search_files",
            "create_archive",
            "extract_archive",
            "set_file_permissions",
            "find_duplicates",
            # 服务器信息
            "get_server_info",
        ],
        "security_config": config,
    }


@mcp.tool()
async def health_check() -> dict:
    """
    健康检查

    Returns:
        健康状态字典
    """
    import psutil
    import tempfile
    from pathlib import Path

    try:
        # 检查临时目录写入权限
        temp_dir = Path(tempfile.gettempdir())
        test_file = temp_dir / "mcp_fs_health_check.txt"

        try:
            test_file.write_text("health check")
            test_file.unlink()
            write_permission = True
        except Exception:
            write_permission = False

        # 系统资源信息
        disk_usage = psutil.disk_usage("/")
        memory = psutil.virtual_memory()

        return {
            "status": "healthy",
            "timestamp": str(asyncio.get_event_loop().time()),
            "write_permission": write_permission,
            "system_resources": {
                "disk_total": disk_usage.total,
                "disk_used": disk_usage.used,
                "disk_free": disk_usage.free,
                "disk_percent": disk_usage.percent,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
            },
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": str(asyncio.get_event_loop().time()),
        }


def cleanup():
    """清理资源"""
    logger.info("FileSystem MCP Server shutting down...")


def main():
    """运行MCP服务器的主函数"""
    # 设置清理函数
    atexit.register(cleanup)

    # 设置安全配置
    setup_security_config()

    logger.info("Starting FileSystem MCP Server...")
    logger.info("Available tools:")
    logger.info(
        "  File Operations: read_file, write_file, create_file, delete_file, copy_file, move_file, get_file_stats"
    )
    logger.info(
        "  Directory Operations: list_directory, create_directory, delete_directory, copy_directory, move_directory, get_directory_size, find_empty_directories"
    )
    logger.info(
        "  Advanced Operations: search_files, create_archive, extract_archive, set_file_permissions, find_duplicates"
    )
    logger.info("  Server Tools: get_server_info, health_check")

    try:
        # 运行MCP服务器
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        cleanup()


if __name__ == "__main__":
    main()
