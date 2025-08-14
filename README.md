# 🧠 Claude Thread Continuity MCP Server (Enhanced Fork)

**Never lose context again!** This MCP server automatically saves and restores project state when Claude threads hit token limits, ensuring seamless conversation continuity.

> **🙏 Huge thanks to [peless](https://github.com/peless/claude-thread-continuity) for creating the original Claude Thread Continuity server!** This fork adds conversation state accumulation capabilities through some casual vibe coding. Instead of overwirting the state overy time you save. I'm definitely not a programmer. Maybe its also possible with the original and im too dumb to get it lmao honestly.

## Have some Clanker explain the rest...

## New Features (This Fork) (Why is there no fork emoji but only a spoon or fork+knife?)

### New:  Conversation State Accumulation
Accumulates context across multiple threads instead of overwriting.

**Original behavior:**
- Each `save_project_state` completely overwrote previous data
- Lost conversation history when switching threads

**Enhanced behavior:**
- **`append_lists` mode** - Intelligently appends to arrays while updating scalar fields
- **`merge` mode** - Updates specific fields while preserving others  
- **`replace` mode** - Original overwrite behavior (still default)
- **Conversation accumulation** - Build up technical decisions, file lists, and context over time

### 🔄 Smart Merge Strategies

| Mode | Behavior | Best For |
|------|----------|----------|
| `append_lists` | Adds new items to existing arrays, updates other fields | Multi-session development projects |
| `merge` | Updates specific fields while preserving others | Focused updates to project aspects |
| `replace` | Complete overwrite (original behavior) | Starting fresh or major pivots |

---

## 🌟 All Original Features Included

- **🔄 Automatic State Persistence** - Auto-saves project context during conversations
- **⚡ Seamless Restoration** - Instantly restore full context when starting new threads
- **🛡️ Smart Validation** - Prevents project fragmentation with intelligent name checking
- **🔒 Privacy First** - All data stored locally on your machine
- **🎯 Zero Configuration** - Works invisibly once set up
- **📊 Smart Triggers** - Auto-saves on file changes, decisions, milestones
- **🗂️ Multi-Project Support** - Manage multiple concurrent projects

## ⚡ Quick Start

```bash
# 1. Clone this enhanced fork
git clone https://github.com/[your-username]/claude-thread-continuity-enhanced.git
cd claude-thread-continuity-enhanced

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test the enhanced server
python3 test_server.py

# 4. Add to Claude Desktop config
# See setup instructions below
```

## 🛠️ Installation

### 1. Install the MCP Server

```bash
# Create permanent directory
mkdir -p ~/.mcp-servers/claude-continuity
cd ~/.mcp-servers/claude-continuity

# Copy files from this fork
# Place server.py and requirements.txt here
```

### 2. Configure Claude Desktop

Edit your Claude Desktop configuration file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\\Claude\\claude_desktop_config.json`
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

Close and reopen Claude Desktop. The enhanced continuity tools will now be available automatically.

## 🎯 How the Enhanced Version Works

### NEW: Accumulative State Saving

The enhanced server now supports three merge strategies:

```bash
# Append mode - builds up lists over time (RECOMMENDED for multi-session projects)
save_project_state: project_name="my-app", technical_decisions=["Added Redis caching"], files_modified=["cache.py"], merge_mode="append_lists"

# Merge mode - updates specific fields
save_project_state: project_name="my-app", current_focus="Database optimization", merge_mode="merge"  

# Replace mode - original behavior (complete overwrite)
save_project_state: project_name="my-app", current_focus="Starting fresh", merge_mode="replace"
```

### Example: Building Context Over Time

**Session 1:**
```bash
save_project_state: project_name="react-dashboard", 
  current_focus="Setting up project structure",
  technical_decisions=["Using Vite", "TypeScript setup"],
  files_modified=["package.json", "vite.config.ts"],
  merge_mode="append_lists"
```

**Session 2 (different thread):**
```bash
# Load previous context
load_project_state: project_name="react-dashboard"

# Add more without losing previous decisions
save_project_state: project_name="react-dashboard",
  technical_decisions=["Added Zustand for state management"],
  files_modified=["src/store.ts"],
  merge_mode="append_lists"
```

**Result:** Your project now has accumulated:
- `technical_decisions`: `["Using Vite", "TypeScript setup", "Added Zustand for state management"]`
- `files_modified`: `["package.json", "vite.config.ts", "src/store.ts"]`

### Smart Validation Process (Original Feature)

Before saving, the system:
1. **Checks for Similar Names** - Uses fuzzy matching to find existing projects
2. **Calculates Similarity** - Compares project names with 70% threshold
3. **Provides Recommendations** - Suggests consolidation or renaming
4. **Allows Override** - Use `force: true` for edge cases

## 🔧 Enhanced Commands

| Command | Description | Enhancement in Fork |
|---------|-------------|---------------------|
| `save_project_state` | Save current project state | ✨ **Now supports `merge_mode` parameter** |
| `load_project_state` | Restore full project context | Same as original |
| `list_active_projects` | View all tracked projects | Same as original |
| `get_project_summary` | Get quick project overview | Same as original |
| `validate_project_name` | Check for similar project names | Same as original |
| `auto_save_checkpoint` | Triggered automatically | Same as original |

## 💡 Enhanced Usage Examples

### Multi-Session Development Project
```bash
# Day 1: Initial setup
save_project_state: project_name="e-commerce-api",
  current_focus="Setting up Express server",
  technical_decisions=["Node.js with Express", "MongoDB database"],
  files_modified=["server.js", "package.json"],
  merge_mode="append_lists"

# Day 2: Adding authentication (new thread)
load_project_state: project_name="e-commerce-api"

save_project_state: project_name="e-commerce-api",
  current_focus="Implementing JWT authentication", 
  technical_decisions=["JWT for auth tokens", "bcrypt for password hashing"],
  files_modified=["auth/middleware.js", "models/User.js"],
  merge_mode="append_lists"

# Day 3: Product management (another new thread)
load_project_state: project_name="e-commerce-api"

save_project_state: project_name="e-commerce-api",
  current_focus="Building product CRUD operations",
  technical_decisions=["Mongoose for ODM", "Input validation with Joi"],
  files_modified=["routes/products.js", "models/Product.js"],
  merge_mode="append_lists"
```

**Result:** Your project now has a complete history of all decisions and files across all sessions!

### Focused Updates
```bash
# Just update the current focus without touching other fields
save_project_state: project_name="my-project",
  current_focus="Debugging authentication flow",
  merge_mode="merge"
```

### Force Override When Needed
```bash
save_project_state: project_name="my-web-app-v2", 
  force=true, 
  current_focus="Starting version 2"
```

## 🗂️ Enhanced Data Storage

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

### Enhanced State Structure

Each saved state now includes merge tracking:

```json
{
  "project_name": "my-project",
  "current_focus": "What you're working on now",
  "technical_decisions": ["Accumulated", "decisions", "over", "time"],
  "files_modified": ["All", "files", "ever", "touched"],
  "next_actions": ["Current planned steps"],
  "conversation_summary": "Brief context summary",
  "last_updated": "2025-06-15T10:30:00Z",
  "version": "1.2",
  "merge_mode_used": "append_lists",
  "validation_bypassed": false
}
```

## 🛡️ Merge Mode Details

### `append_lists` Mode (Recommended)
- **Arrays/Lists:** New items are appended to existing lists (duplicates avoided for strings)
- **Other Fields:** Overwritten with new values
- **Best For:** Multi-session development where you want to accumulate decisions and files

### `merge` Mode  
- **All Fields:** New data updates/overwrites existing fields
- **Missing Fields:** Preserved from existing state
- **Best For:** Focused updates to specific aspects of a project

### `replace` Mode (Original Behavior)
- **All Data:** Completely overwrites existing state
- **Best For:** Starting fresh or major project pivots

## 🔍 Troubleshooting

Same as original, plus:

### Merge Mode Issues
**Lists getting too long:**
Occasionally use `replace` mode to start fresh, or manually clean up your project state files.

**Unexpected merge behavior:**
Check the `merge_mode_used` field in your saved state to see which mode was applied.

## 🧪 Development Notes

> **Disclaimer:** This fork was created through "vibe coding" with Claude's assistance. I'm not a professional programmer - just someone who wanted better conversation continuity! The implementation works for my use case, but there might be edge cases I haven't considered. Use at your own discretion and feel free to improve! 🤝

### Key Changes Made
- Added `merge_mode` parameter to `save_state` method
- Implemented three merge strategies with list deduplication
- Updated tool schema to expose merge mode options
- Enhanced state metadata to track merge behavior
- Maintained backward compatibility with original behavior

### Requirements
- Python 3.8+
- MCP SDK 1.0+
- difflib (built-in, for fuzzy matching)

## 🤝 Contributing

All credit for the original amazing work goes to [peless](https://github.com/peless/claude-thread-continuity)! 

If you want to improve this fork:
1. Go fork yourself! Fork this repository
2. Make your improvements (probably better than my vibe coding! 😄)
3. Submit a pull request

## 📄 License

MIT License - same as the original project.

## 🚀 Why This Enhanced Version Matters

**Original version:** 😫 Hit token limit → Start new thread → Lose conversation context → Re-explain recent decisions

**Enhanced version:** 😎 Hit token limit → Start new thread → `load_project_state` → `save_project_state` with `merge_mode="append_lists"` → **All context accumulates over time!**

Perfect for:
- 🏗️ **Long-term Development Projects** - Build up complete history of decisions and files
- 📚 **Extended Learning Sessions** - Accumulate knowledge and progress over multiple conversations  
- ✍️ **Iterative Writing Projects** - Keep track of all changes and decisions across sessions
- 🔧 **Complex Debugging** - Maintain complete context of attempted solutions and findings

## 📈 Fork History

### v1.🍴.0 (This Fork)
- ✨ **Multi-Session State Accumulation** - Lists build up over time instead of being overwritten
- ✨ **Three Merge Strategies** - `append_lists`, `merge`, and `replace` modes
- ✨ **Smart List Management** - Automatic deduplication for string arrays
- ✨ **Enhanced Metadata** - Track which merge mode was used
- 🤝 **Backward Compatible** - Original behavior preserved as default

### v1.1.0 (Original by peless)
- ✨ **Project Validation System** - Prevents fragmentation with fuzzy name matching
- ✨ **validate_project_name** tool - Manual name checking
- ✨ **Force Override** capability - Bypass validation when needed

### v1.0.0 (Original by peless)
- 🚀 Initial release with core continuity functionality

---

**Original by [peless](https://github.com/peless/claude-thread-continuity) | Enhanced fork with ❤️ and vibe coding**

*Now with true conversation continuity - your project context actually grows over time!*
