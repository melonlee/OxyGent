# FileSystem MCP 服务器 - PR 说明

## 🎯 PR 概述

本 PR 实现了完整的 **FileSystem MCP 服务器**，为 OxyGent 框架提供了强大的文件系统操作能力，填补了在文件管理方面的重要空白。

## 🚀 主要特性

### 📁 核心文件操作
- **文件读写**: 支持多种编码格式，自动编码检测
- **文件管理**: 创建、删除、复制、移动操作
- **文件统计**: 详细的文件信息和统计数据

### 📂 目录操作
- **目录管理**: 创建、删除、复制、移动目录
- **目录浏览**: 递归列表、排序、过滤功能
- **目录统计**: 大小统计、空目录检测

### 🔍 高级功能
- **文件搜索**: 支持 glob、正则表达式、内容搜索
- **压缩档案**: ZIP、TAR、TAR.GZ、TAR.BZ2 格式支持
- **重复检测**: 基于大小、哈希值、文件名的重复文件检测
- **权限管理**: Unix/Linux 系统文件权限设置

### 🔒 安全控制
- **路径验证**: 防止路径遍历攻击
- **访问控制**: 可配置的路径白名单/黑名单
- **文件类型**: 扩展名过滤和大小限制
- **权限检查**: 细粒度的文件系统权限控制

## 📦 新增文件

```
mcp_servers/filesystem/
├── __init__.py              # 包初始化
├── core.py                  # 核心功能和安全控制
├── file_operations.py       # 文件操作工具
├── directory_operations.py  # 目录操作工具
├── advanced_operations.py   # 高级操作工具
└── server.py               # MCP 服务器入口

examples/advanced/
└── filesystem_mcp_demo.py  # 使用示例

test/unittest/
└── test_filesystem_mcp.py  # 单元测试

docs/docs_zh/
└── filesystem_mcp_server.md # 详细文档
```

## 🛠️ 可用工具 (共 19 个)

### 文件操作 (7个)
- `read_file` - 读取文件内容
- `write_file` - 写入文件内容  
- `create_file` - 创建新文件
- `delete_file` - 删除文件
- `copy_file` - 复制文件
- `move_file` - 移动/重命名文件
- `get_file_stats` - 获取文件统计信息

### 目录操作 (7个)
- `list_directory` - 列出目录内容
- `create_directory` - 创建目录
- `delete_directory` - 删除目录
- `copy_directory` - 复制目录
- `move_directory` - 移动/重命名目录
- `get_directory_size` - 获取目录大小统计
- `find_empty_directories` - 查找空目录

### 高级操作 (5个)
- `search_files` - 文件搜索
- `create_archive` - 创建压缩档案
- `extract_archive` - 解压档案
- `set_file_permissions` - 设置文件权限
- `find_duplicates` - 查找重复文件

## 🔧 配置选项

支持通过环境变量进行安全配置：

```bash
FS_MAX_FILE_SIZE="10485760"          # 最大文件大小 (10MB)
FS_ALLOWED_PATHS="/home/user/docs"   # 允许访问的路径
FS_FORBIDDEN_PATHS="/etc,/sys"       # 禁止访问的路径  
FS_FORBIDDEN_EXTENSIONS=".exe,.bat"  # 禁止的文件扩展名
FS_ENABLE_HIDDEN_FILES="false"       # 是否允许隐藏文件
```

## 💡 使用示例

```python
import asyncio
from oxygent import MAS, oxy

async def main():
    oxy_space = [
        # FileSystem MCP 客户端
        oxy.StdioMCPClient(
            name="filesystem_server",
            desc="文件系统操作服务器",
            command="python",
            args=["-m", "mcp_servers.filesystem.server"],
        ),
        
        # Agent
        oxy.ReActAgent(
            name="fs_agent",
            desc="文件系统操作助手",
            tools=["filesystem_server"],
        ),
    ]
    
    async with MAS(oxy_space=oxy_space) as mas:
        # 创建文件
        response = await mas.chat_with_agent(
            payload={"query": "创建一个test.txt文件，内容为'Hello World'"}
        )
        print(response.output)

asyncio.run(main())
```

## 🧪 测试覆盖

- ✅ 核心功能单元测试
- ✅ 安全控制测试  
- ✅ 路径验证测试
- ✅ 配置管理测试
- ✅ 完整的使用示例

## 📈 性能特点

- **内存优化**: 大文件流式处理
- **并发支持**: 异步 I/O 操作
- **安全第一**: 多层安全验证
- **高度可配**: 灵活的配置选项

## 🎯 解决的问题

1. **文件系统操作缺口**: OxyGent 之前缺乏完整的文件系统操作能力
2. **企业级安全需求**: 提供了企业级的安全控制机制
3. **开发者体验**: 简单易用的 API 和丰富的功能
4. **与主流框架对比**: 在文件操作能力上达到甚至超越主流 AI Agent 框架

## 🔄 与现有功能的集成

- 完全兼容现有的 MCP 架构
- 遵循 OxyGent 的设计模式
- 支持与其他 Agent 和工具的协作
- 可以通过配置灵活启用/禁用功能

## 📋 后续计划

1. **扩展格式支持**: 更多压缩格式和文件类型
2. **云存储集成**: 支持 S3、Azure Blob 等云存储
3. **文件监控**: 实时文件系统事件监控
4. **性能优化**: 更高效的大文件处理

---

这个 PR 显著增强了 OxyGent 的实用性，特别是在企业级应用场景中，为文件管理和自动化任务提供了强大的基础设施支持。
