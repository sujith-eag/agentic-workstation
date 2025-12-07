# Template System Documentation

> **Source of Truth** for the Jinja2 template system  
> Version: 2.0 | Updated: 2025-12-05

---

## 1. Overview

The template system uses **Jinja2** for rendering agent prompts, sessions, and documentation with:

- **Hierarchical resolution** — Workflow-specific → role-based → base → partials
- **Template inheritance** — `{% extends %}` for layered customization
- **Reusable partials** — `{% include %}` for DRY components
- **Custom filters** — Markdown-aware formatting
- **Context builders** — Automatic data loading from canonical JSON

---

## 2. Directory Structure

```
templates/
├── _base/                    # Base templates (Layer 1)
│   ├── agent_base.md.j2      # All agent personas
│   ├── session_base.md.j2    # Active session documents
│   └── project_index.md.j2   # Project file registry
│
├── _partials/                # Reusable sections
│   ├── frontmatter_helpers.j2
│   ├── artifact_table.j2
│   ├── handoff_section.j2
│   ├── checkpoint_warning.j2
│   ├── governance_footer.j2
│   └── cli_commands.j2
│
├── _roles/                   # Role-specific templates (Layer 2)
│   ├── analyst/              # Planning/research analysts
│   ├── engineer/             # Implementation engineers
│   ├── auditor/              # Review/audit agents
│   └── orchestrator/         # Workflow orchestrators
│
├── docs/                     # Documentation templates
│   ├── copilot-instructions.md.j2
│   ├── GOVERNANCE_GUIDE.md.j2
│   └── GEMINI.md.j2
│
├── logs/                     # Log file templates
│   ├── exchange_log.md.j2
│   └── context_log.md.j2
│
├── artifacts/                # Artifact boilerplate
│   └── artifact_template.md
│
└── workflow.tpl              # Shell CLI wrapper (not Jinja2)

manifests/workflows/<type>/templates/
└── (workflow-specific overrides)
```

---

## 3. Template Resolution

Templates are resolved in priority order (first match wins):

| Priority | Location | Purpose |
|----------|----------|---------|
| 1 | `manifests/workflows/<workflow>/templates/` | Workflow package overrides |
| 2 | `templates/<workflow>/` | Workflow group templates |
| 3 | `templates/_roles/<role>/` | Role-based templates |
| 4 | `templates/_base/` | Base templates |
| 5 | `templates/_partials/` | Shared partials |
| 6 | `templates/` | Root fallback |

### Example Resolution

For `agent_body.md.j2` in **planning** workflow with **analyst** role:

```
1. manifests/workflows/planning/templates/agent_body.md.j2  ❌ not found
2. templates/planning/agent_body.md.j2                      ❌ not found
3. templates/_roles/analyst/agent_body.md.j2                ✅ FOUND → use
4. templates/_base/agent_body.md.j2                         (skipped)
```

---

## 4. Template Inheritance

Templates use Jinja2 block inheritance for layered customization:

```jinja2
{# templates/_base/agent_base.md.j2 #}
{% block frontmatter %}
---
agent_id: {{ agent_id }}
---
{% endblock %}

{% block body %}
## {{ agent_role }}
{{ purpose }}

{% block responsibilities %}{% endblock %}
{% block artifacts %}{% endblock %}
{% block handoff %}{% endblock %}
{% endblock %}
```

```jinja2
{# templates/_roles/analyst/agent.md.j2 #}
{% extends "_base/agent_base.md.j2" %}

{% block responsibilities %}
### Analytical Responsibilities
{% for resp in responsibilities %}
- {{ resp }}
{% endfor %}
{% endblock %}
```

---

## 5. Available Partials

| Partial | Parameters | Purpose |
|---------|------------|---------|
| `frontmatter_helpers.j2` | agent, workflow, project | YAML frontmatter macros |
| `artifact_table.j2` | produces, consumes | Tiered artifact display |
| `handoff_section.j2` | handoff, agent_id | Next agent + checklist |
| `checkpoint_warning.j2` | checkpoint, agent_id | Checkpoint alert box |
| `governance_footer.j2` | governance, enforcement | Rules + constraints |
| `cli_commands.j2` | agent_id, workflow_name | CLI quick reference |

### Usage

```jinja2
{% include '_partials/handoff_section.j2' %}
{% include '_partials/artifact_table.j2' %}
```

---

## 6. Custom Filters

| Filter | Description | Example |
|--------|-------------|---------|
| `md_list` | Array → markdown bullets | `{{ items \| md_list }}` |
| `md_numbered_list` | Array → numbered list | `{{ steps \| md_numbered_list }}` |
| `md_table` | Dict array → table | `{{ rows \| md_table }}` |
| `quote` | Text → blockquote | `{{ text \| quote }}` |
| `code` | Text → code block | `{{ cmd \| code('bash') }}` |
| `slugify` | Text → URL slug | `{{ name \| slugify }}` |
| `capitalize_first` | Capitalize first letter | `{{ word \| capitalize_first }}` |

---

## 7. Context Variables

See [PLACEHOLDER_REGISTRY.md](./PLACEHOLDER_REGISTRY.md) for complete variable reference.

### Quick Reference

| Category | Key Variables |
|----------|---------------|
| **Project** | `project_name`, `workflow_name`, `workflow_display_name` |
| **Agent** | `agent_id`, `agent_role`, `agent_type`, `agent_slug` |
| **Instructions** | `purpose`, `responsibilities`, `workflow`, `boundaries` |
| **Artifacts** | `produces`, `consumes` (tiered dicts) |
| **Workflow** | `stage`, `checkpoint`, `governance`, `logging_policy` |

---

## 8. Core Engine

The template engine is implemented in `src/agentic_workflow/utils/jinja_loader.py`:

```python
from agentic_workflow.utils.jinja_loader import (
    JinjaTemplateLoader,    # Template loader class
    render_agent,           # Render agent template
    render_session,         # Render session template
    build_agent_context,    # Build context from JSON
    load_canonical_json,    # Load canonical data
)

# Basic usage
loader = JinjaTemplateLoader(workflow='planning')
output = loader.render('agent_base.md.j2', context)

# Convenience functions
agent_md = render_agent('planning', 'A-02', 'my_project')
session_md = render_session('planning', 'A-02', 'my_project')
```

---

## 9. Authoring Templates

### Step 1: Choose Layer

| If template is... | Place in... |
|-------------------|-------------|
| Common to all agents | `_base/` |
| Specific to a role | `_roles/<role>/` |
| Specific to a workflow | `manifests/workflows/<type>/templates/` |

### Step 2: Extend Base

```jinja2
{% extends "_base/agent_base.md.j2" %}

{% block artifacts %}
{# Custom artifact section #}
{% include '_partials/artifact_table.j2' %}
{% endblock %}
```

### Step 3: Test

```bash
# Render and inspect
python3 -c "
from scripts.utils.jinja_loader import render_agent
print(render_agent('planning', 'A-02'))
"

# Run test suite
python3 -m pytest tests/test_template_render.py -v
```

---

## 10. Validation

```bash
# Validate all templates
python3 -m scripts.validation.validate_templates

# Run template tests
python3 -m pytest tests/test_template_render.py -v
```

### Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| No raw placeholders | ERROR | No `{{` or `}}` in output |
| Required blocks present | ERROR | All required blocks exist |
| Frontmatter valid | ERROR | YAML parses correctly |
| No empty blocks | WARN | Blocks have content |

---

## 11. File Naming Conventions

| Extension | Engine | Purpose |
|-----------|--------|---------|
| `.j2` | Jinja2 | Template files |
| `.md` | None | Static markdown |
| `.tpl` | Legacy/Shell | Legacy or shell scripts |

**Naming Pattern:** `<name>.<output_type>.j2`

Examples:
- `agent_base.md.j2` → renders to `.md`
- `workflow_config.yaml.j2` → renders to `.yaml`

---

## 12. Data Flow

```
┌─────────────────┐     ┌─────────────────┐
│  agents.json    │     │ instructions.json│
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  build_agent_context()│
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  JinjaTemplateLoader  │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  agent_base.md.j2     │
         │  + _partials/*.j2     │
         └───────────┬───────────┘
                     ▼
         ┌───────────────────────┐
         │  Rendered Markdown    │
         └───────────────────────┘
```

---

## 13. Troubleshooting

### Template Not Found

```
TemplateNotFound: some_template.j2
```

**Check:**
1. File exists in expected path
2. Extension is `.j2`
3. Workflow parameter matches directory name

### Undefined Variable

```
UndefinedError: 'agent_id' is undefined
```

**Check:**
1. Variable is in context dictionary
2. Spelling matches exactly (case-sensitive)
3. Variable is passed through `{% include %}` if in partial

### Empty Output

**Check:**
1. Block is defined in parent
2. Block name matches exactly
3. Use `{{ super() }}` to include parent content

---

## References

- [PLACEHOLDER_REGISTRY.md](./PLACEHOLDER_REGISTRY.md) — Complete variable reference
- [MIGRATION_STATUS.md](./MIGRATION_STATUS.md) — Migration progress tracking
- [scripts/utils/jinja_loader.py](../scripts/utils/jinja_loader.py) — Core engine
- [tests/test_template_render.py](../tests/test_template_render.py) — Test suite

---

*Last updated: 2025-12-05*
