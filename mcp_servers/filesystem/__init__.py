"""
FileSystem MCP Server

这个包提供了文件系统操作的 MCP 服务器实现，包括：
- 文件操作（读取、写入、创建、删除）
- 目录操作（列表、创建、删除、遍历）
- 高级操作（搜索、压缩、权限管理）
- 安全控制（路径验证、权限检查）
"""

from .server import main

__all__ = ["main"]
