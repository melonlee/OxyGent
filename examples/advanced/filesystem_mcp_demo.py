"""
FileSystem MCP 服务器使用示例

本示例演示如何使用 FileSystem MCP 服务器进行各种文件系统操作
"""

import asyncio
import os
from pathlib import Path

from oxygent import MAS, Config, oxy


async def main():
    """FileSystem MCP 服务器使用示例"""

    # 配置 LLM
    Config.set_agent_llm_model("default_llm")

    # 创建 oxy_space，包含 FileSystem MCP 客户端和 Agent
    oxy_space = [
        # LLM 配置
        oxy.HttpLLM(
            name="default_llm",
            api_key=os.getenv("DEFAULT_LLM_API_KEY"),
            base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
            model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
        ),
        # FileSystem MCP 客户端
        oxy.StdioMCPClient(
            name="filesystem_server",
            desc="文件系统操作服务器",
            command="python",
            args=["-m", "mcp_servers.filesystem.server"],
            env={
                "FS_MAX_FILE_SIZE": "10485760",  # 10MB
                "FS_ALLOWED_PATHS": f"{Path.home()}/Documents,{Path.cwd()}",
                "FS_FORBIDDEN_PATHS": "/etc,/sys,/proc,/dev",
                "FS_FORBIDDEN_EXTENSIONS": ".exe,.bat,.cmd,.sh,.ps1",
                "FS_ENABLE_HIDDEN_FILES": "false",
                "FS_ENABLE_SYSTEM_FILES": "false",
            },
        ),
        # 文件系统操作 Agent
        oxy.ReActAgent(
            name="filesystem_agent",
            desc="专业的文件系统操作助手，可以进行文件和目录的各种操作",
            tools=["filesystem_server"],
        ),
        # 主控 Agent
        oxy.ReActAgent(
            is_master=True,
            name="master_agent",
            desc="主控制器，负责协调文件系统操作",
            sub_agents=["filesystem_agent"],
        ),
    ]

    async with MAS(oxy_space=oxy_space) as mas:
        print("🚀 FileSystem MCP 服务器示例启动")
        print("=" * 60)

        # 示例1: 获取服务器信息
        print("\n📋 示例1: 获取服务器信息")
        response = await mas.chat_with_agent(
            payload={"query": "获取文件系统服务器的信息和配置"}
        )
        print(f"结果: {response.output}")

        # 示例2: 创建测试目录和文件
        print("\n📁 示例2: 创建测试目录和文件")
        test_dir = Path.cwd() / "filesystem_test"
        response = await mas.chat_with_agent(
            payload={
                "query": f"在 {test_dir} 创建一个测试目录，然后在其中创建一个名为 hello.txt 的文件，内容为 'Hello FileSystem MCP!'"
            }
        )
        print(f"结果: {response.output}")

        # 示例3: 读取文件内容
        print("\n📄 示例3: 读取文件内容")
        response = await mas.chat_with_agent(
            payload={"query": f"读取 {test_dir}/hello.txt 文件的内容"}
        )
        print(f"结果: {response.output}")

        # 示例4: 列出目录内容
        print("\n📋 示例4: 列出目录内容")
        response = await mas.chat_with_agent(
            payload={"query": f"列出 {test_dir} 目录的详细内容，包括文件大小和修改时间"}
        )
        print(f"结果: {response.output}")

        # 示例5: 搜索文件
        print("\n🔍 示例5: 搜索文件")
        response = await mas.chat_with_agent(
            payload={
                "query": f"在 {Path.cwd()} 目录中搜索所有 .py 文件，限制结果为前10个"
            }
        )
        print(f"结果: {response.output}")

        # 示例6: 复制文件
        print("\n📋 示例6: 复制文件")
        response = await mas.chat_with_agent(
            payload={
                "query": f"将 {test_dir}/hello.txt 复制为 {test_dir}/hello_copy.txt"
            }
        )
        print(f"结果: {response.output}")

        # 示例7: 获取目录大小统计
        print("\n📊 示例7: 获取目录大小统计")
        response = await mas.chat_with_agent(
            payload={"query": f"获取 {test_dir} 目录的大小统计信息"}
        )
        print(f"结果: {response.output}")

        # 示例8: 创建压缩档案
        print("\n🗜️ 示例8: 创建压缩档案")
        response = await mas.chat_with_agent(
            payload={"query": f"将 {test_dir} 目录压缩为 {test_dir}.zip 档案"}
        )
        print(f"结果: {response.output}")

        # 示例9: 健康检查
        print("\n🏥 示例9: 系统健康检查")
        response = await mas.chat_with_agent(
            payload={"query": "执行文件系统服务器的健康检查，显示系统资源使用情况"}
        )
        print(f"结果: {response.output}")

        # 示例10: 清理测试文件
        print("\n🧹 示例10: 清理测试文件")
        response = await mas.chat_with_agent(
            payload={
                "query": f"删除测试目录 {test_dir} 及其所有内容，还有压缩档案 {test_dir}.zip"
            }
        )
        print(f"结果: {response.output}")

        print("\n✅ FileSystem MCP 服务器示例完成!")


if __name__ == "__main__":
    asyncio.run(main())
