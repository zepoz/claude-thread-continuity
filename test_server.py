#!/usr/bin/env python3
"""
Test script for Claude Thread Continuity MCP Server

This script tests the basic functionality of the server to ensure it's working correctly.
Run this before setting up the server with Claude Desktop.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the current directory to Python path so we can import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from server import ProjectState, ContinuityServer
    print("✅ Successfully imported server modules")
except ImportError as e:
    print(f"❌ Failed to import server modules: {e}")
    print("Make sure you're running this from the directory containing server.py")
    sys.exit(1)

def test_project_state():
    """Test the ProjectState class functionality."""
    print("\n🧪 Testing ProjectState class...")
    
    # Use a temporary directory for testing
    test_dir = Path("/tmp/claude_continuity_test")
    storage = ProjectState(str(test_dir))
    
    # Test data
    test_project = "test-project"
    test_data = {
        "current_focus": "Testing the continuity system",
        "technical_decisions": ["Using Python for MCP server", "JSON for data storage"],
        "files_modified": ["server.py", "test_server.py"],
        "next_actions": ["Run integration tests", "Deploy to production"],
        "conversation_summary": "Building and testing Claude Thread Continuity MCP server"
    }
    
    try:
        # Test saving
        print("  📝 Testing save_state...")
        success = storage.save_state(test_project, test_data)
        if success:
            print("  ✅ save_state successful")
        else:
            print("  ❌ save_state failed")
            return False
        
        # Test loading
        print("  📖 Testing load_state...")
        loaded_data = storage.load_state(test_project)
        if loaded_data:
            print("  ✅ load_state successful")
            # Verify data integrity
            if loaded_data.get("current_focus") == test_data["current_focus"]:
                print("  ✅ Data integrity verified")
            else:
                print("  ❌ Data integrity check failed")
                return False
        else:
            print("  ❌ load_state returned None")
            return False
        
        # Test listing projects
        print("  📋 Testing list_projects...")
        projects = storage.list_projects()
        if projects and any(p["name"] == test_project for p in projects):
            print("  ✅ list_projects successful")
        else:
            print("  ❌ list_projects failed or project not found")
            return False
        
        # Test project summary
        print("  📊 Testing get_project_summary...")
        summary = storage.get_project_summary(test_project)
        if summary and "Testing the continuity system" in summary:
            print("  ✅ get_project_summary successful")
        else:
            print("  ❌ get_project_summary failed")
            return False
        
        # Test auto-save checkpoint
        print("  💾 Testing auto_save_checkpoint...")
        checkpoint_success = storage.auto_save_checkpoint(test_project, "test_trigger", "Testing checkpoint functionality")
        if checkpoint_success:
            print("  ✅ auto_save_checkpoint successful")
        else:
            print("  ❌ auto_save_checkpoint failed")
            return False
        
        # Cleanup
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("  🧹 Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error during testing: {e}")
        return False

async def test_server_initialization():
    """Test basic server initialization."""
    print("\n🧪 Testing ContinuityServer initialization...")
    
    try:
        server = ContinuityServer()
        print("  ✅ Server instance created successfully")
        
        # Test async initialization
        init_result = await server.initialize()
        if init_result:
            print("  ✅ Async initialization successful")
        else:
            print("  ⚠️  Async initialization returned False (may still work)")
        
        # Test storage initialization
        storage = await server._ensure_storage_initialized()
        if storage:
            print("  ✅ Storage initialization successful")
        else:
            print("  ❌ Storage initialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error during server testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test that all required dependencies are available."""
    print("\n🧪 Testing dependencies...")
    
    dependencies = [
        ("mcp", "MCP SDK"),
        ("mcp.server", "MCP Server"),
        ("mcp.types", "MCP Types"),
        ("json", "JSON (built-in)"),
        ("pathlib", "Pathlib (built-in)"),
        ("asyncio", "Asyncio (built-in)")
    ]
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {description}")
        except ImportError:
            print(f"  ❌ {description} - MISSING!")
            print(f"     Try: pip install {module_name}")
            return False
    
    return True

def main():
    """Run all tests."""
    print("🚀 Claude Thread Continuity MCP Server Test Suite")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test dependencies
    if not test_dependencies():
        all_tests_passed = False
        print("\n❌ Dependency tests failed. Please install missing dependencies.")
    
    # Test ProjectState functionality
    if not test_project_state():
        all_tests_passed = False
        print("\n❌ ProjectState tests failed.")
    
    # Test server initialization
    try:
        if not asyncio.run(test_server_initialization()):
            all_tests_passed = False
            print("\n❌ Server initialization tests failed.")
    except Exception as e:
        print(f"\n❌ Server initialization test crashed: {e}")
        all_tests_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All tests passed! The server is ready to use.")
        print("\nNext steps:")
        print("1. Add the server to your Claude Desktop config")
        print("2. Restart Claude Desktop")
        print("3. Start using the continuity tools!")
    else:
        print("❌ Some tests failed. Please fix the issues above before using the server.")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    sys.exit(main())
