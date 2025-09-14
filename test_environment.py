#!/usr/bin/env python3
"""
OxyGent 环境检查脚本
检查本地运行 OxyGent 所需的所有依赖和配置
"""

import asyncio
import sys
import os
import subprocess
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"🐍 Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 10):
        print("✅ Python 版本符合要求 (>= 3.10)")
        return True
    elif version >= (3, 8):
        print("⚠️  Python 版本可用但建议升级到 3.10+ (当前 >= 3.8)")
        return True
    else:
        print("❌ Python 版本过低，需要 >= 3.8")
        return False


def check_node_version():
    """检查 Node.js 版本"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"📦 Node.js 版本: {version}")
            
            # 提取版本号
            version_num = int(version.lstrip('v').split('.')[0])
            if version_num >= 18:
                print("✅ Node.js 版本符合要求 (>= 18)")
                return True
            else:
                print("❌ Node.js 版本过低，需要 >= 18")
                return False
        else:
            print("❌ Node.js 未安装或不可用")
            return False
    except FileNotFoundError:
        print("❌ Node.js 未安装")
        return False


def check_package_managers():
    """检查包管理器"""
    managers = {}
    
    # 检查 pip
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            managers['pip'] = result.stdout.strip().split()[1]
            print(f"📦 pip 版本: {managers['pip']}")
        else:
            managers['pip'] = None
    except:
        managers['pip'] = None
    
    # 检查 uv
    try:
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            managers['uv'] = result.stdout.strip().split()[1]
            print(f"⚡ uv 版本: {managers['uv']}")
        else:
            managers['uv'] = None
    except FileNotFoundError:
        managers['uv'] = None
    
    # 检查 npx
    try:
        result = subprocess.run(['npx', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            managers['npx'] = result.stdout.strip()
            print(f"📦 npx 版本: {managers['npx']}")
        else:
            managers['npx'] = None
    except FileNotFoundError:
        managers['npx'] = None
    
    return managers


async def check_python_dependencies():
    """检查 Python 依赖包"""
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'httpx', 
        'aioredis', 'websockets', 'aiofiles'
    ]
    
    optional_packages = [
        'mcp', 'openai', 'numpy', 'pandas', 'pillow',
        'elasticsearch', 'pytest'
    ]
    
    missing_required = []
    missing_optional = []
    
    print("\n🔍 检查核心 Python 依赖...")
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package}")
    
    print("\n🔍 检查可选 Python 依赖...")
    for package in optional_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (可选)")
    
    return missing_required, missing_optional


async def check_oxygent_import():
    """检查 OxyGent 导入"""
    try:
        from oxygent import MAS, Config, oxy
        print("✅ OxyGent 核心模块导入成功")
        
        # 检查主要组件
        components = ['HttpLLM', 'ReActAgent', 'ChatAgent', 'FunctionHub']
        for comp in components:
            if hasattr(oxy, comp):
                print(f"✅ oxy.{comp} 可用")
            else:
                print(f"❌ oxy.{comp} 不可用")
        
        return True
    except ImportError as e:
        print(f"❌ OxyGent 导入失败: {e}")
        return False


def check_environment_variables():
    """检查环境变量"""
    required_env = [
        'DEFAULT_LLM_API_KEY',
        'DEFAULT_LLM_BASE_URL', 
        'DEFAULT_LLM_MODEL_NAME'
    ]
    
    # 检查 Kimi 配置
    kimi_env = [
        'MOONSHOT_API_KEY'
    ]
    
    optional_env = [
        'ES_HOST_1', 'REDIS_HOST', 'VEARCH_ROUTER_URL'
    ]
    
    print("\n🔍 检查环境变量...")
    
    missing_required = []
    for var in required_env:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            missing_required.append(var)
            print(f"❌ {var}")
    
    # 检查 Kimi 配置
    kimi_configured = False
    for var in kimi_env:
        if os.getenv(var):
            print(f"🌙 {var} (Kimi 配置)")
            kimi_configured = True
        else:
            print(f"⚠️  {var} (Kimi 可选)")
    
    missing_optional = []
    for var in optional_env:
        if os.getenv(var):
            print(f"✅ {var}")
        else:
            missing_optional.append(var)
            print(f"⚠️  {var} (可选)")
    
    # 如果配置了 Kimi，给出提示
    if kimi_configured:
        print("💡 检测到 Kimi 配置，可以使用 examples/advanced/kimi_demo.py")
    
    return missing_required, missing_optional


def check_project_files():
    """检查项目文件"""
    required_files = [
        'requirements.txt', 'config.json', 'demo.py'
    ]
    
    optional_files = [
        '.env', 'pytest.ini'
    ]
    
    print("\n🔍 检查项目文件...")
    
    missing_required = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            missing_required.append(file)
            print(f"❌ {file}")
    
    missing_optional = []
    for file in optional_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            missing_optional.append(file)
            print(f"⚠️  {file} (可选)")
    
    return missing_required, missing_optional


async def run_basic_test():
    """运行基础功能测试"""
    try:
        print("\n🧪 运行基础功能测试...")
        
        # 测试 MAS 创建
        from oxygent import MAS, oxy
        
        test_oxy_space = [
            oxy.ReActAgent(name="test_agent", is_master=True)
        ]
        
        # 不启动实际服务，只测试创建
        mas = MAS(oxy_space=test_oxy_space)
        print("✅ MAS 实例创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False


def generate_setup_commands(missing_deps, missing_env, managers):
    """生成设置命令"""
    commands = []
    
    print("\n🛠️  推荐的设置命令:")
    
    # 安装缺失的依赖
    if missing_deps:
        if managers.get('uv'):
            cmd = f"uv pip install {' '.join(missing_deps)}"
        else:
            cmd = f"pip3 install {' '.join(missing_deps)}"
        commands.append(cmd)
        print(f"📦 安装依赖: {cmd}")
    
    # 设置环境变量
    if missing_env:
        print("🔧 设置环境变量:")
        for var in missing_env:
            print(f"   export {var}='your_value_here'")
    
    # 安装 UV (如果没有)
    if not managers.get('uv'):
        cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        commands.append(cmd)
        print(f"⚡ 安装 UV: {cmd}")
    
    return commands


async def main():
    """主函数"""
    print("🚀 OxyGent 环境检查开始...\n")
    
    # 系统环境检查
    python_ok = check_python_version()
    node_ok = check_node_version()
    managers = check_package_managers()
    
    # Python 依赖检查
    missing_required, missing_optional = await check_python_dependencies()
    
    # OxyGent 导入检查
    oxygent_ok = await check_oxygent_import()
    
    # 环境变量检查
    missing_env_required, missing_env_optional = check_environment_variables()
    
    # 项目文件检查
    missing_files_required, missing_files_optional = check_project_files()
    
    # 基础功能测试
    if oxygent_ok:
        test_ok = await run_basic_test()
    else:
        test_ok = False
    
    # 生成总结报告
    print("\n" + "="*60)
    print("📊 环境检查总结")
    print("="*60)
    
    # 计算总体状态
    critical_issues = []
    if not python_ok:
        critical_issues.append("Python 版本")
    if missing_required:
        critical_issues.append("核心 Python 依赖")
    if not oxygent_ok:
        critical_issues.append("OxyGent 导入")
    if missing_env_required:
        critical_issues.append("必需环境变量")
    if missing_files_required:
        critical_issues.append("项目文件")
    
    if not critical_issues:
        print("🎉 环境检查通过！OxyGent 可以正常运行")
        print("\n✅ 可以运行以下命令测试:")
        print("   python3 demo.py")
        print("   python3 -m examples.agents.single_demo")
    else:
        print("❌ 发现关键问题，需要解决:")
        for issue in critical_issues:
            print(f"   • {issue}")
        
        # 生成修复命令
        generate_setup_commands(
            missing_required, 
            missing_env_required, 
            managers
        )
    
    # 可选改进建议
    suggestions = []
    if not node_ok:
        suggestions.append("安装/升级 Node.js (用于 MCP 服务器)")
    if missing_optional:
        suggestions.append(f"安装可选依赖: {', '.join(missing_optional)}")
    if not managers.get('uv'):
        suggestions.append("安装 UV 包管理器 (更快的依赖管理)")
    
    if suggestions:
        print("\n💡 可选改进建议:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    print(f"\n📋 详细设置指南: LOCAL_SETUP_GUIDE.md")


if __name__ == "__main__":
    asyncio.run(main())
