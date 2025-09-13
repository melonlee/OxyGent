# FileSystem MCP 服务器

FileSystem MCP 服务器提供了完整的文件系统操作能力，支持文件和目录的各种操作，同时具备强大的安全控制机制。

## 🌟 主要特性

### 📁 文件操作
- **读取文件**: 支持多种编码，自动检测文件类型
- **写入文件**: 支持覆盖和追加模式
- **创建文件**: 自动创建父目录
- **删除文件**: 支持强制删除
- **复制文件**: 保留或不保留元数据
- **移动文件**: 支持重命名和移动
- **文件统计**: 详细的文件信息和统计数据

### 📂 目录操作
- **列出目录**: 支持递归列表、排序、过滤
- **创建目录**: 自动创建父目录
- **删除目录**: 支持递归删除和强制删除
- **复制目录**: 完整的目录树复制
- **移动目录**: 目录重命名和移动
- **目录统计**: 大小统计和空目录查找

### 🔍 高级操作
- **文件搜索**: 支持glob、正则表达式和内容搜索
- **压缩档案**: 支持ZIP、TAR、TAR.GZ、TAR.BZ2格式
- **解压档案**: 安全的档案解压
- **权限管理**: Unix/Linux系统的文件权限设置
- **重复文件**: 基于大小、哈希值或文件名的重复检测

### 🔒 安全控制
- **路径验证**: 防止路径遍历攻击
- **扩展名过滤**: 可配置的文件类型限制
- **大小限制**: 防止过大文件操作
- **权限检查**: 细粒度的访问控制
- **隐藏文件**: 可配置的隐藏文件处理

## 🚀 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install oxygent

# 设置环境变量（可选）
export FS_MAX_FILE_SIZE="10485760"  # 10MB
export FS_ALLOWED_PATHS="/home/user/documents,/home/user/projects"
export FS_FORBIDDEN_PATHS="/etc,/sys,/proc,/dev"
export FS_FORBIDDEN_EXTENSIONS=".exe,.bat,.cmd,.sh,.ps1"
export FS_ENABLE_HIDDEN_FILES="false"
```

### 2. 基本使用

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
            payload={"query": "创建一个名为test.txt的文件，内容为'Hello World'"}
        )
        print(response.output)

asyncio.run(main())
```

## 🛠️ 可用工具

### 文件操作工具

| 工具名称 | 描述 | 主要参数 |
|---------|------|----------|
| `read_file` | 读取文件内容 | `file_path`, `encoding`, `max_lines`, `start_line` |
| `write_file` | 写入文件内容 | `file_path`, `content`, `encoding`, `mode`, `create_dirs` |
| `create_file` | 创建新文件 | `file_path`, `content`, `encoding`, `overwrite` |
| `delete_file` | 删除文件 | `file_path`, `force` |
| `copy_file` | 复制文件 | `source_path`, `destination_path`, `overwrite`, `preserve_metadata` |
| `move_file` | 移动/重命名文件 | `source_path`, `destination_path`, `overwrite` |
| `get_file_stats` | 获取文件统计信息 | `file_path` |

### 目录操作工具

| 工具名称 | 描述 | 主要参数 |
|---------|------|----------|
| `list_directory` | 列出目录内容 | `directory_path`, `show_hidden`, `recursive`, `max_depth`, `sort_by` |
| `create_directory` | 创建目录 | `directory_path`, `parents`, `exist_ok` |
| `delete_directory` | 删除目录 | `directory_path`, `recursive`, `force` |
| `copy_directory` | 复制目录 | `source_path`, `destination_path`, `overwrite`, `preserve_metadata` |
| `move_directory` | 移动/重命名目录 | `source_path`, `destination_path`, `overwrite` |
| `get_directory_size` | 获取目录大小统计 | `directory_path`, `include_subdirs` |
| `find_empty_directories` | 查找空目录 | `directory_path`, `recursive` |

### 高级操作工具

| 工具名称 | 描述 | 主要参数 |
|---------|------|----------|
| `search_files` | 搜索文件 | `search_path`, `pattern`, `search_type`, `recursive`, `max_results` |
| `create_archive` | 创建压缩档案 | `source_path`, `archive_path`, `archive_type`, `compression_level` |
| `extract_archive` | 解压档案 | `archive_path`, `extract_path`, `overwrite`, `members` |
| `set_file_permissions` | 设置文件权限 | `file_path`, `permissions`, `recursive` |
| `find_duplicates` | 查找重复文件 | `search_path`, `method`, `recursive`, `min_size` |

### 系统工具

| 工具名称 | 描述 | 主要参数 |
|---------|------|----------|
| `get_server_info` | 获取服务器信息 | 无 |
| `health_check` | 健康检查 | 无 |

## 🔧 配置选项

### 环境变量配置

| 变量名 | 默认值 | 描述 |
|-------|--------|------|
| `FS_MAX_FILE_SIZE` | `104857600` (100MB) | 最大文件大小限制 |
| `FS_ALLOWED_PATHS` | 空 | 允许访问的路径列表（逗号分隔） |
| `FS_FORBIDDEN_PATHS` | `/etc,/sys,/proc,/dev` | 禁止访问的路径列表 |
| `FS_FORBIDDEN_EXTENSIONS` | `.exe,.bat,.cmd,.sh,.ps1` | 禁止的文件扩展名 |
| `FS_ENABLE_HIDDEN_FILES` | `false` | 是否允许操作隐藏文件 |
| `FS_ENABLE_SYSTEM_FILES` | `false` | 是否允许操作系统文件 |

### 代码配置

```python
from mcp_servers.filesystem.core import set_config

# 设置最大文件大小为50MB
set_config("max_file_size", 50 * 1024 * 1024)

# 设置允许的路径
set_config("allowed_paths", ["/home/user/documents", "/tmp"])

# 设置禁止的扩展名
set_config("forbidden_extensions", [".exe", ".bat", ".cmd"])
```

## 💡 使用示例

### 文件操作示例

```python
# 读取文件
response = await mas.chat_with_agent(
    payload={"query": "读取 /path/to/file.txt 的内容"}
)

# 创建文件
response = await mas.chat_with_agent(
    payload={"query": "创建一个文件 /path/to/new.txt，内容为 'Hello World'"}
)

# 复制文件
response = await mas.chat_with_agent(
    payload={"query": "将 source.txt 复制为 backup.txt"}
)
```

### 目录操作示例

```python
# 列出目录
response = await mas.chat_with_agent(
    payload={"query": "列出 /home/user 目录的所有文件，按大小排序"}
)

# 创建目录
response = await mas.chat_with_agent(
    payload={"query": "创建目录 /path/to/new/directory"}
)

# 获取目录大小
response = await mas.chat_with_agent(
    payload={"query": "获取 /home/user/documents 目录的总大小"}
)
```

### 高级操作示例

```python
# 搜索文件
response = await mas.chat_with_agent(
    payload={"query": "在 /home/user 中搜索所有 .py 文件"}
)

# 创建压缩包
response = await mas.chat_with_agent(
    payload={"query": "将 /path/to/directory 压缩为 backup.zip"}
)

# 查找重复文件
response = await mas.chat_with_agent(
    payload={"query": "在 /home/user/downloads 中查找重复的文件"}
)
```

## 🔐 安全考虑

### 路径安全
- 自动检测和阻止路径遍历攻击（如 `../../../etc/passwd`）
- 支持路径白名单和黑名单配置
- 隐藏文件访问控制

### 文件类型安全
- 可配置的文件扩展名过滤
- 自动检测和阻止危险文件类型
- 二进制文件处理保护

### 资源限制
- 文件大小限制防止资源耗尽
- 搜索结果数量限制
- 递归深度限制

### 权限控制
- 基于文件系统权限的访问控制
- 强制删除的权限检查
- 操作日志和审计

## 🚨 故障排除

### 常见问题

1. **权限被拒绝**
   - 检查文件/目录权限
   - 确认路径在允许范围内
   - 检查用户权限

2. **文件编码错误**
   - 指定正确的编码格式
   - 使用自动编码检测
   - 检查文件是否为二进制文件

3. **路径不安全**
   - 检查路径是否在禁止列表中
   - 确认路径格式正确
   - 检查隐藏文件设置

4. **文件大小超限**
   - 调整 `FS_MAX_FILE_SIZE` 配置
   - 分块处理大文件
   - 使用压缩减小文件大小

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 启用详细日志
oxy.StdioMCPClient(
    name="filesystem_server",
    command="python",
    args=["-m", "mcp_servers.filesystem.server", "--debug"],
)
```

## 📈 性能优化

### 大文件处理
- 使用流式读取处理大文件
- 分块写入避免内存溢出
- 异步I/O提高并发性能

### 目录遍历
- 限制递归深度避免无限循环
- 使用生成器减少内存占用
- 并行处理提高效率

### 搜索优化
- 使用索引加速搜索
- 限制搜索结果数量
- 缓存常用查询结果

## 🤝 贡献指南

欢迎为 FileSystem MCP 服务器贡献代码！

1. Fork 项目
2. 创建功能分支
3. 添加测试
4. 提交 Pull Request

### 开发环境设置

```bash
git clone https://github.com/jd-opensource/OxyGent.git
cd OxyGent
pip install -r requirements.txt
pip install pytest pytest-asyncio

# 运行测试
pytest test/unittest/test_filesystem_mcp.py
```

## 📄 许可证

本项目采用 Apache License 2.0 许可证。详见 [LICENSE](../../LICENSE) 文件。
