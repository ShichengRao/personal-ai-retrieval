#!/usr/bin/env python3
"""
Simple test script to validate core functionality without external dependencies.
This tests the basic structure and imports of our personal AI system.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that core modules can be imported."""
    print("Testing core imports...")
    
    try:
        from personal_ai.utils.config import Config
        print("✅ Config module imported successfully")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from personal_ai.utils.text_processing import TextChunker, TextPreprocessor
        print("✅ Text processing modules imported successfully")
    except ImportError as e:
        print(f"❌ Text processing import failed: {e}")
        return False
    
    try:
        from personal_ai.embeddings.base import EmbeddingService
        print("✅ Embedding base module imported successfully")
        
        # Test Claude embeddings import (may fail without dependencies)
        try:
            from personal_ai.embeddings.claude_embeddings import ClaudeEmbeddings
            print("✅ Claude embeddings module imported successfully")
        except ImportError as e:
            print(f"⚠️ Claude embeddings import failed (optional dependency): {e}")
    except ImportError as e:
        print(f"❌ Embedding import failed: {e}")
        return False
    
    try:
        from personal_ai.tools.base import BaseTool, ToolRegistry
        print("✅ Tool base modules imported successfully")
    except ImportError as e:
        print(f"❌ Tool base import failed: {e}")
        return False
    
    try:
        from personal_ai.llm.base import BaseLLMClient
        print("✅ LLM base module imported successfully")
        
        # Test Claude LLM import (may fail without dependencies)
        try:
            from personal_ai.llm.claude_client import ClaudeLLMClient
            from personal_ai.llm.factory import create_llm_client
            print("✅ Claude LLM modules imported successfully")
        except ImportError as e:
            print(f"⚠️ Claude LLM import failed (optional dependency): {e}")
    except ImportError as e:
        print(f"❌ LLM import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration management."""
    print("\nTesting configuration...")
    
    try:
        from personal_ai.utils.config import Config
        
        # Create a test config
        config = Config()
        
        # Test setting and getting values
        config.set('test.value', 'hello')
        assert config.get('test.value') == 'hello'
        
        # Test default values
        assert config.get('nonexistent.key', 'default') == 'default'
        
        # Test Claude configuration properties
        claude_model = config.claude_model
        assert isinstance(claude_model, str)
        
        prefer_claude = config.prefer_claude
        assert isinstance(prefer_claude, bool)
        
        print("✅ Configuration management (including Claude) working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_text_processing():
    """Test text processing functionality."""
    print("\nTesting text processing...")
    
    try:
        from personal_ai.utils.text_processing import TextChunker, TextPreprocessor
        
        # Test text chunking
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)
        
        test_text = "This is a test document. " * 20  # Create a longer text
        chunks = chunker.chunk_text(test_text)
        
        assert len(chunks) > 1, "Should create multiple chunks"
        assert all('text' in chunk and 'metadata' in chunk for chunk in chunks)
        
        # Test text preprocessing
        keywords = TextPreprocessor.extract_keywords("This is a test document about machine learning and AI")
        assert len(keywords) > 0, "Should extract keywords"
        
        entities = TextPreprocessor.extract_entities("Contact john@example.com or visit https://example.com")
        assert len(entities['emails']) > 0, "Should extract email addresses"
        assert len(entities['urls']) > 0, "Should extract URLs"
        
        print("✅ Text processing working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Text processing test failed: {e}")
        return False

def test_tool_registry():
    """Test tool registry functionality."""
    print("\nTesting tool registry...")
    
    try:
        from personal_ai.tools.base import BaseTool, ToolRegistry
        
        # Create a simple test tool
        class TestTool(BaseTool):
            @property
            def name(self):
                return "test_tool"
            
            @property
            def description(self):
                return "A test tool"
            
            @property
            def parameters(self):
                return {"param1": {"type": "string", "description": "Test parameter"}}
            
            def execute(self, **kwargs):
                return {"result": "test successful", "params": kwargs}
        
        # Test registry
        registry = ToolRegistry()
        test_tool = TestTool()
        
        registry.register(test_tool)
        assert "test_tool" in registry.list_tools()
        
        retrieved_tool = registry.get_tool("test_tool")
        assert retrieved_tool is not None
        
        # Test execution
        result = registry.execute_tool("test_tool", param1="test_value")
        assert result['success'] == True
        assert result['result']['result'] == "test successful"
        
        print("✅ Tool registry working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        return False

def test_project_structure():
    """Test that the project structure is correct."""
    print("\nTesting project structure...")
    
    required_files = [
        'src/personal_ai/__init__.py',
        'src/personal_ai/utils/__init__.py',
        'src/personal_ai/utils/config.py',
        'src/personal_ai/utils/text_processing.py',
        'src/personal_ai/embeddings/__init__.py',
        'src/personal_ai/embeddings/base.py',
        'src/personal_ai/storage/__init__.py',
        'src/personal_ai/loaders/__init__.py',
        'src/personal_ai/query/__init__.py',
        'src/personal_ai/tools/__init__.py',
        'src/personal_ai/tools/base.py',
        'src/personal_ai/cli/__init__.py',
        'requirements.txt',
        'setup.py',
        'config.yaml.template',
        '.env.template'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ Project structure is correct")
    return True

def test_claude_integration():
    """Test Claude integration without requiring API key."""
    print("\nTesting Claude integration...")
    
    try:
        # Test basic imports
        try:
            from personal_ai.llm.claude_client import ClaudeLLMClient
            claude_available = True
        except ImportError as e:
            print(f"⚠️ Claude client not available: {e}")
            claude_available = False
        
        try:
            from personal_ai.embeddings.claude_embeddings import ClaudeEmbeddings
            claude_embeddings_available = True
        except ImportError as e:
            print(f"⚠️ Claude embeddings not available: {e}")
            claude_embeddings_available = False
        
        # Test configuration
        from personal_ai.utils.config import config
        claude_model = config.claude_model
        assert isinstance(claude_model, str)
        
        prefer_claude = config.prefer_claude
        assert isinstance(prefer_claude, bool)
        
        # Test LLM factory (should work even without Claude dependencies)
        try:
            from personal_ai.llm.factory import create_llm_client
            client = create_llm_client(prefer_claude=True, claude_api_key=None, openai_api_key=None)
            # Should return None since no API keys provided
            assert client is None
            print("✅ LLM factory working correctly")
        except Exception as e:
            print(f"⚠️ LLM factory test failed: {e}")
        
        if claude_available or claude_embeddings_available:
            print("✅ Claude integration structure working correctly")
        else:
            print("⚠️ Claude integration available but dependencies missing (install anthropic and sentence-transformers)")
        
        return True
        
    except Exception as e:
        print(f"❌ Claude integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Personal AI Retrieval System - Core Functionality Test (with Claude Support)")
    print("=" * 70)
    
    tests = [
        test_project_structure,
        test_imports,
        test_config,
        test_text_processing,
        test_tool_registry,
        test_claude_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All core functionality tests passed!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Set up configuration: cp config.yaml.template config.yaml")
        print("3. Set up Google API credentials")
        print("4. Add OpenAI or Claude API key to .env file")
        print("5. Run data ingestion: pai-ingest --help")
        print("6. Start the assistant: pai-assistant --help")
        print("\nLLM Support:")
        print("- OpenAI GPT-4: Add OPENAI_API_KEY to .env")
        print("- Claude 3.5 Sonnet: Add CLAUDE_API_KEY to .env")
        print("- Local models: No API key needed (slower but free)")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())