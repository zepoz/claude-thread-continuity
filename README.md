# 🧠 Claude Thread Continuity MCP Server

**Never lose context again!** This MCP server automatically saves and restores project state when Claude threads hit token limits, ensuring seamless conversation continuity.

## 🚀 Features

- **🔄 Automatic State Persistence** - Auto-saves project context during conversations
- **⚡ Seamless Restoration** - Instantly restore full context when starting new threads
- **🔒 Privacy First** - All data stored locally on your machine
- **🎯 Zero Configuration** - Works invisibly once set up
- **📊 Smart Triggers** - Auto-saves on file changes, decisions, milestones
- **🗂️ Multi-Project Support** - Manage multiple concurrent projects

## ⚡ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/peless/claude-thread-continuity.git
cd claude-thread-continuity

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add to Claude Desktop config
# See setup instructions below
```

## 🛠️ Installation

### 1. Install the MCP Server

```bash
# Create permanent directory
mkdir -p ~/.mcp-servers/claude-continuity
cd ~/.mcp-servers/claude-continuity

# Copy files (or clone repo to this location)
# Place server.py and requirements.txt here
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "claude-continuity": {
      "command": "python3",
      "args": ["~/.mcp-servers/claude-continuity/server.py"],
      "env": {}
    }
  }
}
```

### 3. Restart Claude Desktop

Close and reopen Claude Desktop. The continuity tools will now be available automatically.

## 🎯 How It Works

### Automatic Context Saving

The server automatically saves project state when:
- ✅ Files are created or modified
- ✅ Technical decisions are made  
- ✅ Project milestones are reached
- ✅ Every 10 messages (fallback)

### Context Restoration

When starting a new thread:
1. **Load Project:** `load_project_state: project_name="your-project"`
2. **Full Context Restored:** All technical decisions, files, and progress restored
3. **Continue Seamlessly:** Pick up exactly where you left off

## 🔧 Available Commands

| Command | Description |
|---------|-------------|
| `save_project_state` | Manually save current project state |
| `load_project_state` | Restore full project context |
| `list_active_projects` | View all tracked projects |
| `get_project_summary` | Get quick project overview |
| `auto_save_checkpoint` | Triggered automatically during conversations |

## 💡 Usage Examples

### Starting a New Project
```
save_project_state: project_name="my-web-app", current_focus="Setting up React components", technical_decisions=["Using TypeScript", "Vite for bundling"], next_actions=["Create header component", "Set up routing"]
```

### Continuing After Token Limit
```
load_project_state: project_name="my-web-app"
```

### Viewing All Projects
```
list_active_projects
```

## 🗂️ Data Storage

Project states are stored locally at:
```
~/.claude_states/
├── project-name-1/
│   ├── current_state.json
│   └── backup_*.json
└── project-name-2/
    ├── current_state.json
    └── backup_*.json
```

- **Privacy:** Everything stays on your machine
- **Backups:** Automatic backup rotation (keeps last 5)
- **Format:** Human-readable JSON files

## 🏗️ Project State Structure

Each saved state includes:

```json
{
  "project_name": "my-project",
  "current_focus": "What you're working on now",
  "technical_decisions": ["Key choices made"],
  "files_modified": ["List of files created/changed"],
  "next_actions": ["Planned next steps"],
  "conversation_summary": "Brief context summary",
  "last_updated": "2025-06-07T10:30:00Z"
}
```

## 🔍 Troubleshooting

### Tools Not Appearing
1. Check Claude Desktop logs
2. Verify Python 3 is in your PATH: `python3 --version`
3. Validate JSON config syntax
4. Restart Claude Desktop completely

### Testing the Server
```bash
cd ~/.mcp-servers/claude-continuity
python3 server.py
# Should show initialization messages
```

### Common Issues

**Permission Errors:**
```bash
chmod +x ~/.mcp-servers/claude-continuity/server.py
```

**Python Path Issues:**
Update the config to use full Python path:
```json
{
  "command": "/usr/bin/python3",
  "args": ["~/.mcp-servers/claude-continuity/server.py"]
}
```

## 🧪 Development

### Requirements
- Python 3.8+
- MCP SDK 1.0+

### Running Tests
```bash
python3 test_server.py
```

### Project Structure
```
claude-thread-continuity/
├── server.py           # Main MCP server
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── LICENSE            # MIT License
└── examples/          # Usage examples
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🚀 Why This Matters

**Before:** 😫 Hit token limit → Lose all context → Re-explain everything → Lose momentum

**After:** 😎 Hit token limit → Start new thread → `load_project_state` → Continue seamlessly

Perfect for:
- 🏗️ **Complex Development Projects** - Keep track of architecture decisions
- 📚 **Learning & Research** - Maintain context across study sessions  
- ✍️ **Writing Projects** - Remember plot points and character development
- 🔧 **Multi-session Debugging** - Preserve debugging state and findings

---

**Built with ❤️ for the Claude community**

*Tired of losing context? This MCP server has your back!*
