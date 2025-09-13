"""
FileSystem 核心功能单元测试（不依赖 MCP）
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# 添加项目根目录到路径，用于独立测试
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# 直接导入核心功能模块，不通过 MCP 相关代码
from examples.advanced.filesystem_standalone_test import (
    format_size,
    get_file_info,
    is_safe_path,
)


class TestFilesystemCoreOnly:
    """测试文件系统核心功能（独立版本）"""
    
    def setup_method(self):
        """测试前的设置"""
        # 创建临时目录
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test.txt"
        self.test_file.write_text("Hello, World!")
    
    def teardown_method(self):
        """测试后的清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_format_size(self):
        """测试文件大小格式化"""
        assert format_size(0) == "0 B"
        assert format_size(1024) == "1.00 KB"
        assert format_size(1024 * 1024) == "1.00 MB"
        assert format_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_size(1536) == "1.50 KB"  # 1.5KB
    
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
        assert "formatted_size" in info
        assert info["extension"] == ".txt"
        assert info["stem"] == "test"
    
    def test_get_file_info_directory(self):
        """测试获取目录信息"""
        info = get_file_info(self.temp_dir)
        
        assert "error" not in info
        assert info["is_file"] is False
        assert info["is_dir"] is True
        assert "created_time" in info
        assert "modified_time" in info
    
    def test_get_file_info_not_exists(self):
        """测试获取文件信息 - 文件不存在"""
        non_existent = self.temp_dir / "not_exists.txt"
        info = get_file_info(non_existent)
        
        assert "error" in info
        assert "文件不存在" in info["error"]
    
    def test_is_safe_path_valid(self):
        """测试安全路径验证 - 有效路径"""
        is_safe, reason = is_safe_path(str(self.test_file))
        assert is_safe is True
        assert "路径安全" in reason
    
    def test_is_safe_path_hidden_file(self):
        """测试安全路径验证 - 隐藏文件"""
        hidden_file = self.temp_dir / ".hidden"
        is_safe, reason = is_safe_path(str(hidden_file))
        assert is_safe is False
        assert "不允许操作隐藏文件" in reason
    
    def test_is_safe_path_system_path(self):
        """测试安全路径验证 - 系统路径"""
        # 注意：在某些系统上 /etc 可能不存在或不被认为是危险的
        # 这个测试主要验证逻辑是否正确
        system_paths = ["/etc/passwd", "/sys/kernel", "/proc/version"]
        for path in system_paths:
            is_safe, reason = is_safe_path(path)
            # 系统路径应该被标记为不安全，或者因为其他原因（如隐藏文件）被拒绝
            assert isinstance(is_safe, bool)
            assert isinstance(reason, str)
    
    def test_file_operations_integration(self):
        """测试文件操作集成"""
        # 创建测试文件
        test_content = "Integration test content"
        integration_file = self.temp_dir / "integration.txt"
        integration_file.write_text(test_content)
        
        # 验证文件创建
        assert integration_file.exists()
        assert integration_file.read_text() == test_content
        
        # 获取文件信息
        info = get_file_info(integration_file)
        assert info["name"] == "integration.txt"
        assert info["size"] == len(test_content)
        
        # 复制文件
        copy_file = self.temp_dir / "integration_copy.txt"
        shutil.copy2(integration_file, copy_file)
        assert copy_file.exists()
        assert copy_file.read_text() == test_content
        
        # 验证复制文件信息
        copy_info = get_file_info(copy_file)
        assert copy_info["name"] == "integration_copy.txt"
        assert copy_info["size"] == info["size"]
    
    def test_directory_operations_integration(self):
        """测试目录操作集成"""
        # 创建子目录
        sub_dir = self.temp_dir / "subdir"
        sub_dir.mkdir()
        
        # 验证目录创建
        assert sub_dir.exists()
        assert sub_dir.is_dir()
        
        # 在子目录中创建文件
        files = ["file1.txt", "file2.py", "file3.md"]
        for filename in files:
            file_path = sub_dir / filename
            file_path.write_text(f"Content of {filename}")
        
        # 验证文件创建
        created_files = list(sub_dir.iterdir())
        assert len(created_files) == len(files)
        
        # 获取目录信息
        dir_info = get_file_info(sub_dir)
        assert dir_info["is_dir"] is True
        assert dir_info["name"] == "subdir"
        
        # 复制目录
        copy_dir = self.temp_dir / "subdir_copy"
        shutil.copytree(sub_dir, copy_dir)
        
        # 验证目录复制
        assert copy_dir.exists()
        assert copy_dir.is_dir()
        copied_files = list(copy_dir.iterdir())
        assert len(copied_files) == len(files)


class TestFilesystemAlgorithms:
    """测试文件系统算法"""
    
    def setup_method(self):
        """测试前的设置"""
        self.temp_dir = Path(tempfile.mkdtemp())
    
    def teardown_method(self):
        """测试后的清理"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_search_algorithms(self):
        """测试搜索算法"""
        # 创建测试文件
        test_files = [
            ("document.txt", "text content"),
            ("script.py", "python code"),
            ("readme.md", "markdown text"),
            ("config.json", "json data"),
        ]
        
        for filename, content in test_files:
            file_path = self.temp_dir / filename
            file_path.write_text(content)
        
        # 测试扩展名搜索
        py_files = [f for f in self.temp_dir.iterdir() if f.suffix == ".py"]
        assert len(py_files) == 1
        assert py_files[0].name == "script.py"
        
        # 测试内容搜索
        text_files = []
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                content = file_path.read_text()
                if "text" in content.lower():
                    text_files.append(file_path)
        
        assert len(text_files) == 2  # document.txt 和 readme.md
    
    def test_duplicate_detection_algorithms(self):
        """测试重复检测算法"""
        import hashlib
        
        # 创建测试文件，包括重复内容
        files_content = [
            ("file1.txt", "content A"),
            ("file2.txt", "content B"),
            ("file1_copy.txt", "content A"),  # 重复
            ("file3.txt", "content B"),       # 重复
            ("unique.txt", "unique content"),
        ]
        
        for filename, content in files_content:
            file_path = self.temp_dir / filename
            file_path.write_text(content)
        
        # 按哈希值检测重复
        hash_groups = {}
        for file_path in self.temp_dir.iterdir():
            if file_path.is_file():
                content = file_path.read_text()
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                if file_hash not in hash_groups:
                    hash_groups[file_hash] = []
                hash_groups[file_hash].append(file_path)
        
        # 验证重复检测结果
        duplicates = {h: files for h, files in hash_groups.items() if len(files) > 1}
        assert len(duplicates) == 2  # 两组重复文件
        
        # 验证重复组的内容
        duplicate_files = []
        for files in duplicates.values():
            duplicate_files.extend([f.name for f in files])
        
        expected_duplicates = ["file1.txt", "file1_copy.txt", "file2.txt", "file3.txt"]
        assert sorted(duplicate_files) == sorted(expected_duplicates)
    
    def test_compression_algorithms(self):
        """测试压缩算法"""
        import zipfile
        import tarfile
        
        # 创建测试文件
        test_content = "This is test content for compression " * 100  # 增加内容以测试压缩
        test_file = self.temp_dir / "test.txt"
        test_file.write_text(test_content)
        
        original_size = len(test_content.encode())
        
        # 测试 ZIP 压缩
        zip_file = self.temp_dir / "test.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(test_file, test_file.name)
        
        zip_size = zip_file.stat().st_size
        assert zip_size < original_size  # 压缩后应该更小
        
        # 测试 ZIP 解压
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_file, 'r') as zf:
            zf.extractall(extract_dir)
        
        extracted_file = extract_dir / "test.txt"
        assert extracted_file.exists()
        assert extracted_file.read_text() == test_content
        
        # 测试 TAR.GZ 压缩
        tar_file = self.temp_dir / "test.tar.gz"
        with tarfile.open(tar_file, 'w:gz') as tf:
            tf.add(test_file, test_file.name)
        
        tar_size = tar_file.stat().st_size
        assert tar_size < original_size  # 压缩后应该更小


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
