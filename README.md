# NexusAI - Intelligent Code Assistant 🚀

<div align="center">

![NexusAI Logo](https://img.shields.io/badge/NexusAI-v2.1-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDAgMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0NSIgZmlsbD0iIzYzNjZmMSIvPjx0ZXh0IHg9IjUwIiB5PSI2OCIgZm9udC1zaXplPSI1MCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0id2hpdGUiPk48L3RleHQ+PC9zdmc+)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![Monaco](https://img.shields.io/badge/Monaco_Editor-0.45-007ACC?style=for-the-badge&logo=visualstudiocode&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A professional AI-powered code editor with intelligent assistant, real-time code execution, and advanced developer tools.**

[Features](#-features) • [Demo](#-demo) • [Installation](#-installation) • [Architecture](#-architecture) • [API](#-api-reference) • [Contributing](#-contributing)

</div>

---

## ✨ Features

### 🤖 AI-Powered Assistance
- **Intelligent Chat Interface** — Natural language coding assistance powered by multiple AI models (DeepSeek, Gemini, Llama, Qwen)
- **Code Explanation** — Get detailed, step-by-step explanations of complex code
- **Bug Detection & Auto-Fix** — AI-powered debugging with one-click error resolution
- **Code Generation** — Generate complete, runnable code from natural language descriptions
- **Auto-Optimization** — Performance improvement suggestions with diff preview

### 📝 Professional Code Editor
- **Monaco Editor** — VS Code's powerful editor engine with IntelliSense
- **20+ Languages** — Python, JavaScript, TypeScript, Go, Rust, Java, C++, Ruby, PHP, and more
- **Syntax Highlighting** — Beautiful code coloring powered by highlight.js
- **Multi-file Tabs** — Work with multiple files simultaneously
- **Code Formatting** — Auto-format with language-specific rules

### ⚡ Code Execution Engine
- **Real-time Execution** — Run Python, JavaScript, Go, Ruby, PHP directly in the browser
- **Compiled Language Support** — Compile and run Java, C++, C, Rust, C# with error reporting
- **Integrated Terminal** — View output and errors in a professional terminal emulator
- **Stdin Support** — Handle interactive programs with user input prompts
- **Error-to-AI Pipeline** — Automatically feed execution errors to the AI for instant fixes

### 🎨 Premium UI/UX
- **VS Code-like Interface** — Familiar 3-panel layout (Explorer, Editor, Chat)
- **Command Palette** — Quick access to all features via `Ctrl+Shift+P`
- **Glassmorphism Design** — Modern glass effects with gradient backgrounds
- **Smooth Animations** — Micro-animations for enhanced user experience
- **Responsive Design** — Works on desktop, tablet, and mobile

### � Developer Tooling
- **Code Metrics** — Lines of code, complexity analysis, function count
- **Code Snippets** — Save, search, and reuse code snippets
- **Session Persistence** — Auto-save and restore coding sessions
- **Live Preview** — Real-time HTML/CSS preview panel
- **Image-to-Code** — Convert design mockups to code using AI vision
- **GitHub Integration** — Clone repositories directly into the workspace
- **Code Templates** — 14+ starter templates for various languages

---

## 🎯 Demo

### Command Palette
Press `Ctrl+Shift+P` to access all features quickly:

```
📄 New File           | ▶️ Run Code
📂 Open File          | ✨ Format Code
💾 Save File          | 📊 Code Metrics
🤖 Ask AI             | 📚 Browse Snippets
🌓 Toggle Theme       | ⌨️ Keyboard Shortcuts
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` | Command Palette |
| `Ctrl+Enter` | Run Code |
| `Ctrl+S` | Save to Workspace |
| `Ctrl+/` | Focus Chat |
| `Ctrl+N` | New File |
| `Ctrl+O` | Open File |
| `Shift+Alt+F` | Format Code |
| `Escape` | Close Modals |

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for cloning)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/nexusai.git
cd nexusai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r ai_smart_assistant/app/requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OpenRouter API key

# Run the application
python run.py
```

### Environment Variables

Create a `.env` file in the root directory:

```env
OPENROUTER_API_KEY=your_api_key_here
SECRET_KEY=your-secret-key
```

Get your free API key at [OpenRouter.ai](https://openrouter.ai/keys)

### Command Line Options

```bash
python run.py                     # Default: localhost:5000
python run.py --port 8080         # Custom port
python run.py --host 0.0.0.0     # Allow external access
python run.py --no-debug          # Production mode
```

---

## 🏗️ Architecture

### Project Structure

```
nexusai/
├── run.py                          # Application entry point (CLI)
├── .env                            # Environment variables (not tracked)
├── .env.example                    # Environment template
├── LICENSE                         # MIT License
├── CONTRIBUTING.md                 # Contribution guidelines
├── README.md                       # This file
│
├── ai_smart_assistant/
│   └── app/
│       ├── __init__.py             # Flask app factory
│       ├── config.py               # Centralized configuration
│       ├── routes.py               # API endpoints (20+ routes)
│       ├── requirements.txt        # Python dependencies
│       ├── templates/
│       │   ├── base.html           # Base template (SEO, meta tags)
│       │   └── index.html          # Main IDE interface
│       └── assets/
│           ├── css/
│           │   └── style.css       # Premium glassmorphism theme
│           └── js/
│               ├── app.js          # Core application modules
│               └── templates.js    # 14+ code templates
│
└── workspace/                      # Code execution sandbox
```

### Design Patterns Used

| Pattern | Usage |
|---------|-------|
| **Factory Pattern** | Flask app creation (`create_app()`) |
| **Blueprint Architecture** | Modular route organization |
| **Module Pattern** | Frontend JS (`Utils`, `API`, `EditorManager`, etc.) |
| **Observer Pattern** | Event-driven UI updates |
| **SSE (Server-Sent Events)** | Real-time AI chat streaming |
| **Strategy Pattern** | Multi-language code execution runners |

---

## 🛠️ Technologies

### Backend
| Technology | Purpose |
|-----------|---------|
| **Flask 3.0** | Web framework & API server |
| **OpenRouter API** | Multi-model AI gateway |
| **Python 3.10+** | Core runtime |
| **Werkzeug** | WSGI utilities & security |

### Frontend
| Technology | Purpose |
|-----------|---------|
| **Monaco Editor** | VS Code's editor engine |
| **Marked.js** | Markdown rendering |
| **Highlight.js** | Syntax highlighting |
| **diff2html** | Code diff visualization |

### AI Models (via OpenRouter)
| Model | Strength |
|-------|----------|
| DeepSeek R1 | Advanced reasoning |
| Google Gemini 2.0 Flash | Fast & capable |
| Meta Llama 3.3 70B | Open-source powerhouse |
| Qwen 2.5 72B | Multilingual expert |
| Microsoft Phi-3 Medium | Compact & efficient |

---

## 🔌 API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main editor interface |
| `/chat` | POST | AI chat with SSE streaming |
| `/run-code` | POST | Execute code (20+ languages) |
| `/upload` | POST | Upload file/project (ZIP) |
| `/vision-analyze` | POST | Image-to-code (AI vision) |
| `/github-clone` | POST | Clone Git repository |
| `/api/format-code` | POST | Format code |
| `/api/analyze-code` | POST | Code metrics & analysis |
| `/api/syntax-check` | POST | Syntax validation |
| `/api/snippets` | GET/POST/DELETE | Snippet management |
| `/api/templates` | GET | Code templates |
| `/api/models` | GET | Available AI models |
| `/api/languages` | GET | Supported languages |
| `/api/session` | GET/POST/DELETE | Session management |
| `/api/export-chat` | GET | Export chat history |
| `/health` | GET | Health check |

### Example: Run Code

```bash
curl -X POST http://localhost:5000/run-code \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, World!\")", "language": "python"}'
```

### Example: Chat with AI

```bash
curl -X POST http://localhost:5000/chat \
  -F "user_input=Explain how Python decorators work"
```

---

## 📈 Future Roadmap

- [ ] Collaborative editing via WebSocket
- [ ] VS Code extension
- [ ] Plugin system for custom tools
- [ ] Git integration (commit, push, pull)
- [ ] Docker containerization
- [ ] Multi-language debugging with breakpoints
- [ ] Custom AI model selection in settings
- [ ] Workspace file persistence

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ using Flask, Monaco Editor, and OpenRouter AI**

⭐ Star this repo if you find it useful!

</div>
