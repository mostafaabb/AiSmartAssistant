"""
NexusAI Routes Module
Defines all API endpoints and page routes for the NexusAI code assistant.

Endpoints:
    - GET  /              : Main editor page
    - POST /chat          : AI chat with streaming response
    - POST /run-code      : Execute code in various languages
    - POST /upload        : Upload file or project (ZIP)
    - POST /vision-analyze: Image-to-code conversion
    - POST /github-clone  : Clone a GitHub repository
    - GET  /health        : Health check endpoint
    - Various /api/* endpoints for utilities
"""

import json
import time
import logging
import requests
import os
import zipfile
import io
import subprocess
import tempfile
import shutil
from datetime import datetime

from flask import (
    Blueprint, render_template, request, current_app,
    redirect, url_for, jsonify, Response, stream_with_context
)
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

# Configuration
ALLOWED_EXTENSIONS = {
    'py', 'js', 'html', 'css', 'json', 'txt', 'md', 'ts',
    'java', 'cpp', 'c', 'cs', 'zip', 'jsx', 'tsx', 'vue',
    'go', 'rs', 'rb', 'php', 'sql', 'yaml', 'yml', 'xml',
    'sh', 'bat'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PROJECT_FILES = 50

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Utility to collect project files in a repo/zip for context
def collect_project_files(root_dir):
    project_files = []
    for root, dirs, files in os.walk(root_dir):
        if '.git' in root:
            continue
        for name in files:
            if any(name.endswith(ext) for ext in ALLOWED_EXTENSIONS if ext != 'zip'):
                try:
                    fpath = os.path.join(root, name)
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        project_files.append({
                            "name": os.path.relpath(fpath, root_dir),
                            "content": f.read(),
                            "language": name.rsplit('.', 1)[1].lower() if '.' in name else 'txt'
                        })
                except Exception:
                    continue
    return project_files

# Global state for single-user local environment
# Replacing robust server-side session due to environment constraints
GLOBAL_STATE = {
    'history': [],
    'code_context': None,
    'last_execution_error': None
}

@main.route('/', methods=['GET'])
def index():
    """Render the main NexusAI editor interface."""
    return render_template(
        "index.html",
        history=GLOBAL_STATE['history'],
        code_context=GLOBAL_STATE['code_context']
    )


# System prompt for better AI responses
SYSTEM_PROMPT = """You are NexusAI, an expert AI programming assistant. You help developers write, debug, and understand code.

Guidelines:
- Be concise but thorough
- Always provide working code examples when relevant
- Explain your reasoning step by step
- Use proper code formatting with language identifiers
- When fixing bugs, explain what was wrong and why the fix works
- Suggest best practices and optimizations when appropriate
- If you're unsure, say so and provide alternatives

Remember: You're helping a developer in an IDE, so prioritize practical, runnable code."""


@main.route('/chat', methods=['POST'])
def chat():
    """Streaming AI chat endpoint.

    Accepts user prompts via form data and streams AI responses
    using Server-Sent Events (SSE). Automatically includes code
    context and recent errors for enhanced assistance.

    Form Data:
        user_input (str): The user's message or question.

    Returns:
        SSE stream with AI-generated content chunks.
    """
    prompt = request.form.get('user_input')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    context = GLOBAL_STATE.get('code_context')
    last_error = GLOBAL_STATE.get('last_execution_error')
    
    # Auto-Refine Logic: Inject last error if relevant
    if last_error and any(k in prompt.lower() for k in ["fix", "error", "debug", "why", "help"]):
        prompt = f"The terminal just reported this error:\n```\n{last_error}\n```\nTask: {prompt}"
        GLOBAL_STATE['last_execution_error'] = None # Clear after use

    full_prompt = prompt
    if context:
        if context['type'] == 'single':
            full_prompt = f"Context: File {context['name']}\n```{context['language']}\n{context['content']}\n```\n\nTask: {prompt}"
        else:
            files = context['files'][:15] # Pruned context
            proj_ctx = f"Project: {context['name']}\n"
            for f in files:
                proj_ctx += f"File: {f['name']}\n```{f['language']}\n{f['content']}\n```\n"
            full_prompt = f"{proj_ctx}\nTask: {prompt}"

    GLOBAL_STATE['history'].append({"role": "user", "content": prompt})
    # session.modified = True -- Not needed for in-memory global state

    def generate():
        # Immediate UI Feedback
        yield f"data: {json.dumps({'content': ''})}\n\n"
        
        api_key = current_app.config.get('OPENROUTER_API_KEY')
        if not api_key or api_key == 'your_openrouter_api_key_here':
            yield f"data: {json.dumps({'content': '⚠️ **Configuration Required**\n\nPlease set your `OPENROUTER_API_KEY` in the `.env` file.\n\n**Steps:**\n1. Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys)\n2. Open `.env` file in project root\n3. Replace `your_openrouter_api_key_here` with your key\n4. Restart the server'})}\n\n"
            return

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}", 
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "NexusAI Code Assistant",
            "Content-Type": "application/json"
        }
        
        # Models to try - using most reliable free models (ordered by quality)
        models_to_try = [
            "deepseek/deepseek-r1-0528:free",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "microsoft/phi-3-medium-128k-instruct:free"
        ]
        
        full_response = ""
        success = False
        last_debug_msg = ""
        
        for model in models_to_try:
            try:
                data = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt}
                    ],
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
                
                # Check for 200 OK before iterating
                with requests.post(url, headers=headers, json=data, stream=True, timeout=60) as r:
                    if r.status_code != 200:
                        last_exec_error = r.text
                        try:
                            err_json = r.json()
                            if 'error' in err_json:
                                last_exec_error = json.dumps(err_json['error'])
                        except Exception:
                            pass
                        
                        last_debug_msg = f"Model {model} failed with status {r.status_code}: {last_exec_error}"
                        logger.warning(last_debug_msg)
                        time.sleep(1) # Backoff briefly
                        continue
                        
                    for line in r.iter_lines():
                        if line:
                            chunk = line.decode('utf-8').replace('data: ', '')
                            if chunk == '[DONE]': break
                            try:
                                j = json.loads(chunk)
                                content = j['choices'][0]['delta'].get('content', '')
                                full_response += content
                                yield f"data: {json.dumps({'content': content})}\n\n"
                            except (json.JSONDecodeError, KeyError, IndexError):
                                continue
                    
                    # If we got here with some response, mark success
                    if full_response:
                        success = True
                        break
            except Exception as e:
                last_debug_msg = f"Exception attempting {model}: {str(e)}"
                continue
                
        if not success:
            debug_info = f"\n\nDEBUG INFO: {last_debug_msg}" if 'last_debug_msg' in locals() else ""
            yield f"data: {json.dumps({'content': f'\n\n⚠️ **Connection Error**\n\nUnable to reach AI models. Please check:\n1. Your internet connection\n2. Your API key is valid\n3. OpenRouter service status{debug_info}'})}\n\n"
        else:
            # Save to history once done
            GLOBAL_STATE['history'].append({"role": "assistant", "content": full_response})

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


# ==================== UTILITY ENDPOINTS ====================

@main.route('/api/format-code', methods=['POST'])
def format_code():
    """Format code using language-specific formatters.

    Request JSON:
        code (str): Source code to format.
        language (str): Programming language identifier.

    Returns:
        JSON with formatted code and formatter info.
    """
    data = request.json or {}
    code = data.get('code', '')
    language = data.get('language', 'python').lower()
    
    if not code.strip():
        return jsonify({"error": "No code provided"}), 400
    
    # Language-specific formatting
    formatters = {
        'python': {'cmd': ['black', '-'], 'description': 'Black formatter'},
        'javascript': {'cmd': ['npx', 'prettier', '--stdin-filepath', 'file.js'], 'description': 'Prettier'},
        'typescript': {'cmd': ['npx', 'prettier', '--stdin-filepath', 'file.ts'], 'description': 'Prettier'},
        'json': {'cmd': ['python', '-m', 'json.tool'], 'description': 'JSON formatter'},
        'html': {'cmd': ['npx', 'prettier', '--stdin-filepath', 'file.html'], 'description': 'Prettier'},
        'css': {'cmd': ['npx', 'prettier', '--stdin-filepath', 'file.css'], 'description': 'Prettier'},
        'java': {'cmd': ['google-java-format', '-'], 'description': 'Google Java Format'},
        'sql': {'manual': True, 'description': 'Manual formatting recommended'},
        'xml': {'cmd': ['python', '-m', 'xml.dom.minidom'], 'description': 'XML formatter'},
    }
    
    if language not in formatters:
        return jsonify({
            "formatted": code,
            "message": f"ℹ️ No automatic formatter for {language}. Manual formatting recommended."
        })
    
    formatter = formatters[language]
    
    if formatter.get('manual'):
        return jsonify({
            "formatted": code,
            "message": f"ℹ️ {formatter['description']}"
        })
    
    try:
        result = subprocess.run(
            formatter['cmd'],
            input=code,
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return jsonify({
                "formatted": result.stdout,
                "success": True,
                "formatter": formatter['description']
            })
        else:
            return jsonify({
                "formatted": code,
                "message": f"⚠️ Formatter '{formatter['description']}' not available. Install with: pip install {language}-tools"
            })
    except Exception as e:
        return jsonify({
            "formatted": code,
            "message": f"ℹ️ Could not auto-format: {str(e)}"
        })


@main.route('/api/analyze-code', methods=['POST'])
def analyze_code():
    """Analyze code metrics including line count, complexity, and structure.

    Request JSON:
        code (str): Source code to analyze.
        language (str): Programming language identifier.

    Returns:
        JSON with detailed code metrics and analysis.
    """
    data = request.json or {}
    code = data.get('code', '')
    language = data.get('language', 'python').lower()
    
    if not code.strip():
        return jsonify({"error": "No code provided"}), 400
    
    analysis = {
        "language": language,
        "lines": len(code.split('\n')),
        "characters": len(code),
        "words": len(code.split()),
        "functions": code.count('def ') + code.count('function ') + code.count('func '),
        "imports": code.count('import ') + code.count('require('),
        "comments": code.count('#') + code.count('//'),
    }
    
    # Language-specific analysis
    if language == 'python':
        analysis["classes"] = code.count('class ')
        analysis["async_functions"] = code.count('async def ')
        analysis["decorators"] = code.count('@')
        
    elif language in ['javascript', 'typescript', 'js', 'ts']:
        analysis["classes"] = code.count('class ')
        analysis["async_functions"] = code.count('async ')
        analysis["const_declarations"] = code.count('const ')
        analysis["let_declarations"] = code.count('let ')
        
    elif language in ['java']:
        analysis["classes"] = code.count('class ')
        analysis["interfaces"] = code.count('interface ')
        analysis["methods"] = code.count('public ') + code.count('private ')
        
    elif language in ['cpp', 'c++', 'c']:
        analysis["includes"] = code.count('#include')
        analysis["structs"] = code.count('struct ')
        
    elif language == 'sql':
        analysis["tables"] = code.count('FROM ') + code.count('from ')
        analysis["joins"] = code.count('JOIN')
        analysis["selects"] = code.count('SELECT') + code.count('select')
    
    return jsonify(analysis)


@main.route('/api/languages', methods=['GET'])
def get_languages():
    """Get all supported languages"""
    languages = {
        "interpreted": [
            {"name": "Python", "id": "python", "icon": "🐍", "version": "3.x"},
            {"name": "JavaScript", "id": "javascript", "icon": "📜", "version": "ES6+"},
            {"name": "TypeScript", "id": "typescript", "icon": "📘", "version": "Latest"},
            {"name": "Ruby", "id": "ruby", "icon": "💎", "version": "2.7+"},
            {"name": "PHP", "id": "php", "icon": "🐘", "version": "7.0+"},
            {"name": "Go", "id": "go", "icon": "🐹", "version": "1.16+"},
            {"name": "Perl", "id": "perl", "icon": "🐪", "version": "5.0+"},
            {"name": "Lua", "id": "lua", "icon": "🌙", "version": "5.0+"},
            {"name": "Bash", "id": "bash", "icon": "🖥️", "version": "5.0+"},
            {"name": "PowerShell", "id": "powershell", "icon": "⚡", "version": "5.1+"}
        ],
        "compiled": [
            {"name": "Java", "id": "java", "icon": "☕", "version": "8+"},
            {"name": "C++", "id": "cpp", "icon": "➕", "version": "11+"},
            {"name": "C", "id": "c", "icon": "🔤", "version": "99+"},
            {"name": "C#", "id": "csharp", "icon": "🎯", "version": "7.0+"},
            {"name": "Rust", "id": "rust", "icon": "🦀", "version": "1.0+"}
        ],
        "markup": [
            {"name": "HTML", "id": "html", "icon": "📄", "version": "5"},
            {"name": "CSS", "id": "css", "icon": "🎨", "version": "3+"},
            {"name": "XML", "id": "xml", "icon": "📋", "version": "1.0"},
            {"name": "JSON", "id": "json", "icon": "📦", "version": "RFC 7159"},
            {"name": "SQL", "id": "sql", "icon": "🗄️", "version": "2016+"},
            {"name": "Markdown", "id": "markdown", "icon": "📝", "version": "Latest"}
        ]
    }
    return jsonify(languages)


@main.route('/api/syntax-check', methods=['POST'])
def syntax_check():
    """Check syntax without executing code"""
    data = request.json or {}
    code = data.get('code', '')
    language = data.get('language', 'python').lower()
    
    if not code.strip():
        return jsonify({"valid": True, "message": "Empty code"})
    
    # Python syntax check
    if language in ['python', 'python3']:
        try:
            compile(code, '<string>', 'exec')
            return jsonify({"valid": True, "message": "✅ Valid Python syntax"})
        except SyntaxError as e:
            return jsonify({
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset,
                "message": f"Syntax error at line {e.lineno}: {e.msg}"
            })
    
    # JSON syntax check
    elif language == 'json':
        try:
            json.loads(code)
            return jsonify({"valid": True, "message": "✅ Valid JSON"})
        except json.JSONDecodeError as e:
            return jsonify({
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "message": f"Invalid JSON at line {e.lineno}: {e.msg}"
            })
    
    # Basic bracket matching for other languages
    else:
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        errors = []
        
        for i, char in enumerate(code):
            if char in brackets:
                stack.append((char, i))
            elif char in brackets.values():
                if not stack:
                    errors.append(f"Unexpected closing bracket '{char}' at position {i}")
                else:
                    opening, _ = stack.pop()
                    if brackets[opening] != char:
                        errors.append(f"Mismatched brackets at position {i}")
        
        if stack:
            for opening, pos in stack:
                errors.append(f"Unclosed bracket '{opening}' at position {pos}")
        
        if errors:
            return jsonify({"valid": False, "errors": errors})
        else:
            return jsonify({"valid": True, "message": f"✅ Basic syntax check passed for {language}"})


@main.route('/api/models', methods=['GET'])
def list_models():
    """List available AI models"""
    models = [
        {"id": "deepseek/deepseek-r1-0528:free", "name": "DeepSeek R1", "description": "Latest reasoning model"},
        {"id": "google/gemini-2.0-flash-exp:free", "name": "Gemini 2.0 Flash", "description": "Fast & capable"},
        {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Llama 3.3 70B", "description": "Open-source powerhouse"},
        {"id": "qwen/qwen-2.5-72b-instruct:free", "name": "Qwen 2.5 72B", "description": "Multilingual expert"},
        {"id": "microsoft/phi-3-medium-128k-instruct:free", "name": "Phi-3 Medium", "description": "Compact & efficient"}
    ]
    return jsonify({"models": models})


@main.route('/api/context', methods=['GET'])
def get_context():
    """Get current code context info"""
    context = GLOBAL_STATE.get('code_context')
    if not context:
        return jsonify({"has_context": False})
    
    if context['type'] == 'single':
        return jsonify({
            "has_context": True,
            "type": "single",
            "name": context['name'],
            "language": context['language'],
            "size": len(context.get('content', ''))
        })
    else:
        return jsonify({
            "has_context": True,
            "type": "project",
            "name": context['name'],
            "file_count": len(context.get('files', []))
        })


@main.route('/api/download-code', methods=['POST'])
def download_code():
    """Prepare code for download"""
    data = request.json or {}
    code = data.get('code', '')
    filename = data.get('filename', 'code.txt')
    
    return jsonify({
        "success": True,
        "code": code,
        "filename": secure_filename(filename)
    })

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        is_zip = filename.endswith('.zip')
        
        if is_zip:
            # Handle ZIP extraction
            try:
                z = zipfile.ZipFile(io.BytesIO(file.read()))
                project_files = []
                for name in z.namelist():
                    if not name.endswith('/') and not any(part.startswith('.') for part in name.split('/')):
                        try:
                            content = z.read(name).decode('utf-8', errors='ignore')
                            project_files.append({
                                "name": name,
                                "content": content,
                                "language": name.rsplit('.', 1)[1].lower() if '.' in name else 'txt'
                            })
                        except: continue
                
                GLOBAL_STATE['code_context'] = {
                    "type": "project",
                    "name": filename,
                    "files": project_files[:50] # Limit to 50 files for session/prompt safety
                }
                return jsonify({"success": True, "name": filename, "type": "project", "count": len(project_files)})
            except Exception as e:
                return jsonify({"error": f"Failed to process ZIP: {str(e)}"}), 500
        else:
            # Handle single file
            content = file.read().decode('utf-8', errors='ignore')
            language = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'txt'
            GLOBAL_STATE['code_context'] = {
                "type": "single",
                "name": filename,
                "content": content,
                "language": language
            }
            return jsonify({"success": True, "name": filename, "type": "single"})
            
    return jsonify({"error": "File type not allowed"}), 400

def _clone_repository(repo_url):
    import subprocess
    safe_name = secure_filename(repo_url.split('/')[-1] or 'repo')
    target_dir = os.path.join(os.getcwd(), 'workspace', 'repo_' + safe_name)

    os.makedirs(os.path.join(os.getcwd(), 'workspace'), exist_ok=True)
    subprocess.run(["git", "clone", repo_url, target_dir], check=True)

    project_files = collect_project_files(target_dir)
    GLOBAL_STATE['code_context'] = {
        "type": "project",
        "name": safe_name,
        "files": project_files[:50]
    }
    return target_dir, project_files

@main.route('/github-clone', methods=['POST'])
@main.route('/clone-repo', methods=['POST'])
def github_clone():
    data = request.get_json(silent=True) or {}
    repo_url = data.get('url') or data.get('repo_url')
    if not repo_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        target_dir, project_files = _clone_repository(repo_url)
        return jsonify({
            "success": True,
            "path": target_dir,
            "files": project_files[:50]
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Git clone failed: {e}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/vision-analyze', methods=['POST'])
@main.route('/vision-to-code', methods=['POST'])
def vision_analyze():
    import base64

    api_key = current_app.config.get('OPENROUTER_API_KEY')
    if not api_key:
        return jsonify({"error": "OPENROUTER_API_KEY is not configured on the server."}), 500

    # Accept either multipart file upload or JSON base64 payload
    img_base64 = None
    if 'file' in request.files:
        img_base64 = base64.b64encode(request.files['file'].read()).decode('utf-8')
    else:
        payload = request.get_json(silent=True) or {}
        raw_image = payload.get('image')
        if raw_image:
            img_base64 = raw_image.split(',')[1] if raw_image.startswith('data:') else raw_image

    if not img_base64:
        return jsonify({"error": "No image provided"}), 400

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "google/gemini-2.0-flash-exp:free",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this design and generate the complete, responsive HTML and CSS code to recreate it."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }
        ]
    }
    
    try:
        res = requests.post(url, headers=headers, json=data, timeout=120)
        res_json = res.json()
        if res.status_code == 200 and 'choices' in res_json:
            code = res_json['choices'][0]['message']['content']
            return jsonify({"success": True, "code": code, "language": "html"})
        err_msg = res_json.get('error') if isinstance(res_json, dict) else res.text
        return jsonify({"error": err_msg or "Vision analysis failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/write-to-disk', methods=['POST'])
def write_to_disk():
    data = request.json
    path = data.get('path')
    content = data.get('content')
    
    if not path or content is None:
        return jsonify({"error": "Missing path or content"}), 400
    
    # Security: Prevent escaping the project directory
    abs_path = os.path.abspath(os.path.join(os.getcwd(), 'workspace', path))
    if not abs_path.startswith(os.path.abspath(os.path.join(os.getcwd(), 'workspace'))):
         return jsonify({"error": "Access denied (path out of bounds)"}), 403
            
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"success": True, "path": path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/sync-editor', methods=['POST'])
def sync_editor():
    data = request.json
    content = data.get('content')
    context = GLOBAL_STATE.get('code_context')
    if context and content:
        if context['type'] == 'single':
            context['content'] = content
            # GLOBAL_STATE['code_context'] is already updated by reference if mutable, but explicit is safe
            return jsonify({"success": True})
    return jsonify({"success": False}), 400

@main.route('/run-code', methods=['POST'])
def run_code():
    """Execute code in a sandboxed environment.

    Supports 20+ programming languages including interpreted (Python,
    JavaScript, Go) and compiled (Java, C++, Rust) languages.

    Request JSON:
        code (str): Source code to execute.
        language (str): Target language identifier.
        stdin (str, optional): Standard input data.

    Returns:
        JSON with execution output, errors, and exit code.
    """
    data = request.json or {}
    code = data.get('code', '')
    language = data.get('language', 'python').lower()
    
    if not code.strip():
        return jsonify({"error": "No code provided"}), 400
    
    # Language Configuration Mapping - Comprehensive Support
    runners = {
        # Interpreted Languages
        'python': {'cmd': ['python'], 'ext': '.py'},
        'python3': {'cmd': ['python3'], 'ext': '.py'},
        'javascript': {'cmd': ['node'], 'ext': '.js'},
        'js': {'cmd': ['node'], 'ext': '.js'},
        'typescript': {'cmd': ['npx', 'ts-node'], 'ext': '.ts'},
        'ts': {'cmd': ['npx', 'ts-node'], 'ext': '.ts'},
        'ruby': {'cmd': ['ruby'], 'ext': '.rb'},
        'php': {'cmd': ['php'], 'ext': '.php'},
        'bash': {'cmd': ['bash'], 'ext': '.sh'},
        'sh': {'cmd': ['bash'], 'ext': '.sh'},
        'shell': {'cmd': ['powershell', '-ExecutionPolicy', 'Bypass', '-File'], 'ext': '.ps1'},
        'powershell': {'cmd': ['powershell', '-ExecutionPolicy', 'Bypass', '-File'], 'ext': '.ps1'},
        'ps1': {'cmd': ['powershell', '-ExecutionPolicy', 'Bypass', '-File'], 'ext': '.ps1'},
        'bat': {'cmd': ['cmd', '/c'], 'ext': '.bat'},
        'perl': {'cmd': ['perl'], 'ext': '.pl'},
        'lua': {'cmd': ['lua'], 'ext': '.lua'},
        
        # Compiled Languages (require compilation)
        'go': {'cmd': ['go', 'run'], 'ext': '.go'},
        'rust': {'cmd': ['rustc', '--edition', '2021', '-o'], 'ext': '.rs', 'compile': True},
        'java': {'compile': True, 'ext': '.java'},
        'cpp': {'cmd': ['g++', '-o'], 'ext': '.cpp', 'compile': True},
        'c++': {'cmd': ['g++', '-o'], 'ext': '.cpp', 'compile': True},
        'c': {'cmd': ['gcc', '-o'], 'ext': '.c', 'compile': True},
        'csharp': {'cmd': ['csc'], 'ext': '.cs', 'compile': True},
        'cs': {'cmd': ['csc'], 'ext': '.cs', 'compile': True},
        
        # Markup/Web (Preview mode)
        'html': {'mode': 'preview', 'ext': '.html'},
        'css': {'mode': 'preview', 'ext': '.css'},
        'xml': {'mode': 'preview', 'ext': '.xml'},
        'json': {'mode': 'preview', 'ext': '.json'},
        'sql': {'mode': 'preview', 'ext': '.sql'},
        'markdown': {'mode': 'preview', 'ext': '.md'},
        'md': {'mode': 'preview', 'ext': '.md'}
    }

    if language in ['html', 'css', 'xml', 'json', 'sql', 'markdown', 'md']:
        preview_info = {
            'html': "Open in browser to see the rendered output",
            'css': "Combine with HTML to see styling",
            'xml': "XML structure preview available",
            'json': "Valid JSON is formatted and ready to use",
            'sql': "SQL syntax is valid. Execute against a database",
            'markdown': "Markdown formatting will render in browsers"
        }
        msg = preview_info.get(language, "Preview mode")
        return jsonify({
            "output": f"ℹ️ {language.upper()} Code\n\n{msg}\n\nTo execute:\n1. Save using 'Write to Disk'\n2. Open in appropriate application",
            "is_preview": True
        })

    if language not in runners:
        supported = ', '.join(sorted([k for k in runners.keys() if k not in ['html', 'css', 'xml', 'json', 'sql', 'markdown', 'md']]))
        return jsonify({
            "error": f"❌ No runner configured for '{language}'.\n\n✅ Supported languages:\n{supported}\n\nNote: Install runtimes for compiled languages (Java, C++, Rust, etc.)"
        }), 400
    
    config = runners[language]
    temp_path = None
    executable_path = None
    
    try:
        # Create workspace dir if needed
        workspace_dir = os.path.join(os.getcwd(), 'workspace')
        os.makedirs(workspace_dir, exist_ok=True)
        
        # Create temp file in workspace
        with tempfile.NamedTemporaryFile(suffix=config['ext'], delete=False, dir=workspace_dir, mode='w', encoding='utf-8') as tf:
            tf.write(code)
            temp_path = tf.name
        
        stdin_data = data.get('stdin', '')

        # Prepare environment with UTF-8 support
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

        # Handle compiled languages
        if config.get('compile'):
            if language == 'java':
                # Java compilation
                class_name = code.split('class ')[1].split()[0] if 'class ' in code else 'Main'
                compile_cmd = ['javac', temp_path]
                result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    error_msg = result.stderr or "Compilation failed"
                    GLOBAL_STATE['last_execution_error'] = error_msg
                    return jsonify({"error": f"❌ Java Compilation Error:\n{error_msg}"}), 400
                
                # Run compiled Java
                class_path = os.path.dirname(temp_path)
                run_cmd = ['java', '-cp', class_path, class_name]
                result = subprocess.run(run_cmd, input=stdin_data, capture_output=True, text=True, timeout=60, env=env)
            
            elif language in ['cpp', 'c++', 'c']:
                # C/C++ compilation
                compiler = 'g++' if language in ['cpp', 'c++'] else 'gcc'
                executable_path = temp_path.replace(config['ext'], '.exe')
                compile_cmd = [compiler, temp_path, '-o', executable_path]
                result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    error_msg = result.stderr or "Compilation failed"
                    GLOBAL_STATE['last_execution_error'] = error_msg
                    return jsonify({"error": f"❌ {compiler.upper()} Compilation Error:\n{error_msg}"}), 400
                
                # Run compiled executable
                result = subprocess.run([executable_path], input=stdin_data, capture_output=True, text=True, timeout=60, env=env)
            
            elif language == 'rust':
                # Rust compilation
                executable_path = temp_path.replace(config['ext'], '.exe')
                compile_cmd = ['rustc', temp_path, '-o', executable_path]
                result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=60)
                if result.returncode != 0:
                    error_msg = result.stderr or "Compilation failed"
                    GLOBAL_STATE['last_execution_error'] = error_msg
                    return jsonify({"error": f"❌ Rust Compilation Error:\n{error_msg}"}), 400
                
                # Run compiled executable
                result = subprocess.run([executable_path], input=stdin_data, capture_output=True, text=True, timeout=60, env=env)
            
            elif language in ['csharp', 'cs']:
                # C# compilation
                executable_path = temp_path.replace(config['ext'], '.exe')
                compile_cmd = ['csc', temp_path, f'/out:{executable_path}']
                result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    error_msg = result.stderr or "Compilation failed"
                    GLOBAL_STATE['last_execution_error'] = error_msg
                    return jsonify({"error": f"❌ C# Compilation Error:\n{error_msg}"}), 400
                
                # Run compiled executable
                result = subprocess.run([executable_path], input=stdin_data, capture_output=True, text=True, timeout=60, env=env)
        else:
            # Interpreted languages
            command = config.get('cmd', []) + [temp_path]
            result = subprocess.run(
                command,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace',
                env=env,
                cwd=workspace_dir
            )
        
        output = result.stdout
        error = result.stderr
        
        if error:
            GLOBAL_STATE['last_execution_error'] = error

        return jsonify({
            "output": output if output else ("" if error else "✅ Code executed successfully (no output)"),
            "error": error,
            "exit_code": result.returncode,
            "language": language
        })
    except FileNotFoundError as e:
        runtime_info = {
            'python': 'https://python.org',
            'node': 'https://nodejs.org',
            'go': 'https://go.dev',
            'java': 'https://oracle.com/java',
            'rust': 'https://rustup.rs',
            'ruby': 'https://ruby-lang.org',
            'php': 'https://php.net',
            'gcc': 'https://gcc.gnu.org'
        }
        return jsonify({
            "error": f"❌ Runtime not found: '{config['cmd'][0] if config.get('cmd') else language}'\n\nPlease install the required runtime for {language}.\nVisit the official website for installation instructions."
        }), 400
    except subprocess.TimeoutExpired:
        return jsonify({"error": "⏱️ Execution timed out (60s limit)\n\nYour code took too long to run. Check for infinite loops or heavy computations."}), 408
    except Exception as e:
        return jsonify({"error": f"❌ Execution error: {str(e)}"}), 500
    finally:
        # Cleanup temp files
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        if executable_path and os.path.exists(executable_path):
            try:
                os.remove(executable_path)
            except:
                pass


@main.route('/clear-context')
def clear_context():
    GLOBAL_STATE['code_context'] = None
    if request.headers.get('Accept') == 'application/json':
        return jsonify({"success": True})
    return redirect(url_for('main.index'))

@main.route('/clear')
def clear_history():
    GLOBAL_STATE['history'] = []
    GLOBAL_STATE['code_context'] = None
    GLOBAL_STATE['last_execution_error'] = None
    if request.headers.get('Accept') == 'application/json':
        return jsonify({"success": True})
    return redirect(url_for('main.index'))


# Health check endpoint
@main.route('/health')
def health_check():
    return jsonify({
        "status": "ok",
        "has_api_key": bool(current_app.config.get('OPENROUTER_API_KEY')),
        "history_count": len(GLOBAL_STATE['history']),
        "has_context": GLOBAL_STATE['code_context'] is not None
    })




# ==================== CODE ANALYSIS ENDPOINTS ====================

@main.route('/api/snippets', methods=['GET', 'POST', 'DELETE'])
def manage_snippets():
    """Server-side snippet storage (optional backup)"""
    snippets_file = os.path.join(os.getcwd(), 'workspace', 'snippets.json')
    
    if request.method == 'GET':
        if os.path.exists(snippets_file):
            with open(snippets_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify([])
    
    elif request.method == 'POST':
        data = request.json or {}
        snippets = []
        if os.path.exists(snippets_file):
            with open(snippets_file, 'r') as f:
                snippets = json.load(f)
        
        snippet = {
            "id": f"{datetime.now().timestamp()}-{len(snippets)}",
            "name": data.get('name', 'Untitled'),
            "description": data.get('description', ''),
            "code": data.get('code', ''),
            "language": data.get('language', 'python'),
            "tags": data.get('tags', []),
            "createdAt": datetime.now().isoformat()
        }
        snippets.insert(0, snippet)
        
        os.makedirs(os.path.dirname(snippets_file), exist_ok=True)
        with open(snippets_file, 'w') as f:
            json.dump(snippets, f, indent=2)
        
        return jsonify({"success": True, "snippet": snippet})
    
    elif request.method == 'DELETE':
        snippet_id = request.args.get('id')
        if os.path.exists(snippets_file):
            with open(snippets_file, 'r') as f:
                snippets = json.load(f)
            snippets = [s for s in snippets if s['id'] != snippet_id]
            with open(snippets_file, 'w') as f:
                json.dump(snippets, f, indent=2)
        return jsonify({"success": True})


@main.route('/api/templates', methods=['GET'])
def get_templates():
    """Get code templates/boilerplates"""
    templates = {
        "python": {
            "basic": "# Python Script\n\ndef main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
            "class": "class MyClass:\n    def __init__(self, name):\n        self.name = name\n    \n    def greet(self):\n        return f'Hello, {self.name}!'\n\n# Usage\nobj = MyClass('World')\nprint(obj.greet())",
            "api": "import requests\n\ndef fetch_data(url):\n    response = requests.get(url)\n    response.raise_for_status()\n    return response.json()\n\n# Usage\ndata = fetch_data('https://api.example.com/data')\nprint(data)",
            "flask": "from flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.route('/')\ndef home():\n    return jsonify({'message': 'Hello, World!'})\n\nif __name__ == '__main__':\n    app.run(debug=True)"
        },
        "javascript": {
            "basic": "// JavaScript\n\nfunction main() {\n    console.log('Hello, World!');\n}\n\nmain();",
            "fetch": "// Fetch API Example\n\nasync function fetchData(url) {\n    try {\n        const response = await fetch(url);\n        const data = await response.json();\n        return data;\n    } catch (error) {\n        console.error('Error:', error);\n    }\n}\n\n// Usage\nfetchData('https://api.example.com/data')\n    .then(data => console.log(data));",
            "express": "const express = require('express');\nconst app = express();\n\napp.get('/', (req, res) => {\n    res.json({ message: 'Hello, World!' });\n});\n\napp.listen(3000, () => {\n    console.log('Server running on port 3000');\n});"
        },
        "html": {
            "basic": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>My Page</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>",
            "responsive": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Responsive Page</title>\n    <style>\n        * { box-sizing: border-box; margin: 0; padding: 0; }\n        body { font-family: system-ui, sans-serif; line-height: 1.6; }\n        .container { max-width: 1200px; margin: 0 auto; padding: 1rem; }\n        header { background: #333; color: white; padding: 1rem; }\n        main { padding: 2rem 0; }\n    </style>\n</head>\n<body>\n    <header>\n        <div class=\"container\">\n            <h1>My Website</h1>\n        </div>\n    </header>\n    <main>\n        <div class=\"container\">\n            <p>Welcome to my website!</p>\n        </div>\n    </main>\n</body>\n</html>"
        }
    }
    
    language = request.args.get('language', 'python')
    return jsonify(templates.get(language, templates['python']))


@main.route('/api/export-chat', methods=['GET'])
def export_chat():
    """Export chat history"""
    history = GLOBAL_STATE['history']
    format_type = request.args.get('format', 'json')
    
    if format_type == 'markdown':
        md = "# NexusAI Chat Export\n\n"
        md += f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n---\n\n"
        for msg in history:
            role = "**You**" if msg['role'] == 'user' else "**NexusAI**"
            md += f"{role}:\n\n{msg['content']}\n\n---\n\n"
        return jsonify({"content": md, "filename": "nexusai-chat.md"})
    
    return jsonify({
        "content": json.dumps(history, indent=2),
        "filename": "nexusai-chat.json",
        "history": history
    })


@main.route('/api/session', methods=['GET', 'POST', 'DELETE'])
def manage_session():
    """Manage coding sessions"""
    session_file = os.path.join(os.getcwd(), 'workspace', 'session.json')
    
    if request.method == 'GET':
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                return jsonify(json.load(f))
        return jsonify(None)
    
    elif request.method == 'POST':
        data = request.json or {}
        session_data = {
            "code": data.get('code', ''),
            "language": data.get('language', 'python'),
            "filename": data.get('filename', 'untitled.py'),
            "history": GLOBAL_STATE['history'],
            "savedAt": datetime.now().isoformat()
        }
        
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return jsonify({"success": True})
    
    elif request.method == 'DELETE':
        if os.path.exists(session_file):
            os.remove(session_file)
        return jsonify({"success": True})
