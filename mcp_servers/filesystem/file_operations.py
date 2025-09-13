"""
文件操作功能

提供文件的读取、写入、创建、删除等基本操作
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union

from .core import mcp, validate_operation, get_file_info, format_size


@mcp.tool()
async def read_file(
    file_path: str,
    encoding: str = "utf-8",
    max_lines: Optional[int] = None,
    start_line: int = 1,
) -> Dict:
    """
    读取文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码，默认utf-8
        max_lines: 最大读取行数，None表示读取全部
        start_line: 起始行号（从1开始）

    Returns:
        包含文件内容和元信息的字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", file_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(file_path)
        if not path.is_file():
            return {"success": False, "error": "指定路径不是文件"}

        # 获取文件信息
        file_info = get_file_info(path)
        if "error" in file_info:
            return {"success": False, "error": file_info["error"]}

        # 读取文件内容
        try:
            with open(path, "r", encoding=encoding) as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            encodings = ["gbk", "gb2312", "latin1", "cp1252"]
            content = None
            used_encoding = None

            for enc in encodings:
                try:
                    with open(path, "r", encoding=enc) as f:
                        lines = f.readlines()
                    used_encoding = enc
                    break
                except UnicodeDecodeError:
                    continue

            if used_encoding is None:
                return {"success": False, "error": "无法解码文件，可能是二进制文件"}

            encoding = used_encoding

        # 处理行号和行数限制
        total_lines = len(lines)
        if start_line > total_lines:
            return {
                "success": False,
                "error": f"起始行号{start_line}超过文件总行数{total_lines}",
            }

        start_idx = start_line - 1
        if max_lines:
            end_idx = min(start_idx + max_lines, total_lines)
            selected_lines = lines[start_idx:end_idx]
        else:
            selected_lines = lines[start_idx:]

        content = "".join(selected_lines)

        return {
            "success": True,
            "content": content,
            "encoding": encoding,
            "total_lines": total_lines,
            "returned_lines": len(selected_lines),
            "start_line": start_line,
            "file_info": file_info,
        }

    except Exception as e:
        return {"success": False, "error": f"读取文件失败: {str(e)}"}


@mcp.tool()
async def write_file(
    file_path: str,
    content: str,
    encoding: str = "utf-8",
    mode: str = "w",
    create_dirs: bool = True,
) -> Dict:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认utf-8
        mode: 写入模式，'w'覆盖，'a'追加
        create_dirs: 是否自动创建父目录

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("write", file_path, check_exists=False)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(file_path)

        # 创建父目录（如果需要）
        if create_dirs and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        # 检查写入模式
        if mode not in ["w", "a"]:
            return {
                "success": False,
                "error": "写入模式只支持 'w'（覆盖）或 'a'（追加）",
            }

        # 写入文件
        with open(path, mode, encoding=encoding) as f:
            f.write(content)

        # 获取写入后的文件信息
        file_info = get_file_info(path)

        return {
            "success": True,
            "message": f"文件{'追加' if mode == 'a' else '写入'}成功",
            "bytes_written": len(content.encode(encoding)),
            "file_info": file_info,
        }

    except Exception as e:
        return {"success": False, "error": f"写入文件失败: {str(e)}"}


@mcp.tool()
async def create_file(
    file_path: str, content: str = "", encoding: str = "utf-8", overwrite: bool = False
) -> Dict:
    """
    创建新文件

    Args:
        file_path: 文件路径
        content: 初始内容
        encoding: 文件编码
        overwrite: 是否覆盖已存在的文件

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("create", file_path, check_exists=False)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(file_path)

        # 检查文件是否已存在
        if path.exists() and not overwrite:
            return {"success": False, "error": "文件已存在，使用 overwrite=True 来覆盖"}

        # 创建父目录
        path.parent.mkdir(parents=True, exist_ok=True)

        # 创建文件
        with open(path, "w", encoding=encoding) as f:
            f.write(content)

        # 获取文件信息
        file_info = get_file_info(path)

        return {"success": True, "message": "文件创建成功", "file_info": file_info}

    except Exception as e:
        return {"success": False, "error": f"创建文件失败: {str(e)}"}


@mcp.tool()
async def delete_file(file_path: str, force: bool = False) -> Dict:
    """
    删除文件

    Args:
        file_path: 文件路径
        force: 是否强制删除（忽略权限问题）

    Returns:
        操作结果字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("delete", file_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(file_path)

        if not path.is_file():
            return {"success": False, "error": "指定路径不是文件"}

        # 获取删除前的文件信息
        file_info = get_file_info(path)

        # 删除文件
        if force:
            # 强制删除：先修改权限再删除
            path.chmod(0o777)

        path.unlink()

        return {
            "success": True,
            "message": "文件删除成功",
            "deleted_file_info": file_info,
        }

    except Exception as e:
        return {"success": False, "error": f"删除文件失败: {str(e)}"}


@mcp.tool()
async def copy_file(
    source_path: str,
    destination_path: str,
    overwrite: bool = False,
    preserve_metadata: bool = True,
) -> Dict:
    """
    复制文件

    Args:
        source_path: 源文件路径
        destination_path: 目标文件路径
        overwrite: 是否覆盖已存在的目标文件
        preserve_metadata: 是否保留文件元数据（时间戳、权限等）

    Returns:
        操作结果字典
    """
    try:
        # 验证源文件操作
        is_valid, reason = validate_operation("copy", source_path)
        if not is_valid:
            return {"success": False, "error": f"源文件验证失败: {reason}"}

        # 验证目标文件操作
        is_valid, reason = validate_operation(
            "copy", destination_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": f"目标文件验证失败: {reason}"}

        source = Path(source_path)
        destination = Path(destination_path)

        if not source.is_file():
            return {"success": False, "error": "源路径不是文件"}

        # 检查目标文件是否已存在
        if destination.exists() and not overwrite:
            return {
                "success": False,
                "error": "目标文件已存在，使用 overwrite=True 来覆盖",
            }

        # 创建目标目录
        destination.parent.mkdir(parents=True, exist_ok=True)

        # 复制文件
        if preserve_metadata:
            shutil.copy2(source, destination)
        else:
            shutil.copy(source, destination)

        # 获取文件信息
        source_info = get_file_info(source)
        dest_info = get_file_info(destination)

        return {
            "success": True,
            "message": "文件复制成功",
            "source_info": source_info,
            "destination_info": dest_info,
        }

    except Exception as e:
        return {"success": False, "error": f"复制文件失败: {str(e)}"}


@mcp.tool()
async def move_file(
    source_path: str, destination_path: str, overwrite: bool = False
) -> Dict:
    """
    移动/重命名文件

    Args:
        source_path: 源文件路径
        destination_path: 目标文件路径
        overwrite: 是否覆盖已存在的目标文件

    Returns:
        操作结果字典
    """
    try:
        # 验证源文件操作
        is_valid, reason = validate_operation("move", source_path)
        if not is_valid:
            return {"success": False, "error": f"源文件验证失败: {reason}"}

        # 验证目标文件操作
        is_valid, reason = validate_operation(
            "move", destination_path, check_exists=False
        )
        if not is_valid:
            return {"success": False, "error": f"目标文件验证失败: {reason}"}

        source = Path(source_path)
        destination = Path(destination_path)

        if not source.exists():
            return {"success": False, "error": "源文件不存在"}

        # 检查目标文件是否已存在
        if destination.exists() and not overwrite:
            return {
                "success": False,
                "error": "目标文件已存在，使用 overwrite=True 来覆盖",
            }

        # 获取移动前的文件信息
        source_info = get_file_info(source)

        # 创建目标目录
        destination.parent.mkdir(parents=True, exist_ok=True)

        # 移动文件
        shutil.move(str(source), str(destination))

        # 获取移动后的文件信息
        dest_info = get_file_info(destination)

        return {
            "success": True,
            "message": "文件移动成功",
            "source_info": source_info,
            "destination_info": dest_info,
        }

    except Exception as e:
        return {"success": False, "error": f"移动文件失败: {str(e)}"}


@mcp.tool()
async def get_file_stats(file_path: str) -> Dict:
    """
    获取文件详细统计信息

    Args:
        file_path: 文件路径

    Returns:
        文件统计信息字典
    """
    try:
        # 验证操作
        is_valid, reason = validate_operation("read", file_path)
        if not is_valid:
            return {"success": False, "error": reason}

        path = Path(file_path)

        if not path.is_file():
            return {"success": False, "error": "指定路径不是文件"}

        # 获取基本文件信息
        file_info = get_file_info(path)
        if "error" in file_info:
            return {"success": False, "error": file_info["error"]}

        # 添加额外统计信息
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                file_info["character_count"] = len(content)
                file_info["line_count"] = content.count("\n") + 1 if content else 0
                file_info["word_count"] = len(content.split()) if content else 0
        except UnicodeDecodeError:
            file_info["is_binary"] = True
            file_info["character_count"] = "N/A (binary file)"
            file_info["line_count"] = "N/A (binary file)"
            file_info["word_count"] = "N/A (binary file)"

        file_info["formatted_size"] = format_size(file_info["size"])
        file_info["success"] = True

        return file_info

    except Exception as e:
        return {"success": False, "error": f"获取文件统计失败: {str(e)}"}
