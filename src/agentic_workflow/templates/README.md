# Templates Directory

> **Jinja2 template system** for agent workflows  
> See [TEMPLATES.md](./TEMPLATES.md) for complete documentation

---

## Quick Start

```python
from scripts.utils.jinja_loader import render_agent, render_session

# Render agent template
agent_md = render_agent('planning', 'A-02', 'my_project')

# Render session template
session_md = render_session('planning', 'A-02', 'my_project')
```

---

## Directory Structure

```
templates/
├── _base/                    # Base templates (Jinja2)
│   ├── agent_base.md.j2      # Agent personas
│   ├── session_base.md.j2    # Active sessions
│   └── project_index.md.j2   # Project registry
│
├── _partials/                # Reusable sections
│   ├── artifact_table.j2
│   ├── handoff_section.j2
│   └── ...
│
├── docs/                     # Documentation templates
│   ├── copilot-instructions.md.j2
│   └── GOVERNANCE_GUIDE.md.j2
│
├── logs/                     # Log templates
│   ├── exchange_log.md.j2
│   └── context_log.md.j2
│
├── artifacts/                # Artifact boilerplate
│   └── artifact_template.md
│
└── workflow.tpl              # Shell CLI wrapper
```

---

## Documentation

| Document | Purpose |
|----------|---------|
| [TEMPLATES.md](./TEMPLATES.md) | Template system guide |
| [PLACEHOLDER_REGISTRY.md](./PLACEHOLDER_REGISTRY.md) | Variable reference |
| [MIGRATION_STATUS.md](./MIGRATION_STATUS.md) | Migration progress |

---

## Template Resolution

Templates resolve in priority order:

1. `manifests/workflows/<workflow>/templates/` — Workflow override
2. `templates/_base/` — Base templates
3. `templates/_partials/` — Shared partials

---

## Editing Guidelines

1. **Edit templates**, not generated files in `agent_files/` or `projects/`
2. Use `.j2` extension for Jinja2 templates
3. Run tests after changes:
   ```bash
   python3 -m pytest tests/test_template_render.py -v
   ```

---

## Regenerating Files

```bash
# Regenerate agent files
python3 -m scripts.generation.generate_agents --workflow planning --jinja2

# Refresh project
python3 -m scripts.cli.workflow refresh <project_name>
```

---

*See [TEMPLATES.md](./TEMPLATES.md) for complete documentation*
