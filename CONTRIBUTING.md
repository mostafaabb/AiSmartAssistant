# Contributing to NexusAI 🚀

Thank you for your interest in contributing to NexusAI! We welcome contributions from everyone.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)

## 📜 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## 🚀 Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/yourusername/nexusai.git
   cd nexusai
   ```
3. **Create** a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🛠️ Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r ai_smart_assistant/app/requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Run the development server:
   ```bash
   python run.py
   ```

## ✏️ Making Changes

### Backend (Python/Flask)
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Write meaningful error messages
- Add appropriate logging

### Frontend (JavaScript/CSS)
- Use ES6+ syntax
- Follow the existing module pattern (e.g., `const ModuleName = { ... }`)
- Keep CSS organized by component sections
- Test across multiple browsers

### Templates (HTML/Jinja2)
- Use semantic HTML5 elements
- Ensure accessibility (ARIA labels, keyboard navigation)
- Keep templates modular using Jinja2 blocks

## 📬 Pull Request Process

1. **Update** documentation if you've changed APIs or features
2. **Test** your changes thoroughly
3. **Commit** with clear, descriptive messages:
   ```
   feat: add multi-language syntax checking
   fix: resolve code execution timeout issue
   docs: update API reference for new endpoints
   ```
4. **Push** your branch and create a Pull Request
5. **Describe** your changes in the PR description

## 🎨 Style Guidelines

### Commit Messages
We follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Code Quality
- Write self-documenting code with clear variable names
- Keep functions focused and small
- Handle errors gracefully
- Add comments for complex logic

---

Thank you for contributing to NexusAI! 🎉
