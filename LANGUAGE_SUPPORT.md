# NexusAI Language Support Guide 🚀

## Overview
NexusAI now supports **30+ programming languages** with powerful execution, analysis, and AI-assisted features.

---

## Supported Languages

### 📜 **Interpreted Languages** (No compilation needed)
Execute directly in the browser or server.

| Language | Command | Icon | Features |
|----------|---------|------|----------|
| **Python** | `python` | 🐍 | Full execution, syntax check, formatting with Black |
| **JavaScript** | `node` | 📜 | Full execution, modern ES6+ support |
| **TypeScript** | `ts-node` | 📘 | Full execution with type checking |
| **Ruby** | `ruby` | 💎 | Full execution, dynamic typing |
| **PHP** | `php` | 🐘 | Web scripting, server-side execution |
| **Go** | `go run` | 🐹 | Concurrent programming support |
| **Bash/Shell** | `bash` | 🖥️ | System commands, scripting |
| **PowerShell** | `powershell` | ⚡ | Windows automation scripts |
| **Perl** | `perl` | 🐪 | Text processing, scripting |
| **Lua** | `lua` | 🌙 | Lightweight scripting |

### ⚙️ **Compiled Languages** (Compilation required)
Automatically compiled before execution.

| Language | Compiler | Icon | Features |
|----------|----------|------|----------|
| **Java** | `javac` | ☕ | OOP, static typing, JVM |
| **C++** | `g++` | ➕ | Performance, system programming |
| **C** | `gcc` | 🔤 | Low-level, embedded systems |
| **C#** | `csc` | 🎯 | .NET framework, Windows |
| **Rust** | `rustc` | 🦀 | Memory safety, performance |

### 📄 **Markup & Web** (Preview mode)
Display and analyze without execution.

| Language | Icon | Best For |
|----------|------|----------|
| **HTML** | 📄 | Web page structure |
| **CSS** | 🎨 | Styling and layout |
| **JSON** | 📦 | Data interchange format |
| **XML** | 📋 | Document structure |
| **Markdown** | 📝 | Documentation |

### 🗄️ **Database & Other**

| Language | Icon | Best For |
|----------|------|----------|
| **SQL** | 🗄️ | Database queries and operations |

---

## Key Features by Language Type

### ✅ **All Languages Support:**
- ✓ Syntax highlighting (30+ themes available)
- ✓ Code formatting
- ✓ Code analysis (lines, functions, imports, etc.)
- ✓ Syntax validation
- ✓ Download/Export
- ✓ AI-powered suggestions

### ✅ **Executable Languages Add:**
- ✓ Real-time code execution
- ✓ Standard input/output (stdin/stdout)
- ✓ Error detection and AI-powered fixes
- ✓ Execution history
- ✓ Performance metrics
- ✓ Timeout protection (60-second limit)

### ✅ **Web Languages Add:**
- ✓ Live preview (HTML/CSS)
- ✓ Browser compatibility checking
- ✓ Responsive design testing

---

## Quick Start Templates

Every language has pre-built templates for quick initialization:

### Python
- 🐍 **Python Script** - Basic script template
- 🏗️ **Python Class** - OOP example with methods
- 🔧 **Flask API** - REST API with routes

### JavaScript/TypeScript
- 📡 **JS Fetch API** - HTTP request example
- ⏳ **JS Async/Await** - Asynchronous programming
- ⚡ **Express App** - Node.js server template

### Web
- 🌐 **HTML Page** - Semantic HTML5 boilerplate
- 🎨 **CSS Grid** - Modern layout system
- 📸 **Image to Code** - Convert designs to HTML/CSS

### Backend
- 🔧 **Flask API** - Python REST framework
- ⚡ **Express App** - JavaScript/Node.js framework

### Other Languages
- ☕ **Java Main** - Basic Java program
- ☕ **Java Class** - Object-oriented example
- 🐹 **Go Program** - Goroutine-ready template
- 🦀 **Rust Program** - Memory-safe program
- ➕ **C++ Program** - Modern C++ example
- 🗄️ **SQL Query** - Complete CRUD operations

**How to Use:** Click any template button in the Explorer panel, and it automatically loads into the editor with the correct language selected.

---

## Execution & Error Handling

### Running Code
1. Click **▶ Run** button or press **Ctrl+Enter**
2. Code executes in isolated temporary environment
3. Output appears in Terminal panel
4. Errors are captured and displayed with AI suggestions

### Input/Output
- **stdin**: Provide input via Terminal input field
- **stdout**: View output in Terminal panel
- **stderr**: Error messages displayed in red

### Timeout Protection
- Each execution limited to **60 seconds**
- Infinite loops automatically terminated
- Memory-safe execution environment

---

## AI-Powered Features

All code benefits from AI analysis through the integrated assistant:

### Code Analysis
- **Analyze Code** - Metrics, complexity, structure
- **Syntax Check** - Validate before execution
- **Find Bugs** - Detect logical errors
- **Improve Performance** - Optimization suggestions

### AI Assistance
- **Explain Code** - Step-by-step explanation
- **Debug Code** - AI-powered debugging
- **Generate Tests** - Automatic test generation
- **Refactor Code** - Code quality improvements
- **Optimize Code** - Performance tuning

### Code Generation
- **From Comments** - Turn comments into code
- **From Templates** - Customize starter templates
- **Image to Code** - Convert UI designs to HTML/CSS

---

## Language-Specific Tips

### Python
```python
# NexusAI supports:
- Type hints (3.5+)
- Async/await
- Decorators
- Class-based and functional programming
```

### JavaScript
```javascript
// NexusAI supports:
- ES6+ features (arrow functions, destructuring, etc.)
- Promise and async/await
- Module imports/exports
- Modern DOM APIs
```

### Java
```java
// NexusAI supports:
- Multiple classes in single file
- Generics and interfaces
- Exception handling
- Inner/anonymous classes
```

### Rust
```rust
// NexusAI supports:
- Ownership and borrowing
- Pattern matching
- Traits and impls
- Async/await (tokio)
```

### SQL
```sql
-- NexusAI supports:
- SELECT, INSERT, UPDATE, DELETE
- JOINs and subqueries
- Transactions
- Aggregate functions
```

---

## Installation Requirements

For compiled languages, ensure these are installed on your system:

```bash
# Java
java -version

# C/C++
g++ --version
gcc --version

# Rust
rustc --version

# Go
go version

# Python
python --version

# Node.js (for JavaScript/TypeScript)
node --version
npm --version
```

To install:
- **Java**: https://www.oracle.com/java/
- **C/C++**: `apt-get install gcc g++` (Linux) or XCode (macOS)
- **Rust**: https://rustup.rs
- **Go**: https://golang.org/dl
- **Python**: https://python.org
- **Node.js**: https://nodejs.org

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Run code |
| `Ctrl+S` | Save/Download |
| `Shift+Alt+F` | Format code |
| `Ctrl+/` | Focus chat |
| `Ctrl+Shift+P` | Command palette |
| `Ctrl+N` | New file |
| `Ctrl+O` | Open file |

---

## Workflow Examples

### Python Development
1. Click **🐍 Python Script** template
2. Write your code
3. Press **Ctrl+Enter** to execute
4. View output in Terminal
5. Ask AI "Explain this code" for help

### Web Development
1. Click **🌐 HTML Page** template
2. Write HTML + CSS
3. Click **👁️ Preview** for live preview
4. Click **✨ Format Code** to beautify
5. Ask AI "Make this responsive"

### Data Science
1. Load Python template
2. Write pandas/numpy code
3. Click **📊 Analyze Code** for metrics
4. Execute with **Ctrl+Enter**
5. Ask AI for optimization suggestions

### Algorithm Development
1. Select any language template
2. Write algorithm code
3. Click **🧪 Generate Tests** for unit tests
4. Execute and iterate
5. Ask AI "Improve performance"

---

## Best Practices

### 1. **Format Your Code**
Always use `Shift+Alt+F` or "Format Code" command to maintain consistency.

### 2. **Check Syntax First**
Use "Check Syntax" before running to catch errors early.

### 3. **Use Templates**
Start with language templates to follow best practices.

### 4. **Leverage AI**
Ask AI for explanations, debugging, and optimization.

### 5. **Save Often**
Press `Ctrl+S` frequently to save your work.

### 6. **Read Error Messages**
AI analyzes errors and suggests fixes.

---

## Troubleshooting

### "Runtime not found" Error
**Solution:** Install the required runtime for your language.

### Code Takes Too Long
**Solution:** Infinite loop detected. Check your loop conditions. (60-second timeout limit)

### Import Not Found (Python)
**Solution:** Install package with pip first, or ask AI for help.

### Compilation Failed
**Solution:** Check syntax and compiler version. AI can suggest fixes.

### Preview Not Working
**Solution:** Live preview only works for HTML/CSS. Other languages need to be saved to disk.

---

## Performance Tips

### Python
- Use list comprehensions instead of loops
- Avoid global variables
- Use built-in functions (they're optimized)

### JavaScript
- Minimize DOM manipulations
- Use async/await for better flow
- Leverage modern browser APIs

### Java
- Use proper generics
- Avoid creating unnecessary objects
- Use StringBuilder for string concatenation

### C/C++
- Use -O2 optimization flag
- Manage memory carefully
- Prefer algorithms over raw loops

### Rust
- Let the compiler guide you (errors are helpful)
- Use iterators instead of loops
- Embrace the type system

---

## Getting Help

1. **Use AI Features**: Ask the assistant for explanations, debugging, and suggestions
2. **Check Templates**: Browse template examples for your language
3. **Read Documentation**: Click language links for official docs
4. **Code Metrics**: Analyze your code structure with "Analyze Code"
5. **Search**: Find similar code patterns in our snippet library

---

## Coming Soon 🚀

- Docker integration for advanced language support
- Remote code execution (secure cloud)
- Collaborative editing
- Version control integration
- Package management (pip, npm, cargo, etc.)
- Advanced debugging with breakpoints
- Code coverage analysis

---

**Happy Coding! 🎉**

*NexusAI - Your Intelligent Programming Companion*
