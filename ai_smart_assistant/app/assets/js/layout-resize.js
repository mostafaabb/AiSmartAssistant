/**
 * Resizable IDE layout: explorer / editor+terminal / chat
 * Persists sizes in localStorage; double-click a handle to reset that axis.
 */
const LayoutResize = {
    root: null,
    defaults: { explorer: 260, chat: 400, terminal: 180 },
    min: { explorer: 160, chat: 260, terminal: 72 },
    max: { explorer: 560, chat: 720, terminal: () => Math.min(window.innerHeight * 0.65, 720) },

    init() {
        this.root = document.getElementById('ide-layout');
        if (!this.root) return;

        this.loadVars();
        this.bindHorizontal('resize-explorer', 'explorer', true);
        this.bindHorizontal('resize-chat', 'chat', false);
        this.bindVertical('resize-terminal', 'terminal');
        this.bindToggles();
        this.bindCopySelection();

        window.addEventListener('resize', () => {
            this.clampAll();
        });
    },

    loadVars() {
        const ex = parseInt(localStorage.getItem('nexus-layout-explorer'), 10);
        const ch = parseInt(localStorage.getItem('nexus-layout-chat'), 10);
        const te = parseInt(localStorage.getItem('nexus-layout-terminal'), 10);
        this.root.style.setProperty('--explorer-w', `${Number.isFinite(ex) ? ex : this.defaults.explorer}px`);
        this.root.style.setProperty('--chat-w', `${Number.isFinite(ch) ? ch : this.defaults.chat}px`);
        this.root.style.setProperty('--terminal-h', `${Number.isFinite(te) ? te : this.defaults.terminal}px`);
    },

    save(key, px) {
        localStorage.setItem(key, String(Math.round(px)));
    },

    clampAll() {
        this._clampDim('--explorer-w', 'explorer', 'nexus-layout-explorer');
        this._clampDim('--chat-w', 'chat', 'nexus-layout-chat');
        this._clampDim('--terminal-h', 'terminal', 'nexus-layout-terminal', true);
    },

    _clampDim(cssVar, name, storageKey, isHeight) {
        const raw = this.root.style.getPropertyValue(cssVar);
        const px = parseFloat(raw) || this.defaults[name];
        const min = this.min[name];
        const max = typeof this.max[name] === 'function' ? this.max[name]() : this.max[name];
        const v = Math.max(min, Math.min(max, px));
        this.root.style.setProperty(cssVar, `${v}px`);
        this.save(storageKey, v);
    },

    bindHorizontal(handleId, which, isLeftPane) {
        const handle = document.getElementById(handleId);
        if (!handle) return;

        handle.addEventListener('dblclick', () => {
            const d = this.defaults[which];
            const prop = which === 'explorer' ? '--explorer-w' : '--chat-w';
            this.root.style.setProperty(prop, `${d}px`);
            this.save(`nexus-layout-${which}`, d);
        });

        handle.addEventListener('mousedown', (down) => {
            if (down.button !== 0) return;
            down.preventDefault();
            const prop = which === 'explorer' ? '--explorer-w' : '--chat-w';
            const start = parseFloat(getComputedStyle(this.root).getPropertyValue(prop)) || this.defaults[which];
            const startX = down.clientX;
            const max = typeof this.max[which] === 'function' ? this.max[which]() : this.max[which];

            const onMove = (e) => {
                const dx = e.clientX - startX;
                const next = isLeftPane ? start + dx : start - dx;
                const v = Math.max(this.min[which], Math.min(max, next));
                this.root.style.setProperty(prop, `${v}px`);
            };

            const onUp = () => {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                document.body.classList.remove('layout-resizing');
                const cur = parseFloat(getComputedStyle(this.root).getPropertyValue(prop)) || this.defaults[which];
                this.save(`nexus-layout-${which}`, cur);
                setTimeout(() => window.NexusAI?.editor?.layout?.(), 0);
            };

            document.body.classList.add('layout-resizing');
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    },

    bindVertical(handleId) {
        const handle = document.getElementById(handleId);
        if (!handle) return;

        handle.addEventListener('dblclick', () => {
            const d = this.defaults.terminal;
            this.root.style.setProperty('--terminal-h', `${d}px`);
            this.save('nexus-layout-terminal', d);
            if (window.monaco?.editor) {
                const ed = window.NexusAI?.editor || window.EditorManager?.instance;
                ed?.layout?.();
            }
        });

        handle.addEventListener('mousedown', (down) => {
            if (down.button !== 0) return;
            down.preventDefault();
            const start = parseFloat(getComputedStyle(this.root).getPropertyValue('--terminal-h')) || this.defaults.terminal;
            const startY = down.clientY;
            const max = this.max.terminal();

            const onMove = (e) => {
                const dy = e.clientY - startY;
                const next = start + dy;
                const v = Math.max(this.min.terminal, Math.min(max, next));
                this.root.style.setProperty('--terminal-h', `${v}px`);
                const ed = window.NexusAI?.editor || window.EditorManager?.instance;
                ed?.layout?.();
            };

            const onUp = () => {
                document.removeEventListener('mousemove', onMove);
                document.removeEventListener('mouseup', onUp);
                document.body.classList.remove('layout-resizing-v');
                const cur = parseFloat(getComputedStyle(this.root).getPropertyValue('--terminal-h')) || this.defaults.terminal;
                this.save('nexus-layout-terminal', cur);
                const ed = window.NexusAI?.editor || window.EditorManager?.instance;
                ed?.layout?.();
            };

            document.body.classList.add('layout-resizing-v');
            document.addEventListener('mousemove', onMove);
            document.addEventListener('mouseup', onUp);
        });
    },

    bindToggles() {
        const root = this.root;
        const ex = () => {
            root.classList.toggle('layout-hide-explorer');
            setTimeout(() => window.NexusAI?.editor?.layout?.(), 100);
        };
        const ch = () => {
            root.classList.toggle('layout-hide-chat');
            setTimeout(() => window.NexusAI?.editor?.layout?.(), 100);
        };

        document.getElementById('toggle-explorer-btn')?.addEventListener('click', ex);
        document.getElementById('toggle-chat-btn')?.addEventListener('click', ch);
        document.getElementById('focus-mode-btn')?.addEventListener('click', () => {
            root.classList.toggle('layout-zen');
            const on = root.classList.contains('layout-zen');
            if (window.Toast) Toast.info(on ? 'Focus mode — side panels hidden' : 'Focus mode off');
            setTimeout(() => window.NexusAI?.editor?.layout?.(), 120);
        });

        Shortcuts.register('ctrl+shift+b', 'Toggle explorer sidebar', ex);
        Shortcuts.register('ctrl+shift+j', 'Toggle AI chat panel', ch);
        Shortcuts.register('ctrl+shift+m', 'Focus mode (hide both side panels)', () => {
            document.getElementById('focus-mode-btn')?.click();
        });
        Shortcuts.register('ctrl+alt+q', 'Insert editor selection into chat', () => {
            document.getElementById('copy-selection-chat-btn')?.click();
        });
    },

    bindCopySelection() {
        document.getElementById('copy-selection-chat-btn')?.addEventListener('click', () => {
            const ed = window.NexusAI?.editor || window.EditorManager?.instance;
            const input = document.getElementById('user-input');
            if (!ed || !input) return;
            const model = ed.getModel();
            const sel = ed.getSelection();
            if (!model || !sel) return;
            const text = model.getValueInRange(sel);
            if (!text.trim()) {
                if (window.Toast) Toast.warning('Select code first');
                return;
            }
            const lang = document.getElementById('language-select')?.value || 'text';
            input.value = `Regarding this selection:\n\`\`\`${lang}\n${text}\n\`\`\`\n\n`;
            input.focus();
            if (window.Toast) Toast.success('Selection inserted into chat');
        });
    }
};

window.LayoutResize = LayoutResize;
