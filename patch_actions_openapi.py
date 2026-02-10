import json

INP = "continuum-openapi.raw.json"
OUT = "continuum-openapi.actions.json"

# Set this to your HTTPS tunnel URL (trycloudflare/ngrok)
TUNNEL_URL = "https://mardi-empty-closest-nikon.trycloudflare.com"

spec = json.load(open(INP))

# ── helpers ──────────────────────────────────────────────────────────

def to_type_union(schema):
    """Convert anyOf: [X, null] -> type: [X.type, 'null']."""
    if not isinstance(schema, dict):
        return schema
    if "anyOf" in schema and isinstance(schema["anyOf"], list) and len(schema["anyOf"]) == 2:
        a, b = schema["anyOf"]
        if isinstance(a, dict) and isinstance(b, dict) and b.get("type") == "null" and "type" in a:
            out = dict(a)
            out["type"] = [a["type"], "null"]
            if "title" in schema:
                out.setdefault("title", schema["title"])
            if "description" in schema:
                out.setdefault("description", schema["description"])
            return out
    return schema


# ── 1. servers ───────────────────────────────────────────────────────

spec["servers"] = [{"url": TUNNEL_URL}]

# ── 2. Fix anyOf nullables in component request schemas ─────────────

for name in ("CommitRequest", "SupersedeRequest", "ResolveRequest"):
    schema = spec.get("components", {}).get("schemas", {}).get(name)
    if not schema or "properties" not in schema:
        continue
    for k, v in list(schema["properties"].items()):
        schema["properties"][k] = to_type_union(v)

# ── 3. Shared sub-schemas for response bodies ───────────────────────

decision_schema = {
    "type": "object",
    "properties": {
        "id":                 {"type": "string"},
        "version":            {"type": "integer"},
        "status":             {"type": "string"},
        "title":              {"type": "string"},
        "rationale":          {"type": "string"},
        "options_considered":  {"type": "array", "items": {"type": "object", "properties": {}}},
        "context":            {"type": "object", "properties": {}},
        "enforcement": {
            "type": "object",
            "properties": {
                "scope":            {"type": "string"},
                "decision_type":    {"type": "string"},
                "supersedes":       {"type": "string"},
                "precedence":       {"type": "integer"},
                "override_policy":  {"type": "string"}
            }
        },
        "stakeholders":       {"type": "array", "items": {"type": "string"}},
        "metadata":           {"type": "object", "properties": {}},
        "created_at":         {"type": "string"},
        "updated_at":         {"type": "string"}
    }
}

# ── 4. Patch every 200 response schema ──────────────────────────────

RESPONSE_SCHEMAS = {
    ("/health", "get"): {
        "type": "object",
        "properties": {
            "ok":        {"type": "boolean"},
            "store_dir": {"type": "string"}
        },
        "required": ["ok", "store_dir"]
    },
    ("/inspect", "get"): {
        "type": "object",
        "properties": {
            "binding": {
                "type": "array",
                "items": {"type": "object", "properties": {}}
            }
        },
        "required": ["binding"]
    },
    ("/decision/{decision_id}", "get"): {
        "type": "object",
        "properties": {
            "decision": decision_schema
        },
        "required": ["decision"]
    },
    ("/resolve", "post"): {
        "type": "object",
        "properties": {
            "resolution": {
                "type": "object",
                "properties": {
                    "status":              {"type": "string"},
                    "resolved_context":    {"type": "object", "properties": {}},
                    "clarification":       {"type": "object", "properties": {
                        "question":   {"type": "string"},
                        "candidates": {"type": "array", "items": {"type": "object", "properties": {}}},
                        "context":    {"type": "object", "properties": {}}
                    }},
                    "matched_decision_id": {"type": "string"}
                },
                "required": ["status"]
            }
        },
        "required": ["resolution"]
    },
    ("/enforce", "post"): {
        "type": "object",
        "properties": {
            "enforcement": {
                "type": "object",
                "properties": {}
            }
        },
        "required": ["enforcement"]
    },
    ("/commit", "post"): {
        "type": "object",
        "properties": {
            "decision": decision_schema
        },
        "required": ["decision"]
    },
    ("/supersede", "post"): {
        "type": "object",
        "properties": {
            "decision": decision_schema
        },
        "required": ["decision"]
    },
}

for (path, method), schema in RESPONSE_SCHEMAS.items():
    op = spec["paths"][path][method]
    op["responses"]["200"]["content"]["application/json"]["schema"] = schema

# ── 5. Inline /commit requestBody (LLM-proof) ───────────────────────

commit = spec["paths"]["/commit"]["post"]
commit["summary"] = "Commit a decision (store a stable preference/rule)"
commit["description"] = (
    "Create and persist a decision artifact. "
    "For preferences, use decision_type='preference' and activate=true."
)

commit_schema = {
    "type": "object",
    "additionalProperties": False,
    "required": ["title", "scope", "decision_type", "rationale"],
    "properties": {
        "title":         {"type": "string", "description": "Short title for the decision."},
        "scope":         {"type": "string", "description": "Scope string like 'user:personal'."},
        "decision_type": {"type": "string", "description": "Decision type. Use 'preference' for user preferences."},
        "rationale":     {"type": "string", "description": "Why this decision exists (1-2 sentences)."},
        "activate":      {"type": "boolean", "default": True, "description": "If true, activates immediately."}
    }
}

commit["requestBody"]["content"]["application/json"]["schema"] = commit_schema
commit["requestBody"]["content"]["application/json"]["examples"] = {
    "short_responses": {
        "summary": "Default to short responses",
        "value": {
            "title": "Default to short responses",
            "scope": "user:personal",
            "decision_type": "preference",
            "rationale": "User prefers short responses by default unless they explicitly ask for a deep dive.",
            "activate": True
        }
    }
}

# ── 6. Add example to /resolve ───────────────────────────────────────

resolve = spec["paths"]["/resolve"]["post"]
resolve["requestBody"]["content"]["application/json"]["examples"] = {
    "basic": {
        "summary": "Resolve with scope",
        "value": {"prompt": "bookings last week", "scope": "user:personal", "candidates": None}
    }
}

# ── 7. Fix bare objects in component schemas ─────────────────────────
#    Actions also complains about type:"object" without properties in
#    ValidationError.ctx, EnforceRequest.action, and items schemas.

# EnforceRequest.action
enforce_action = spec["components"]["schemas"]["EnforceRequest"]["properties"].get("action", {})
if enforce_action.get("type") == "object" and "properties" not in enforce_action:
    enforce_action["properties"] = {}

# ValidationError.ctx
val_err = spec["components"]["schemas"].get("ValidationError", {}).get("properties", {})
if "ctx" in val_err and val_err["ctx"].get("type") == "object" and "properties" not in val_err["ctx"]:
    val_err["ctx"]["properties"] = {}

# ValidationError.input — ensure it has a type
if "input" in val_err and "type" not in val_err["input"]:
    val_err["input"]["type"] = "string"

# ValidationError.loc.items — replace anyOf: [string, integer] with plain string
if "loc" in val_err:
    loc_items = val_err["loc"].get("items", {})
    if "anyOf" in loc_items:
        val_err["loc"]["items"] = {"type": "string"}

# Walk all component schemas: any object without properties gets an empty one
def fix_bare_objects(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "object" and "properties" not in obj and "$ref" not in obj:
            obj["properties"] = {}
        for v in obj.values():
            fix_bare_objects(v)
    elif isinstance(obj, list):
        for v in obj:
            fix_bare_objects(v)

fix_bare_objects(spec["components"])

# ── done ─────────────────────────────────────────────────────────────

json.dump(spec, open(OUT, "w"), indent=2)
print(f"Wrote {OUT} with servers={TUNNEL_URL}")
