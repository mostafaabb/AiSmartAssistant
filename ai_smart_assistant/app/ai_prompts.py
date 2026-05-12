"""System prompts and AI assistant modes for OpenRouter chat."""

SYSTEM_PROMPT = """You are NexusAI, an expert AI programming assistant embedded in a web IDE. You help developers write, debug, review, and ship high-quality code.

Guidelines:
- Be concise but precise; use headings and bullet lists when they aid scanning
- Prefer working, runnable code in fenced blocks with correct language tags
- When fixing bugs, state the root cause and why the fix works
- Call out trade-offs, risks, and testing suggestions when relevant
- If information is missing, ask one focused question or state reasonable assumptions
- Never invent file paths or APIs that you are not confident exist

You are assisting in an IDE: prioritize practical, copy-paste-ready output."""

# Mode-specific instructions appended to the system prompt
AI_MODE_PROMPTS: dict[str, str] = {
    "general": "",
    "explain": (
        "Focus on explaining the code: intent, control flow, data structures, and edge cases. "
        "Use short examples only where they clarify behavior."
    ),
    "debug": (
        "Focus on finding bugs, logic errors, race conditions, and failure modes. "
        "Suggest concrete fixes and how to verify them (tests, logs, repro steps)."
    ),
    "tests": (
        "Focus on generating thorough unit/integration tests with clear arrange/act/assert structure. "
        "Name frameworks explicitly (e.g. pytest, jest, vitest) and include edge cases."
    ),
    "optimize": (
        "Focus on performance, memory, algorithmic complexity, and readability. "
        "Benchmark or complexity notes when useful; avoid micro-optimizations without impact."
    ),
    "document": (
        "Focus on documentation: docstrings, module-level comments, README snippets, and API usage examples."
    ),
    "refactor": (
        "Focus on refactoring: naming, structure, separation of concerns, and DRY—without changing external behavior. "
        "Propose incremental steps if the change is large."
    ),
    "review": (
        "Act as a senior reviewer: correctness, readability, testing gaps, error handling, and API design. "
        "Use a short severity-tagged list (e.g. blocking / suggestion / nit)."
    ),
    "security": (
        "Act as a security reviewer: injection, authn/z, secrets, deserialization, SSRF, path traversal, "
        "crypto misuse, and dependency risks. Reference OWASP-style categories when helpful."
    ),
    "architecture": (
        "Focus on architecture: boundaries, coupling, scalability, observability, and evolution. "
        "Suggest diagrams in text (components + data flow) when it helps."
    ),
    "types": (
        "Focus on static typing: add precise types, generics, protocols/interfaces, and narrow unions. "
        "Mention the type system (TypeScript, mypy, etc.) explicitly."
    ),
    "commit": (
        "Generate a concise conventional commit message and optional body from the described or shown changes. "
        "Follow Conventional Commits when possible."
    ),
}

DEFAULT_MODEL_FALLBACKS: list[str] = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-coder:free",
    "google/gemma-4-31b-it:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
]

# Models the UI may select; must be safe to pass to OpenRouter
ALLOWED_CHAT_MODELS: frozenset[str] = frozenset(
    {
        "meta-llama/llama-3.3-70b-instruct:free",
        "qwen/qwen3-coder:free",
        "google/gemma-4-31b-it:free",
        "liquid/lfm-2.5-1.2b-thinking:free",
        "deepseek/deepseek-chat-v3-0324:free",
        "mistralai/mistral-7b-instruct:free",
    }
)


def build_system_prompt(mode: str) -> str:
    mode = (mode or "general").strip().lower()
    extra = AI_MODE_PROMPTS.get(mode, AI_MODE_PROMPTS["general"])
    if not extra:
        return SYSTEM_PROMPT
    return f"{SYSTEM_PROMPT}\n\n## Current mode\n{extra}"


def context_file_limit(mode: str) -> int:
    m = (mode or "").lower()
    if m in ("security", "review", "architecture"):
        return 22
    return 16


MODE_LABELS: dict[str, str] = {
    "general": "General",
    "explain": "Explain",
    "debug": "Debug",
    "tests": "Tests",
    "optimize": "Optimize",
    "document": "Document",
    "refactor": "Refactor",
    "review": "Code review",
    "security": "Security",
    "architecture": "Architecture",
    "types": "Types",
    "commit": "Commit message",
}


def modes_for_api() -> list[dict]:
    rows = []
    for k, v in AI_MODE_PROMPTS.items():
        desc = v.strip() if v else "Balanced help for any coding task"
        if len(desc) > 140:
            desc = desc[:137] + "…"
        rows.append(
            {"id": k, "label": MODE_LABELS.get(k, k.title()), "description": desc}
        )
    return rows


def resolve_models(preferred: str | None) -> list[str]:
    """Ordered list of models to try (user preference first, then fallbacks)."""
    out: list[str] = []
    if preferred:
        p = preferred.strip()
        if p in ALLOWED_CHAT_MODELS and p not in out:
            out.append(p)
    for m in DEFAULT_MODEL_FALLBACKS:
        if m not in out:
            out.append(m)
    return out
