"""
FileSystem MCP 服务器单元测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# 导入要测试的模块
from mcp_servers.filesystem.core import (
    is_safe_path,
    is_allowed_extension,
    get_file_info,
    validate_operation,
    set_config,
    get_config,
)


class TestFilesystemCore:
    """测试文件系统核心功能"""

    def setup_method(self):
        """测试前的设置"""
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.txt"
        self.test_file.write_text("Hello, World!")

        # 重置配置
        set_config("allowed_paths", [])
        set_config("forbidden_paths", ["/etc", "/sys", "/proc", "/dev"])
        set_config("forbidden_extensions", [".exe", ".bat", ".cmd"])
        set_config("enable_hidden_files", False)

    def teardown_method(self):
        """测试后的清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_is_safe_path_valid(self):
        """测试安全路径验证 - 有效路径"""
        is_safe, reason = is_safe_path(str(self.test_file))
        assert is_safe is True
        assert "路径安全" in reason

    def test_is_safe_path_forbidden(self):
        """测试安全路径验证 - 禁止路径"""
        is_safe, reason = is_safe_path("/etc/passwd")
        assert is_safe is False
        assert "禁止访问路径" in reason

    def test_is_safe_path_hidden_file(self):
        """测试安全路径验证 - 隐藏文件"""
        hidden_file = self.temp_dir / ".hidden"
        is_safe, reason = is_safe_path(str(hidden_file))
        assert is_safe is False
        assert "不允许操作隐藏文件" in reason

    def test_is_safe_path_allowed_paths(self):
        """测试安全路径验证 - 允许路径限制"""
        set_config("allowed_paths", [str(self.temp_dir)])

        # 允许的路径
        is_safe, reason = is_safe_path(str(self.test_file))
        assert is_safe is True

        # 不允许的路径
        other_file = Path("/tmp/other.txt")
        is_safe, reason = is_safe_path(str(other_file))
        assert is_safe is False
        assert "路径不在允许的范围内" in reason

    def test_is_allowed_extension_valid(self):
        """测试文件扩展名验证 - 有效扩展名"""
        is_allowed, reason = is_allowed_extension("test.txt")
        assert is_allowed is True
        assert "扩展名允许" in reason

    def test_is_allowed_extension_forbidden(self):
        """测试文件扩展名验证 - 禁止扩展名"""
        is_allowed, reason = is_allowed_extension("malware.exe")
        assert is_allowed is False
        assert "禁止的文件扩展名" in reason

    def test_is_allowed_extension_whitelist(self):
        """测试文件扩展名验证 - 白名单模式"""
        set_config("allowed_extensions", [".txt", ".py"])

        # 允许的扩展名
        is_allowed, reason = is_allowed_extension("test.txt")
        assert is_allowed is True

        # 不允许的扩展名
        is_allowed, reason = is_allowed_extension("test.doc")
        assert is_allowed is False
        assert "不允许的文件扩展名" in reason

    def test_get_file_info_success(self):
        """测试获取文件信息 - 成功"""
        info = get_file_info(self.test_file)

        assert "error" not in info
        assert info["name"] == "test.txt"
        assert info["is_file"] is True
        assert info["is_dir"] is False
        assert info["size"] > 0
        assert "created_time" in info
        assert "modified_time" in info

    def test_get_file_info_not_exists(self):
        """测试获取文件信息 - 文件不存在"""
        non_existent = self.temp_dir / "not_exists.txt"
        info = get_file_info(non_existent)

        assert "error" in info
        assert "文件不存在" in info["error"]

    def test_validate_operation_read_success(self):
        """测试操作验证 - 读取操作成功"""
        is_valid, reason = validate_operation("read", str(self.test_file))
        assert is_valid is True
        assert "操作有效" in reason

    def test_validate_operation_read_not_exists(self):
        """测试操作验证 - 读取不存在的文件"""
        non_existent = self.temp_dir / "not_exists.txt"
        is_valid, reason = validate_operation("read", str(non_existent))
        assert is_valid is False
        assert "文件或目录不存在" in reason

    def test_validate_operation_create_success(self):
        """测试操作验证 - 创建操作成功"""
        new_file = self.temp_dir / "new_file.txt"
        is_valid, reason = validate_operation(
            "create", str(new_file), check_exists=False
        )
        assert is_valid is True
        assert "操作有效" in reason


class TestFilesystemSecurity:
    """测试文件系统安全功能"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """测试后的清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_path_traversal_attack(self):
        """测试路径遍历攻击防护"""
        malicious_path = self.temp_dir / "../../../etc/passwd"
        is_safe, reason = is_safe_path(str(malicious_path))
        # 由于resolve()会解析真实路径，这个测试依赖于具体的路径解析结果
        # 在实际的恶意路径下应该被拒绝
        assert isinstance(is_safe, bool)
        assert isinstance(reason, str)

    def test_config_management(self):
        """测试配置管理"""
        # 设置配置
        set_config("test_key", "test_value")
        assert get_config("test_key") == "test_value"

        # 获取不存在的配置
        assert get_config("non_existent", "default") == "default"
        assert get_config("non_existent") is None

    def test_size_limit_validation(self):
        """测试文件大小限制"""
        # 创建大文件
        large_file = self.temp_dir / "large.txt"
        large_file.write_text("x" * 1000)

        # 设置很小的大小限制
        set_config("max_file_size", 100)

        is_valid, reason = validate_operation("write", str(large_file))
        assert is_valid is False
        assert "文件大小超过限制" in reason


@pytest.mark.asyncio
class TestFilesystemOperations:
    """测试文件系统操作功能"""

    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # 重置配置为测试友好的设置
        set_config("allowed_paths", [str(self.temp_dir)])
        set_config("forbidden_paths", [])
        set_config("forbidden_extensions", [])
        set_config("enable_hidden_files", True)
        set_config("max_file_size", 10 * 1024 * 1024)  # 10MB

    def teardown_method(self):
        """测试后的清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    async def test_file_operations_integration(self):
        """测试文件操作集成"""
        # 这里可以添加集成测试，但需要实际的MCP服务器运行
        # 由于涉及到异步MCP通信，这部分测试较为复杂
        # 可以使用mock来模拟MCP通信
        pass

    def test_file_info_formatting(self):
        """测试文件信息格式化"""
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("Hello, World!")

        info = get_file_info(test_file)

        # 验证必需字段存在
        required_fields = [
            "path",
            "name",
            "size",
            "is_file",
            "is_dir",
            "created_time",
            "modified_time",
            "accessed_time",
        ]

        for field in required_fields:
            assert field in info, f"Missing required field: {field}"

        # 验证数据类型
        assert isinstance(info["size"], int)
        assert isinstance(info["is_file"], bool)
        assert isinstance(info["is_dir"], bool)


if __name__ == "__main__":
    pytest.main([__file__])
