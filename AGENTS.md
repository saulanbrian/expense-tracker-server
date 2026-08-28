# AGENTS.md

## Folder Structure

Follow this layered architecture when adding new code:

```
server/
├── main.py                    # FastAPI entry point
├── config/                    # App configuration (env vars, settings)
├── domain/                    # Pydantic models, shared schemas (no business logic)
├── infra/                     # External service clients
│   ├── db.py                  # Supabase client
│   ├── llm.py                 # LLM client setup
│   ├── ocr.py                 # OCR wrapper
│   ├── worker.py              # ARQ worker settings
│   └── providers/             # LLM provider implementations (one file per provider)
├── services/                  # Database operations (CRUD, one file per table)
├── features/                  # Feature modules (routes + business logic)
│   └── <feature>/
│       ├── router.py          # FastAPI router
│       └── <module>.py        # Feature-specific logic
├── tests/
└── .gitignore
```

## Rules

### Dependency direction (top-down only)

```
features/ → services/ → infra/ → domain/
```

- `features/` depends on `services/` and `infra/`
- `services/` depends on `infra/` and `domain/`
- `infra/` depends on `domain/`
- `domain/` depends on nothing

Never import upward (e.g., `infra/` must not import from `services/`).

### One function per concern

Each function does exactly one thing. Helpers are defined above the functions that call them.

```python
# Good
def _fetch_document(document_id: str) -> Documents:
    ...

def _should_process(document: Documents) -> bool:
    ...

async def run_load(ctx: PipelineContext, update_status) -> LoadResult:
    document = await _fetch_document(ctx.document_id)
    ...
```

### Type hints on public functions

Public functions get full type hints. Internal helpers can use `Any` for complex union types.

```python
# Good
def _call_gemini(
    config: ModelConfig,
    messages: list[ChatCompletionMessageParam],
    response_format: type[T],
) -> T:
    ...

# Acceptable for internal helpers
def _build_parts(content: Any) -> list[types.Part]:
    ...
```

### Typed shared state

Use dataclasses, not dicts, for shared state passed between functions.

```python
# Good
@dataclass
class PipelineContext:
    document_id: str
    document: Documents | None = None

# Bad
ctx = {"document_id": id, "document": None}
```

### Logging

Use `logger.exception()` for errors. Never `traceback.print_exc()`.

```python
# Good
logger.exception("Failed to process document %s", document_id)

# Bad
traceback.print_exc()
```

### Pipeline phases

Each phase file contains exactly one public function (`run_<phase>`) and its helpers.

```
phases/
├── load.py        # run_load — fetch doc, check status, lock
├── convert.py     # run_convert — download file, PDF→images, OCR
├── extract.py     # run_extract — LLM extraction (text + vision)
├── enrich.py      # run_enrich — validate billing doc, FX rate
└── persist.py     # run_persist — save document + line items
```

### LLM providers

One file per provider in `infra/providers/`. Each exposes a single function:

```
_call_openrouter(config, messages, response_format) -> T
_call_gemini(config, messages, response_format) -> T
```

Shared utilities go in `utils.py`. Shared types go in `models.py`.

### Naming

- Files: `snake_case.py`
- Functions: `snake_case`
- Private helpers: `_leading_underscore`
- Constants: `UPPER_SNAKE_CASE`
- Classes: `PascalCase`
