/**
 * NexusAI - Professional Code Assistant
 * Main Application JavaScript
 */

// ==================== GLOBAL STATE ====================
const NexusAI = {
    version: '2.0.0',
    editor: null,
    settings: {
        theme: localStorage.getItem('nexus-theme') || 'dark',
        fontSize: parseInt(localStorage.getItem('nexus-font-size')) || 14,
        autoSave: localStorage.getItem('nexus-auto-save') !== 'false',
        soundEnabled: localStorage.getItem('nexus-sound') !== 'false'
    },
    state: {
        isProcessing: false,
        currentFile: null,
        chatHistory: [],
        executionHistory: []
    }
};

// ==================== UTILITIES ====================
const Utils = {
    // Generate unique ID
    generateId: () => `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    
    // Escape HTML
    escapeHtml: (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    
    // Format timestamp
    formatTime: (date = new Date()) => {
        return date.toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    },
    
    // Format file size
    formatBytes: (bytes) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Copy to clipboard
    copyToClipboard: async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            // Fallback for older browsers
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            const success = document.execCommand('copy');
            document.body.removeChild(textarea);
            return success;
        }
    },
    
    // Download file
    downloadFile: (content, filename, type = 'text/plain') => {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    },
    
    // Debounce function
    debounce: (func, wait) => {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // Get language from filename
    getLanguageFromFilename: (filename) => {
        const ext = filename.split('.').pop().toLowerCase();
        const langMap = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'jsx': 'javascript',
            'tsx': 'typescript',
            'html': 'html',
            'css': 'css',
            'scss': 'scss',
            'json': 'json',
            'md': 'markdown',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'cs': 'csharp',
            'go': 'go',
            'rs': 'rust',
            'rb': 'ruby',
            'php': 'php',
            'sql': 'sql',
            'yaml': 'yaml',
            'yml': 'yaml',
            'xml': 'xml',
            'sh': 'shell',
            'bash': 'shell',
            'ps1': 'powershell',
            'vue': 'vue'
        };
        return langMap[ext] || 'plaintext';
    }
};

// ==================== TOAST NOTIFICATIONS ====================
const Toast = {
    container: null,
    
    init: () => {
        Toast.container = document.getElementById('toast-container');
        if (!Toast.container) {
            Toast.container = document.createElement('div');
            Toast.container.id = 'toast-container';
            Toast.container.className = 'toast-container';
            document.body.appendChild(Toast.container);
        }
    },
    
    show: (message, type = 'info', duration = 3000) => {
        if (!Toast.container) Toast.init();
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${Utils.escapeHtml(message)}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        
        Toast.container.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => toast.classList.add('show'));
        
        // Auto remove
        if (duration > 0) {
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 300);
            }, duration);
        }
        
        return toast;
    },
    
    success: (msg, duration) => Toast.show(msg, 'success', duration),
    error: (msg, duration) => Toast.show(msg, 'error', duration),
    warning: (msg, duration) => Toast.show(msg, 'warning', duration),
    info: (msg, duration) => Toast.show(msg, 'info', duration)
};

// ==================== API CLIENT ====================
const API = {
    baseUrl: '',
    
    // Generic request handler
    request: async (endpoint, options = {}) => {
        const url = API.baseUrl + endpoint;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },
    
    // Health check
    health: () => API.request('/health'),
    
    // Upload file
    uploadFile: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        return fetch('/upload', {
            method: 'POST',
            body: formData
        }).then(r => r.json());
    },
    
    // Run code
    runCode: (code, language, stdin = '') => {
        return API.request('/run-code', {
            method: 'POST',
            body: JSON.stringify({ code, language, stdin })
        });
    },
    
    // Format code
    formatCode: (code, language) => {
        return API.request('/api/format-code', {
            method: 'POST',
            body: JSON.stringify({ code, language })
        });
    },
    
    // Analyze code
    analyzeCode: (code, language) => {
        return API.request('/api/analyze-code', {
            method: 'POST',
            body: JSON.stringify({ code, language })
        });
    },
    
    // Check syntax
    syntaxCheck: (code, language) => {
        return API.request('/api/syntax-check', {
            method: 'POST',
            body: JSON.stringify({ code, language })
        });
    },
    
    // Get all supported languages
    getLanguages: () => API.request('/api/languages'),
    
    // Clear context
    clearContext: () => {
        return fetch('/clear-context', {
            headers: { 'Accept': 'application/json' }
        }).then(r => r.json());
    },
    
    // Clear all
    clearAll: () => {
        return fetch('/clear', {
            headers: { 'Accept': 'application/json' }
        }).then(r => r.json());
    },
    
    // Get context info
    getContext: () => API.request('/api/context'),
    
    // Get available models
    getModels: () => API.request('/api/models'),
    
    // Write to disk
    writeToDisk: (path, content) => {
        return API.request('/write-to-disk', {
            method: 'POST',
            body: JSON.stringify({ path, content })
        });
    },
    
    // Sync editor content
    syncEditor: (content) => {
        return API.request('/sync-editor', {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }
};

// ==================== MARKDOWN RENDERER ====================
const MarkdownRenderer = {
    // Render markdown with code highlighting
    render: (text) => {
        if (typeof marked === 'undefined') {
            return Utils.escapeHtml(text).replace(/\n/g, '<br>');
        }
        
        // Configure marked
        marked.setOptions({
            highlight: function(code, lang) {
                if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (e) {}
                }
                return code;
            },
            breaks: true,
            gfm: true
        });
        
        return marked.parse(text);
    },
    
    // Add copy buttons to code blocks
    addCopyButtons: (container) => {
        container.querySelectorAll('pre code').forEach((block, index) => {
            if (block.parentElement.querySelector('.copy-btn')) return;
            
            const wrapper = document.createElement('div');
            wrapper.className = 'code-block-wrapper';
            block.parentElement.insertBefore(wrapper, block.parentElement.firstChild);
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy';
            copyBtn.onclick = async () => {
                const success = await Utils.copyToClipboard(block.textContent);
                if (success) {
                    copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6L9 17l-5-5"/></svg> Copied!';
                    setTimeout(() => {
                        copyBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy';
                    }, 2000);
                }
            };
            
            wrapper.appendChild(copyBtn);
        });
    }
};

// ==================== EDITOR MANAGER ====================
const EditorManager = {
    instance: null,
    
    init: (containerId, options = {}) => {
        if (typeof monaco === 'undefined') {
            console.warn('Monaco Editor not loaded');
            return null;
        }
        
        const container = document.getElementById(containerId);
        if (!container) return null;
        
        const defaultOptions = {
            value: options.value || '# Welcome to NexusAI\n# Write or paste your code here\n\nprint("Hello, World!")',
            language: options.language || 'python',
            theme: NexusAI.settings.theme === 'dark' ? 'vs-dark' : 'vs',
            fontSize: NexusAI.settings.fontSize,
            minimap: { enabled: true },
            automaticLayout: true,
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            lineNumbers: 'on',
            glyphMargin: true,
            folding: true,
            formatOnPaste: true,
            formatOnType: true,
            tabSize: 4,
            insertSpaces: true,
            renderWhitespace: 'selection',
            bracketPairColorization: { enabled: true },
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            padding: { top: 10, bottom: 10 }
        };
        
        EditorManager.instance = monaco.editor.create(container, defaultOptions);
        NexusAI.editor = EditorManager.instance;
        
        // Auto-save on change
        if (NexusAI.settings.autoSave) {
            EditorManager.instance.onDidChangeModelContent(
                Utils.debounce(() => {
                    API.syncEditor(EditorManager.instance.getValue()).catch(() => {});
                }, 1000)
            );
        }
        
        return EditorManager.instance;
    },
    
    getValue: () => EditorManager.instance?.getValue() || (window.editor?.getValue?.()) || '',
    
    setValue: (value) => {
        const ed = EditorManager.instance || window.editor;
        if (ed) {
            ed.setValue(value);
        }
    },
    
    setLanguage: (language) => {
        const ed = EditorManager.instance || window.editor;
        if (ed && typeof monaco !== 'undefined') {
            monaco.editor.setModelLanguage(ed.getModel(), language);
        }
    },
    
    setTheme: (theme) => {
        if (typeof monaco !== 'undefined') {
            monaco.editor.setTheme(theme === 'dark' ? 'vs-dark' : 'vs');
        }
    },
    
    format: () => {
        const ed = EditorManager.instance || window.editor;
        if (ed) {
            ed.getAction('editor.action.formatDocument')?.run();
        }
    },
    
    focus: () => {
        const ed = EditorManager.instance || window.editor;
        if (ed) {
            ed.focus();
        }
    }
};

// ==================== KEYBOARD SHORTCUTS ====================
const Shortcuts = {
    bindings: {},
    
    init: () => {
        document.addEventListener('keydown', (e) => {
            const key = Shortcuts.getKeyString(e);
            const binding = Shortcuts.bindings[key];
            
            if (binding && !Shortcuts.isInputFocused(e.target)) {
                e.preventDefault();
                binding.handler(e);
            }
        });
    },
    
    getKeyString: (e) => {
        const parts = [];
        if (e.ctrlKey || e.metaKey) parts.push('ctrl');
        if (e.shiftKey) parts.push('shift');
        if (e.altKey) parts.push('alt');
        parts.push(e.key.toLowerCase());
        return parts.join('+');
    },
    
    isInputFocused: (target) => {
        const tagName = target.tagName.toLowerCase();
        return tagName === 'input' || tagName === 'textarea' || target.isContentEditable;
    },
    
    register: (shortcut, description, handler) => {
        Shortcuts.bindings[shortcut.toLowerCase()] = { description, handler };
    },
    
    unregister: (shortcut) => {
        delete Shortcuts.bindings[shortcut.toLowerCase()];
    },
    
    getAll: () => {
        return Object.entries(Shortcuts.bindings).map(([key, value]) => ({
            shortcut: key,
            description: value.description
        }));
    }
};

// ==================== SETTINGS MANAGER ====================
const Settings = {
    modal: null,
    
    init: () => {
        Settings.applyTheme(NexusAI.settings.theme);
    },
    
    save: () => {
        Object.entries(NexusAI.settings).forEach(([key, value]) => {
            localStorage.setItem(`nexus-${key.replace(/([A-Z])/g, '-$1').toLowerCase()}`, value);
        });
    },
    
    applyTheme: (theme) => {
        document.body.classList.remove('theme-light', 'theme-dark');
        document.body.classList.add(`theme-${theme}`);
        NexusAI.settings.theme = theme;
        EditorManager.setTheme(theme);
        Settings.save();
    },
    
    setFontSize: (size) => {
        NexusAI.settings.fontSize = size;
        const ed = EditorManager.instance || window.editor;
        if (ed) {
            ed.updateOptions({ fontSize: size });
        }
        Settings.save();
    },
    
    toggleAutoSave: (enabled) => {
        NexusAI.settings.autoSave = enabled;
        Settings.save();
    }
};

// ==================== COMMAND PALETTE ====================
const CommandPalette = {
    overlay: null,
    searchInput: null,
    commandList: null,
    selectedIndex: 0,
    filteredCommands: [],
    
    commands: [
        { id: 'newFile', name: 'New File', icon: '📄', shortcut: 'Ctrl+N', group: 'File' },
        { id: 'openFile', name: 'Open File', icon: '📂', shortcut: 'Ctrl+O', group: 'File' },
        { id: 'saveFile', name: 'Save File', icon: '💾', shortcut: 'Ctrl+S', group: 'File' },
        { id: 'downloadCode', name: 'Download Code', icon: '⬇️', group: 'File' },
        { id: 'runCode', name: 'Run Code', icon: '▶️', shortcut: 'Ctrl+Enter', group: 'Code' },
        { id: 'formatCode', name: 'Format Code', icon: '✨', shortcut: 'Shift+Alt+F', group: 'Code' },
        { id: 'analyzeCode', name: 'Analyze Code', icon: '📊', group: 'Code' },
        { id: 'syntaxCheck', name: 'Check Syntax', icon: '✓', group: 'Code' },
        { id: 'toggleMinimap', name: 'Toggle Minimap', icon: '🗺️', group: 'Code' },
        { id: 'toggleWordWrap', name: 'Toggle Word Wrap', icon: '↩️', group: 'Code' },
        { id: 'askAI', name: 'Ask AI', icon: '🤖', shortcut: 'Ctrl+/', group: 'AI' },
        { id: 'explainCode', name: 'Explain Code', icon: '💡', group: 'AI' },
        { id: 'debugCode', name: 'Debug Code', icon: '🐛', group: 'AI' },
        { id: 'generateTests', name: 'Generate Tests', icon: '🧪', group: 'AI' },
        { id: 'optimizeCode', name: 'Optimize Code', icon: '⚡', group: 'AI' },
        { id: 'refactorCode', name: 'Refactor Code', icon: '🔄', group: 'AI' },
        { id: 'findBugs', name: 'Find Bugs', icon: '🐛', group: 'AI' },
        { id: 'improvePerformance', name: 'Improve Performance', icon: '🚀', group: 'AI' },
        { id: 'toggleTheme', name: 'Toggle Theme', icon: '🌓', group: 'View' },
        { id: 'openSettings', name: 'Open Settings', icon: '⚙️', group: 'View' },
        { id: 'showShortcuts', name: 'Keyboard Shortcuts', icon: '⌨️', group: 'View' },
        { id: 'showMetrics', name: 'Code Metrics', icon: '📊', group: 'View' },
        { id: 'saveSnippet', name: 'Save as Snippet', icon: '📌', group: 'Snippets' },
        { id: 'browseSnippets', name: 'Browse Snippets', icon: '📚', group: 'Snippets' },
        { id: 'togglePreview', name: 'Toggle Live Preview', icon: '👁️', group: 'View' },
    ],
    
    init: () => {
        CommandPalette.overlay = document.getElementById('command-palette-overlay');
        CommandPalette.searchInput = document.getElementById('command-search');
        CommandPalette.commandList = document.getElementById('command-list');
        
        if (!CommandPalette.overlay) return;
        
        // Search filter
        CommandPalette.searchInput?.addEventListener('input', (e) => {
            CommandPalette.filter(e.target.value);
        });
        
        // Keyboard navigation
        CommandPalette.searchInput?.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                CommandPalette.selectNext();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                CommandPalette.selectPrev();
            } else if (e.key === 'Enter') {
                e.preventDefault();
                CommandPalette.executeSelected();
            } else if (e.key === 'Escape') {
                CommandPalette.hide();
            }
        });
        
        // Click outside to close
        CommandPalette.overlay?.addEventListener('click', (e) => {
            if (e.target === CommandPalette.overlay) {
                CommandPalette.hide();
            }
        });
        
        // Command item clicks
        CommandPalette.commandList?.addEventListener('click', (e) => {
            const item = e.target.closest('.command-item');
            if (item) {
                CommandPalette.execute(item.dataset.command);
            }
        });
    },
    
    show: () => {
        if (!CommandPalette.overlay) return;
        CommandPalette.overlay.classList.remove('hidden');
        CommandPalette.searchInput.value = '';
        CommandPalette.searchInput.focus();
        CommandPalette.filter('');
    },
    
    hide: () => {
        CommandPalette.overlay?.classList.add('hidden');
    },
    
    filter: (query) => {
        const items = CommandPalette.commandList?.querySelectorAll('.command-item');
        const q = query.toLowerCase();
        
        items?.forEach(item => {
            const text = item.textContent.toLowerCase();
            const match = !q || text.includes(q);
            item.style.display = match ? '' : 'none';
        });
        
        // Show/hide groups
        const groups = CommandPalette.commandList?.querySelectorAll('.command-group');
        groups?.forEach(group => {
            const visibleItems = group.querySelectorAll('.command-item:not([style*="display: none"])');
            group.style.display = visibleItems.length > 0 ? '' : 'none';
        });
    },
    
    selectNext: () => {
        const items = Array.from(CommandPalette.commandList?.querySelectorAll('.command-item:not([style*="display: none"])') || []);
        const current = CommandPalette.commandList?.querySelector('.command-item.selected');
        let idx = items.indexOf(current);
        items.forEach(i => i.classList.remove('selected'));
        idx = Math.min(idx + 1, items.length - 1);
        items[idx]?.classList.add('selected');
        items[idx]?.scrollIntoView({ block: 'nearest' });
    },
    
    selectPrev: () => {
        const items = Array.from(CommandPalette.commandList?.querySelectorAll('.command-item:not([style*="display: none"])') || []);
        const current = CommandPalette.commandList?.querySelector('.command-item.selected');
        let idx = items.indexOf(current);
        items.forEach(i => i.classList.remove('selected'));
        idx = Math.max(idx - 1, 0);
        items[idx]?.classList.add('selected');
        items[idx]?.scrollIntoView({ block: 'nearest' });
    },
    
    executeSelected: () => {
        const selected = CommandPalette.commandList?.querySelector('.command-item.selected') ||
                        CommandPalette.commandList?.querySelector('.command-item:not([style*="display: none"])');
        if (selected) {
            CommandPalette.execute(selected.dataset.command);
        }
    },
    
    execute: (commandId) => {
        CommandPalette.hide();
        
        const getEditor = () => EditorManager.instance || window.editor;
        
        const handlers = {
            newFile: () => {
                const ed = getEditor();
                if (ed) {
                    ed.setValue('');
                    NexusAI.state.currentFile = 'untitled.py';
                    document.getElementById('current-filename')?.textContent && 
                        (document.getElementById('current-filename').textContent = 'untitled.py');
                }
                Toast.info('New file created');
            },
            openFile: () => document.getElementById('file-input')?.click(),
            saveFile: () => {
                Utils.downloadFile(EditorManager.getValue(), NexusAI.state.currentFile || 'code.txt');
                Toast.success('File saved!');
            },
            downloadCode: () => {
                Utils.downloadFile(EditorManager.getValue(), NexusAI.state.currentFile || 'code.txt');
                Toast.success('Code downloaded!');
            },
            runCode: () => document.getElementById('run-btn')?.click(),
            formatCode: () => EditorManager.format(),
            toggleMinimap: () => {
                const ed = getEditor();
                if (!ed) return;
                const current = ed.getOption(monaco.editor.EditorOption.minimap);
                ed.updateOptions({ minimap: { enabled: !current?.enabled } });
                Toast.info(`Minimap ${current?.enabled ? 'hidden' : 'shown'}`);
            },
            toggleWordWrap: () => {
                const ed = getEditor();
                if (!ed) return;
                const current = ed.getOption(monaco.editor.EditorOption.wordWrap);
                const newValue = current === 'on' ? 'off' : 'on';
                ed.updateOptions({ wordWrap: newValue });
                Toast.info(`Word wrap ${newValue}`);
            },
            askAI: () => document.getElementById('user-input')?.focus(),
            explainCode: () => CommandPalette.triggerAIAction('Explain this code in detail'),
            debugCode: () => CommandPalette.triggerAIAction('Find bugs and issues in this code'),
            generateTests: () => CommandPalette.triggerAIAction('Generate unit tests for this code'),
            optimizeCode: () => CommandPalette.triggerAIAction('Optimize this code for better performance'),
            toggleTheme: () => {
                const newTheme = NexusAI.settings.theme === 'dark' ? 'light' : 'dark';
                Settings.applyTheme(newTheme);
                Toast.info(`Theme: ${newTheme}`);
            },
            openSettings: () => document.getElementById('settings-overlay')?.classList.remove('hidden'),
            showShortcuts: () => document.getElementById('shortcuts-overlay')?.classList.remove('hidden'),
            showMetrics: () => CodeMetrics.show(),
            saveSnippet: () => SnippetManager.showSaveModal(),
            browseSnippets: () => SnippetManager.show(),
            togglePreview: () => LivePreview.toggle(),
        };
        
        handlers[commandId]?.();
    },
    
    triggerAIAction: (prompt) => {
        const input = document.getElementById('user-input');
        if (input) {
            input.value = prompt;
            document.getElementById('chat-form')?.dispatchEvent(new Event('submit'));
        }
    }
};

// ==================== CODE METRICS ====================
const CodeMetrics = {
    overlay: null,
    
    init: () => {
        CodeMetrics.overlay = document.getElementById('metrics-overlay');
        document.getElementById('close-metrics-btn')?.addEventListener('click', CodeMetrics.hide);
        CodeMetrics.overlay?.addEventListener('click', (e) => {
            if (e.target === CodeMetrics.overlay) CodeMetrics.hide();
        });
    },
    
    show: () => {
        const code = EditorManager.getValue();
        const language = document.getElementById('language-select')?.value || 'python';
        
        CodeMetrics.analyze(code, language);
        CodeMetrics.overlay?.classList.remove('hidden');
    },
    
    hide: () => {
        CodeMetrics.overlay?.classList.add('hidden');
    },
    
    analyze: (code, language) => {
        const lines = code.split('\n');
        const nonBlankLines = lines.filter(l => l.trim().length > 0);
        const blankLines = lines.length - nonBlankLines.length;
        
        // Count comments based on language
        const commentPatterns = {
            python: /^\s*#/,
            javascript: /^\s*(\/\/|\/\*|\*)/,
            html: /^\s*<!--/,
            css: /^\s*\/\*/,
        };
        const pattern = commentPatterns[language] || commentPatterns.python;
        const comments = lines.filter(l => pattern.test(l)).length;
        
        // Count functions
        const funcPatterns = {
            python: /def\s+\w+\s*\(/g,
            javascript: /(function\s+\w+|const\s+\w+\s*=\s*(?:async\s*)?\(|=>\s*{)/g,
            java: /(public|private|protected)\s+\w+\s+\w+\s*\(/g,
        };
        const funcPattern = funcPatterns[language] || funcPatterns.python;
        const functions = (code.match(funcPattern) || []).length;
        
        // Complexity (simplified - based on control structures)
        const complexityKeywords = /\b(if|else|elif|for|while|switch|case|try|catch|except)\b/g;
        const complexityScore = (code.match(complexityKeywords) || []).length;
        const complexityLabel = complexityScore < 5 ? 'Low' : complexityScore < 15 ? 'Medium' : 'High';
        
        // Update UI
        document.getElementById('metric-lines').textContent = nonBlankLines.length;
        document.getElementById('metric-chars').textContent = code.length.toLocaleString();
        document.getElementById('metric-words').textContent = code.split(/\s+/).filter(w => w).length;
        document.getElementById('metric-functions').textContent = functions;
        document.getElementById('metric-language').textContent = language.charAt(0).toUpperCase() + language.slice(1);
        document.getElementById('metric-blank').textContent = blankLines;
        document.getElementById('metric-comments').textContent = comments;
        document.getElementById('metric-complexity').textContent = complexityLabel;
    }
};

// ==================== SNIPPET MANAGER ====================
const SnippetManager = {
    overlay: null,
    saveOverlay: null,
    snippets: [],
    
    init: () => {
        SnippetManager.overlay = document.getElementById('snippets-overlay');
        SnippetManager.saveOverlay = document.getElementById('save-snippet-overlay');
        
        // Load from localStorage
        SnippetManager.snippets = JSON.parse(localStorage.getItem('nexus-snippets') || '[]');
        
        // Event listeners
        document.getElementById('close-snippets-btn')?.addEventListener('click', SnippetManager.hide);
        document.getElementById('close-save-snippet-btn')?.addEventListener('click', SnippetManager.hideSaveModal);
        document.getElementById('cancel-snippet-btn')?.addEventListener('click', SnippetManager.hideSaveModal);
        document.getElementById('confirm-save-snippet-btn')?.addEventListener('click', SnippetManager.save);
        document.getElementById('add-snippet-btn')?.addEventListener('click', SnippetManager.showSaveModal);
        document.getElementById('snippet-search')?.addEventListener('input', (e) => SnippetManager.filter(e.target.value));
        
        SnippetManager.overlay?.addEventListener('click', (e) => {
            if (e.target === SnippetManager.overlay) SnippetManager.hide();
        });
        SnippetManager.saveOverlay?.addEventListener('click', (e) => {
            if (e.target === SnippetManager.saveOverlay) SnippetManager.hideSaveModal();
        });
    },
    
    show: () => {
        SnippetManager.render();
        SnippetManager.overlay?.classList.remove('hidden');
    },
    
    hide: () => {
        SnippetManager.overlay?.classList.add('hidden');
    },
    
    showSaveModal: () => {
        document.getElementById('snippet-name').value = '';
        document.getElementById('snippet-description').value = '';
        document.getElementById('snippet-tags').value = '';
        SnippetManager.saveOverlay?.classList.remove('hidden');
        document.getElementById('snippet-name')?.focus();
    },
    
    hideSaveModal: () => {
        SnippetManager.saveOverlay?.classList.add('hidden');
    },
    
    save: () => {
        const name = document.getElementById('snippet-name')?.value.trim();
        const description = document.getElementById('snippet-description')?.value.trim();
        const tags = document.getElementById('snippet-tags')?.value.split(',').map(t => t.trim()).filter(t => t);
        const code = EditorManager.getValue();
        const language = document.getElementById('language-select')?.value || 'python';
        
        if (!name) {
            Toast.error('Please enter a name');
            return;
        }
        
        const snippet = {
            id: Utils.generateId(),
            name,
            description,
            tags,
            code,
            language,
            createdAt: new Date().toISOString()
        };
        
        SnippetManager.snippets.unshift(snippet);
        localStorage.setItem('nexus-snippets', JSON.stringify(SnippetManager.snippets));
        
        Toast.success('Snippet saved!');
        SnippetManager.hideSaveModal();
        SnippetManager.render();
    },
    
    delete: (id) => {
        SnippetManager.snippets = SnippetManager.snippets.filter(s => s.id !== id);
        localStorage.setItem('nexus-snippets', JSON.stringify(SnippetManager.snippets));
        SnippetManager.render();
        Toast.info('Snippet deleted');
    },
    
    use: (id) => {
        const snippet = SnippetManager.snippets.find(s => s.id === id);
        if (snippet) {
            EditorManager.setValue(snippet.code);
            EditorManager.setLanguage(snippet.language);
            document.getElementById('language-select').value = snippet.language;
            NexusAI.state.currentFile = `${snippet.name}.${snippet.language === 'python' ? 'py' : snippet.language}`;
            Toast.success(`Loaded: ${snippet.name}`);
            SnippetManager.hide();
        }
    },
    
    render: () => {
        const list = document.getElementById('snippets-list');
        if (!list) return;
        
        if (SnippetManager.snippets.length === 0) {
            list.innerHTML = '<div class="snippet-empty">No snippets saved yet. Save your first snippet!</div>';
            return;
        }
        
        list.innerHTML = SnippetManager.snippets.map(s => `
            <div class="snippet-card" data-id="${s.id}">
                <div class="snippet-card-header">
                    <span class="snippet-card-title">${Utils.escapeHtml(s.name)}</span>
                    <span class="snippet-card-lang">${s.language}</span>
                </div>
                ${s.description ? `<div class="snippet-card-desc">${Utils.escapeHtml(s.description)}</div>` : ''}
                <div class="snippet-card-tags">
                    ${s.tags.map(t => `<span class="snippet-tag">${Utils.escapeHtml(t)}</span>`).join('')}
                </div>
                <div class="snippet-card-actions">
                    <button class="action-btn" onclick="SnippetManager.use('${s.id}')">📥 Use</button>
                    <button class="action-btn" onclick="Utils.copyToClipboard(SnippetManager.snippets.find(x=>x.id==='${s.id}').code); Toast.success('Copied!')">📋 Copy</button>
                    <button class="action-btn" onclick="SnippetManager.delete('${s.id}')" style="color: var(--error)">🗑️</button>
                </div>
            </div>
        `).join('');
    },
    
    filter: (query) => {
        const cards = document.querySelectorAll('.snippet-card');
        const q = query.toLowerCase();
        cards.forEach(card => {
            const text = card.textContent.toLowerCase();
            card.style.display = !q || text.includes(q) ? '' : 'none';
        });
    }
};

// ==================== LIVE PREVIEW ====================
const LivePreview = {
    panel: null,
    iframe: null,
    isOpen: false,
    
    init: () => {
        LivePreview.panel = document.getElementById('preview-panel');
        LivePreview.iframe = document.getElementById('preview-iframe');
        
        document.getElementById('close-preview-btn')?.addEventListener('click', LivePreview.hide);
        document.getElementById('refresh-preview-btn')?.addEventListener('click', LivePreview.refresh);
    },
    
    show: () => {
        LivePreview.panel?.classList.remove('hidden');
        LivePreview.isOpen = true;
        LivePreview.refresh();
    },
    
    hide: () => {
        LivePreview.panel?.classList.add('hidden');
        LivePreview.isOpen = false;
    },
    
    toggle: () => {
        const lang = document.getElementById('language-select')?.value;
        if (!['html', 'css'].includes(lang)) {
            Toast.warning('Live preview is only available for HTML/CSS');
            return;
        }
        
        if (LivePreview.isOpen) {
            LivePreview.hide();
        } else {
            LivePreview.show();
        }
    },
    
    refresh: () => {
        if (!LivePreview.iframe) return;
        
        const code = EditorManager.getValue();
        const lang = document.getElementById('language-select')?.value;
        
        let html = code;
        if (lang === 'css') {
            html = `<!DOCTYPE html><html><head><style>${code}</style></head><body><h1>CSS Preview</h1><p>Add your HTML to see the styled result.</p></body></html>`;
        }
        
        const blob = new Blob([html], { type: 'text/html' });
        LivePreview.iframe.src = URL.createObjectURL(blob);
    }
};

// ==================== SESSION MANAGER ====================
const SessionManager = {
    save: () => {
        const session = {
            code: EditorManager.getValue(),
            language: document.getElementById('language-select')?.value,
            filename: NexusAI.state.currentFile,
            timestamp: new Date().toISOString()
        };
        localStorage.setItem('nexus-session', JSON.stringify(session));
        Toast.success('Session saved');
    },
    
    restore: () => {
        const session = JSON.parse(localStorage.getItem('nexus-session') || 'null');
        if (session) {
            EditorManager.setValue(session.code);
            if (session.language) {
                EditorManager.setLanguage(session.language);
                document.getElementById('language-select').value = session.language;
            }
            NexusAI.state.currentFile = session.filename;
            Toast.info('Session restored');
        }
    },
    
    clear: () => {
        localStorage.removeItem('nexus-session');
        Toast.info('Session cleared');
    }
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modules
    Toast.init();
    Shortcuts.init();
    Settings.init();
    CommandPalette.init();
    CodeMetrics.init();
    SnippetManager.init();
    LivePreview.init();
    
    // Register default shortcuts
    Shortcuts.register('ctrl+s', 'Save/Download code', () => {
        const code = EditorManager.getValue();
        Utils.downloadFile(code, NexusAI.state.currentFile || 'code.txt');
        Toast.success('Code downloaded!');
    });
    
    Shortcuts.register('ctrl+enter', 'Run code', () => {
        const runBtn = document.getElementById('run-btn') || document.querySelector('[onclick*="runCode"]');
        if (runBtn) runBtn.click();
    });
    
    Shortcuts.register('ctrl+/', 'Focus chat', () => {
        const chatInput = document.getElementById('user-input');
        if (chatInput) chatInput.focus();
    });
    
    // Command palette shortcut
    Shortcuts.register('ctrl+shift+p', 'Command Palette', () => {
        CommandPalette.show();
    });
    
    // Close modals on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            CommandPalette.hide();
            CodeMetrics.hide();
            SnippetManager.hide();
            SnippetManager.hideSaveModal();
            LivePreview.hide();
            document.getElementById('shortcuts-overlay')?.classList.add('hidden');
            document.getElementById('settings-overlay')?.classList.add('hidden');
        }
    });
    
    // Auto-restore session
    if (localStorage.getItem('nexus-session')) {
        setTimeout(() => SessionManager.restore(), 500);
    }
    
    console.log('🚀 NexusAI v2.1 initialized with professional features');
});

// Export for global access
window.NexusAI = NexusAI;
window.Utils = Utils;
window.Toast = Toast;
window.API = API;
window.MarkdownRenderer = MarkdownRenderer;
window.EditorManager = EditorManager;
window.Shortcuts = Shortcuts;
window.Settings = Settings;
window.CommandPalette = CommandPalette;
window.CodeMetrics = CodeMetrics;
window.SnippetManager = SnippetManager;
window.LivePreview = LivePreview;
window.SessionManager = SessionManager;
