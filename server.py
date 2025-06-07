#!/usr/bin/env python3
"""
Claude Thread Continuity MCP Server

Automatically saves and restores project context when Claude threads hit token limits.
Built for seamless conversation continuity across thread boundaries.

Features:
- Automatic state persistence during conversations
- Seamless context restoration for new threads
- Local JSON storage for privacy
- Smart auto-save triggers
- Multi-project support

Usage:
- save_project_state: Save current project context
- load_project_state: Restore full project context  
- list_active_projects: View all tracked projects
- get_project_summary: Quick project overview

Author: Built for the Claude community
License: MIT
"""
import sys
import os
import time
import asyncio
import logging
import traceback
import argparse
import json
import platform
from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from mcp.types import Resource, Prompt

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'ERROR').upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.ERROR),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

class ProjectState:
    """Manages project state persistence and retrieval."""
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.claude_states"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def get_project_dir(self, project_name: str) -> Path:
        """Get the directory for a specific project."""
        project_dir = self.base_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir
    
    def save_state(self, project_name: str, state_data: Dict[str, Any]) -> bool:
        """Save project state to JSON file."""
        try:
            project_dir = self.get_project_dir(project_name)
            state_file = project_dir / "current_state.json"
            
            # Add metadata
            state_data.update({
                "project_name": project_name,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            })
            
            # Write atomically
            temp_file = state_file.with_suffix(".tmp")
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            temp_file.rename(state_file)
            
            # Create backup
            backup_file = project_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
            
            # Keep only last 5 backups
            self._cleanup_backups(project_dir)
            return True
            
        except Exception as e:
            print(f"Error saving state: {e}", file=sys.stderr)
            return False
    
    def load_state(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Load project state from JSON file."""
        try:
            project_dir = self.get_project_dir(project_name)
            state_file = project_dir / "current_state.json"
            
            if not state_file.exists():
                return None
                
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading state: {e}", file=sys.stderr)
            return None
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all available projects with basic info."""
        projects = []
        
        if not self.base_dir.exists():
            return projects
            
        for project_dir in self.base_dir.iterdir():
            if project_dir.is_dir():
                state_file = project_dir / "current_state.json"
                if state_file.exists():
                    try:
                        with open(state_file, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                            
                        projects.append({
                            "name": project_dir.name,
                            "last_updated": state.get("last_updated", "Unknown"),
                            "current_focus": state.get("current_focus", "No focus set"),
                            "next_actions": state.get("next_actions", [])[:2]
                        })
                    except Exception:
                        continue
        
        # Sort by last updated (most recent first)
        projects.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return projects
    
    def get_project_summary(self, project_name: str) -> Optional[str]:
        """Get a concise summary of project state."""
        state = self.load_state(project_name)
        if not state:
            return None
            
        summary_parts = []
        
        if state.get("current_focus"):
            summary_parts.append(f"Focus: {state['current_focus']}")
            
        if state.get("technical_decisions"):
            decisions = state["technical_decisions"]
            if decisions:
                summary_parts.append(f"Recent decisions: {', '.join(decisions[-2:])}")
        
        if state.get("next_actions"):
            actions = state["next_actions"]
            if actions:
                summary_parts.append(f"Next: {', '.join(actions[:2])}")
        
        return " | ".join(summary_parts) if summary_parts else "No summary available"
    
    def auto_save_checkpoint(self, project_name: str, trigger_type: str, context: str = "") -> bool:
        """Auto-save with trigger context."""
        current_state = self.load_state(project_name) or {}
        current_state.update({
            "auto_save_trigger": trigger_type,
            "auto_save_context": context,
            "checkpoint_time": datetime.now().isoformat()
        })
        return self.save_state(project_name, current_state)
    
    def _cleanup_backups(self, project_dir: Path, keep_count: int = 5):
        """Keep only the most recent backup files."""
        backup_files = sorted(
            [f for f in project_dir.glob("backup_*.json")],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for backup in backup_files[keep_count:]:
            try:
                backup.unlink()
            except Exception:
                pass

class ContinuityServer:
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("claude-continuity")
        
        # Initialize query time tracking
        self.query_times = deque(maxlen=50)
        
        try:
            # Initialize project state storage
            logger.info("Initializing project state storage...")
            print("Initializing project state storage", file=sys.stderr, flush=True)
            self.storage = ProjectState()
            self._storage_initialized = True

        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            logger.error(traceback.format_exc())
            self.storage = None
            self._storage_initialized = False
        
        # Register handlers
        self.register_handlers()
        logger.info("Server initialization complete")
        
        # Test handler registration
        try:
            logger.info("Testing handler registration...")
            capabilities = self.server.get_capabilities(
                notification_options=NotificationOptions(),
                experimental_capabilities={}
            )
            logger.info(f"Server capabilities: {capabilities}")
            print(f"Server capabilities registered successfully!", file=sys.stderr, flush=True)
        except Exception as e:
            logger.error(f"Handler registration test failed: {str(e)}")
            print(f"Handler registration issue: {str(e)}", file=sys.stderr, flush=True)
    
    def record_query_time(self, query_time_ms: float):
        """Record a query time for averaging."""
        self.query_times.append(query_time_ms)
        logger.debug(f"Recorded query time: {query_time_ms:.2f}ms")
    
    def get_average_query_time(self) -> float:
        """Get the average query time from recent operations."""
        if not self.query_times:
            return 0.0
        
        avg = sum(self.query_times) / len(self.query_times)
        logger.debug(f"Average query time: {avg:.2f}ms (from {len(self.query_times)} samples)")
        return round(avg, 2)
    
    async def _ensure_storage_initialized(self):
        """Ensure storage is initialized."""
        if not self._storage_initialized:
            try:
                logger.info("Initializing project state storage...")
                self.storage = ProjectState()
                self._storage_initialized = True
                logger.info("Project state storage initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize storage: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        return self.storage

    async def initialize(self):
        """Async initialization method."""
        try:
            logger.info("Starting async initialization...")
            
            print("\n=== Claude Thread Continuity System ===", file=sys.stderr, flush=True)
            print(f"Python: {platform.python_version()}", file=sys.stderr, flush=True)
            print(f"Storage: Local JSON files", file=sys.stderr, flush=True)
            print("MCP Thread Continuity initialization completed", file=sys.stderr, flush=True)
            
            return True
        except Exception as e:
            logger.error(f"Async initialization error: {str(e)}")
            logger.error(traceback.format_exc())
            print(f"Initialization error: {str(e)}", file=sys.stderr, flush=True)
            return False

    def handle_method_not_found(self, method: str) -> None:
        """Custom handler for unsupported methods."""
        logger.warning(f"Unsupported method requested: {method}")
    
    def register_handlers(self):
        # Resource handlers
        @self.server.list_resources()
        async def handle_list_resources() -> List[Resource]:
            return []
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> List[types.TextContent]:
            logger.warning(f"Resource read request received for URI: {uri}, but no resources are available")
            return [types.TextContent(
                type="text",
                text=f"Error: Resource not found: {uri}"
            )]
        
        @self.server.list_resource_templates()
        async def handle_list_resource_templates() -> List[types.ResourceTemplate]:
            return []
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[types.Prompt]:
            logger.debug("Handling prompts/list request")
            return []
        
        self.server.on_method_not_found = self.handle_method_not_found
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            logger.info("=== HANDLING LIST_TOOLS REQUEST ===")
            try:
                tools = [
                    types.Tool(
                        name="save_project_state",
                        description="Save current project state for thread continuity",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_name": {
                                    "type": "string",
                                    "description": "Name of the project to save state for"
                                },
                                "current_focus": {
                                    "type": "string", 
                                    "description": "Current main objective or focus area"
                                },
                                "technical_decisions": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Key technical decisions made"
                                },
                                "files_modified": {
                                    "type": "array", 
                                    "items": {"type": "string"},
                                    "description": "Files created or modified"
                                },
                                "next_actions": {
                                    "type": "array",
                                    "items": {"type": "string"}, 
                                    "description": "Planned next steps"
                                },
                                "conversation_summary": {
                                    "type": "string",
                                    "description": "Brief summary of conversation context"
                                }
                            },
                            "required": ["project_name"]
                        }
                    ),
                    types.Tool(
                        name="load_project_state", 
                        description="Load saved project state to restore context",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_name": {
                                    "type": "string",
                                    "description": "Name of the project to load"
                                }
                            },
                            "required": ["project_name"]
                        }
                    ),
                    types.Tool(
                        name="list_active_projects",
                        description="List all projects with saved states",
                        inputSchema={
                            "type": "object", 
                            "properties": {}
                        }
                    ),
                    types.Tool(
                        name="get_project_summary",
                        description="Get concise summary of a project's current state", 
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_name": {
                                    "type": "string",
                                    "description": "Name of the project"
                                }
                            },
                            "required": ["project_name"]
                        }
                    ),
                    types.Tool(
                        name="auto_save_checkpoint",
                        description="Automatic checkpoint save during conversation",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "project_name": {
                                    "type": "string", 
                                    "description": "Project name"
                                },
                                "trigger_type": {
                                    "type": "string",
                                    "description": "What triggered the save (file_change, decision, milestone, message_count)"
                                },
                                "context": {
                                    "type": "string",
                                    "description": "Brief context about the trigger"
                                }
                            },
                            "required": ["project_name", "trigger_type"]
                        }
                    )
                ]
                logger.info(f"Returning {len(tools)} tools")
                return tools
            except Exception as e:
                logger.error(f"Error in handle_list_tools: {str(e)}")
                logger.error(traceback.format_exc())
                raise
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> List[types.TextContent]:
            print(f"TOOL CALL INTERCEPTED: {name}", file=sys.stderr, flush=True)
            logger.info(f"=== HANDLING TOOL CALL: {name} ===")
            logger.info(f"Arguments: {arguments}")
            
            try:
                if arguments is None:
                    arguments = {}
                
                logger.info(f"Processing tool: {name}")
                print(f"Processing tool: {name}", file=sys.stderr, flush=True)
                
                if name == "save_project_state":
                    return await self.handle_save_project_state(arguments)
                elif name == "load_project_state":
                    return await self.handle_load_project_state(arguments)
                elif name == "list_active_projects":
                    return await self.handle_list_active_projects(arguments)
                elif name == "get_project_summary":
                    return await self.handle_get_project_summary(arguments)
                elif name == "auto_save_checkpoint":
                    return await self.handle_auto_save_checkpoint(arguments)
                else:
                    logger.warning(f"Unknown tool requested: {name}")
                    print(f"Unknown tool requested: {name}", file=sys.stderr, flush=True)
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                error_msg = f"Error in {name}: {str(e)}\n{traceback.format_exc()}"
                logger.error(error_msg)
                print(f"ERROR in tool execution: {error_msg}", file=sys.stderr, flush=True)
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]

    # TOOL HANDLERS
    async def handle_save_project_state(self, arguments: dict) -> List[types.TextContent]:
        project_name = arguments.get("project_name")
        
        if not project_name:
            return [types.TextContent(type="text", text="Error: Project name is required")]
        
        try:
            storage = await self._ensure_storage_initialized()
            success = storage.save_state(project_name, arguments)
            
            if success:
                message = f"✅ Project state saved for '{project_name}'"
            else:
                message = f"❌ Failed to save state for '{project_name}'"
                
            return [types.TextContent(type="text", text=message)]
        except Exception as e:
            logger.error(f"Error saving project state: {str(e)}\n{traceback.format_exc()}")
            return [types.TextContent(type="text", text=f"Error saving project state: {str(e)}")]
    
    async def handle_load_project_state(self, arguments: dict) -> List[types.TextContent]:
        project_name = arguments.get("project_name")
        
        if not project_name:
            return [types.TextContent(type="text", text="Error: Project name is required")]
        
        try:
            storage = await self._ensure_storage_initialized()
            state = storage.load_state(project_name)
            
            if state:
                # Format the loaded state nicely
                output = f"📂 **Project: {project_name}**\n\n"
                output += f"🎯 **Current Focus:** {state.get('current_focus', 'Not set')}\n\n"
                
                if state.get('technical_decisions'):
                    output += "🔧 **Technical Decisions:**\n"
                    for decision in state['technical_decisions']:
                        output += f"  • {decision}\n"
                    output += "\n"
                
                if state.get('files_modified'):
                    output += "📁 **Files Modified:**\n"
                    for file in state['files_modified']:
                        output += f"  • {file}\n"
                    output += "\n"
                
                if state.get('next_actions'):
                    output += "✅ **Next Actions:**\n"
                    for action in state['next_actions']:
                        output += f"  • {action}\n"
                    output += "\n"
                
                if state.get('conversation_summary'):
                    output += f"💬 **Context:** {state['conversation_summary']}\n\n"
                
                output += f"🕒 **Last Updated:** {state.get('last_updated', 'Unknown')}"
                
                return [types.TextContent(type="text", text=output)]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ No saved state found for project '{project_name}'"
                )]
        except Exception as e:
            logger.error(f"Error loading project state: {str(e)}\n{traceback.format_exc()}")
            return [types.TextContent(type="text", text=f"Error loading project state: {str(e)}")]
    
    async def handle_list_active_projects(self, arguments: dict) -> List[types.TextContent]:
        try:
            storage = await self._ensure_storage_initialized()
            projects = storage.list_projects()
            
            if not projects:
                return [types.TextContent(
                    type="text",
                    text="No active projects found. Start working on a project and save state to see it here."
                )]
            
            output = "📋 **Active Projects:**\n\n"
            
            for i, project in enumerate(projects, 1):
                output += f"**{i}. {project['name']}**\n"
                output += f"   Focus: {project['current_focus']}\n"
                
                if project['next_actions']:
                    actions_preview = ', '.join(project['next_actions'])
                    output += f"   Next: {actions_preview}\n"
                
                output += f"   Updated: {project['last_updated']}\n\n"
            
            output += "💡 Use `load_project_state` with any project name to restore full context."
            
            return [types.TextContent(type="text", text=output)]
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}\n{traceback.format_exc()}")
            return [types.TextContent(type="text", text=f"Error listing projects: {str(e)}")]
    
    async def handle_get_project_summary(self, arguments: dict) -> List[types.TextContent]:
        project_name = arguments.get("project_name")
        
        if not project_name:
            return [types.TextContent(type="text", text="Error: Project name is required")]
        
        try:
            storage = await self._ensure_storage_initialized()
            summary = storage.get_project_summary(project_name)
            
            if summary:
                return [types.TextContent(
                    type="text",
                    text=f"📊 **{project_name}:** {summary}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ No summary available for '{project_name}'"
                )]
        except Exception as e:
            logger.error(f"Error getting project summary: {str(e)}\n{traceback.format_exc()}")
            return [types.TextContent(type="text", text=f"Error getting project summary: {str(e)}")]
    
    async def handle_auto_save_checkpoint(self, arguments: dict) -> List[types.TextContent]:
        project_name = arguments.get("project_name")
        trigger_type = arguments.get("trigger_type")
        context = arguments.get("context", "")
        
        if not project_name or not trigger_type:
            return [types.TextContent(type="text", text="Error: Project name and trigger type are required")]
        
        try:
            storage = await self._ensure_storage_initialized()
            success = storage.auto_save_checkpoint(project_name, trigger_type, context)
            
            if success:
                return [types.TextContent(
                    type="text",
                    text=f"💾 Auto-saved checkpoint for '{project_name}' (trigger: {trigger_type})"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"❌ Auto-save failed for '{project_name}'"
                )]
        except Exception as e:
            logger.error(f"Error auto-saving checkpoint: {str(e)}\n{traceback.format_exc()}")
            return [types.TextContent(type="text", text=f"Error auto-saving checkpoint: {str(e)}")]


async def async_main():
    """Main async function."""
    
    # Print system diagnostics
    print("\n=== Claude Thread Continuity MCP Server ===", file=sys.stderr, flush=True)
    print(f"Python: {platform.python_version()}", file=sys.stderr, flush=True)
    print(f"Storage: ~/.claude_states/", file=sys.stderr, flush=True)
    print("================================================\n", file=sys.stderr, flush=True)
    
    logger.info("Starting Claude Thread Continuity MCP Server")
    
    try:
        # Create server instance
        continuity_server = ContinuityServer()
        
        # Async initialization with timeout and retry
        max_retries = 2
        retry_count = 0
        init_success = False
        
        while retry_count <= max_retries and not init_success:
            if retry_count > 0:
                logger.warning(f"Retrying initialization (attempt {retry_count}/{max_retries})...")
                
            init_task = asyncio.create_task(continuity_server.initialize())
            try:
                init_success = await asyncio.wait_for(init_task, timeout=30.0)
                if init_success:
                    logger.info("Async initialization completed successfully")
                else:
                    logger.warning("Initialization returned failure status")
                    retry_count += 1
            except asyncio.TimeoutError:
                logger.warning("Async initialization timed out. Continuing with server startup.")
                break
            except Exception as init_error:
                logger.error(f"Initialization error: {str(init_error)}")
                logger.error(traceback.format_exc())
                retry_count += 1
                
                if retry_count <= max_retries:
                    logger.info(f"Waiting 2 seconds before retry...")
                    await asyncio.sleep(2)
        
        # Start the server
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            logger.info("Server started and ready to handle requests")
            await continuity_server.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="claude-continuity",
                    server_version="1.0.0",
                    protocol_version="2024-11-05",
                    capabilities=continuity_server.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Fatal server error: {str(e)}", file=sys.stderr, flush=True)
        raise

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
