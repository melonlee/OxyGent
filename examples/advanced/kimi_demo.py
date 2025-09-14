#!/usr/bin/env python3
"""
使用 Kimi K2 模型的 OxyGent 示例
演示如何配置和使用 Moonshot Kimi API
"""

import asyncio
import os
from oxygent import MAS, Config, oxy, preset_tools

# 配置 Kimi K2 模型
Config.set_agent_llm_model("kimi_llm")

# Kimi K2 配置参数
KIMI_CONFIG = {
    "api_key": os.getenv("MOONSHOT_API_KEY", "your-moonshot-api-key"),
    "base_url": "https://api.moonshot.cn/v1",
    "model_name": "moonshot-v1-128k",  # 128K 上下文长度
    "temperature": 0.1,
    "max_tokens": 4096,
}

oxy_space = [
    # 配置 Kimi K2 LLM
    oxy.HttpLLM(
        name="kimi_llm",
        api_key=KIMI_CONFIG["api_key"],
        base_url=KIMI_CONFIG["base_url"],
        model_name=KIMI_CONFIG["model_name"],
        llm_params={
            "temperature": KIMI_CONFIG["temperature"],
            "max_tokens": KIMI_CONFIG["max_tokens"],
        },
        semaphore=4,
        timeout=120,
    ),
    
    # 添加工具
    preset_tools.time_tools,
    preset_tools.file_tools,
    preset_tools.math_tools,
    
    # 配置代理
    oxy.ReActAgent(
        name="time_agent",
        desc="时间查询工具",
        tools=["time_tools"],
        llm_model="kimi_llm",
    ),
    
    oxy.ReActAgent(
        name="file_agent", 
        desc="文件操作工具",
        tools=["file_tools"],
        llm_model="kimi_llm",
    ),
    
    oxy.ReActAgent(
        name="math_agent",
        desc="数学计算工具", 
        tools=["math_tools"],
        llm_model="kimi_llm",
    ),
    
    # 主代理
    oxy.ReActAgent(
        is_master=True,
        name="kimi_master_agent",
        desc="基于 Kimi K2 的智能助手",
        sub_agents=["time_agent", "file_agent", "math_agent"],
        llm_model="kimi_llm",
        additional_prompt="""
        你是一个基于 Kimi K2 模型的智能助手，具备以下能力：
        - 强大的编程和代码生成能力
        - 128K 超长上下文记忆
        - 优秀的工具调用能力
        - 智能体任务执行能力
        
        请根据用户需求选择合适的工具来完成任务。
        """,
    ),
]


async def test_kimi_basic():
    """测试 Kimi K2 基础功能"""
    print("🧪 测试 Kimi K2 基础对话...")
    
    async with MAS(oxy_space=oxy_space) as mas:
        # 测试基础对话
        result = await mas.call(
            callee="kimi_master_agent",
            arguments={
                "query": "你好！请介绍一下你的能力。"
            }
        )
        # 处理返回结果，可能是字符串或对象
        output = result.output if hasattr(result, 'output') else str(result)
        print(f"✅ Kimi K2 响应: {output}")
        return True


async def test_kimi_tools():
    """测试 Kimi K2 工具调用"""
    print("\n🔧 测试 Kimi K2 工具调用...")
    
    async with MAS(oxy_space=oxy_space) as mas:
        # 测试工具调用
        result = await mas.call(
            callee="kimi_master_agent", 
            arguments={
                "query": "现在几点了？请计算 123 + 456 的结果，然后将结果保存到 result.txt 文件中。"
            }
        )
        output = result.output if hasattr(result, 'output') else str(result)
        print(f"✅ 工具调用结果: {output}")
        return True


async def test_kimi_long_context():
    """测试 Kimi K2 长上下文能力"""
    print("\n📚 测试 Kimi K2 长上下文能力...")
    
    # 构造长文本
    long_text = "这是一个测试长上下文的文档。" * 1000  # 约 15K 字符
    
    async with MAS(oxy_space=oxy_space) as mas:
        result = await mas.call(
            callee="kimi_master_agent",
            arguments={
                "query": f"请分析以下长文档并总结要点：\n\n{long_text}\n\n请提供简洁的总结。"
            }
        )
        output = result.output if hasattr(result, 'output') else str(result)
        print(f"✅ 长上下文处理结果: {output[:200]}...")
        return True


async def main():
    """主函数"""
    print("🚀 Kimi K2 + OxyGent 集成测试开始...\n")
    
    # 检查配置
    if KIMI_CONFIG["api_key"] == "your-moonshot-api-key":
        print("⚠️  请先配置 MOONSHOT_API_KEY 环境变量或修改代码中的 API 密钥")
        print("   export MOONSHOT_API_KEY='your-actual-api-key'")
        return
    
    try:
        # 运行测试
        await test_kimi_basic()
        await test_kimi_tools() 
        await test_kimi_long_context()
        
        print("\n🎉 所有测试通过！Kimi K2 集成成功")
        
        # 启动 Web 服务
        print("\n🌐 启动 Web 服务...")
        async with MAS(oxy_space=oxy_space) as mas:
            await mas.start_web_service(
                first_query="你好！我是基于 Kimi K2 的智能助手，有什么可以帮助你的吗？",
                welcome_message="欢迎使用 Kimi K2 + OxyGent 智能助手！"
            )
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查 API 密钥是否正确")
        print("2. 检查网络连接")
        print("3. 确认 Moonshot API 服务可用")


if __name__ == "__main__":
    asyncio.run(main())
