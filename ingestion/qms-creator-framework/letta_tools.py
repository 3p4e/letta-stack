"""
Letta Custom Tools for GMP QMS Agents

Tools registered in Letta that chapter agents can call during content generation.
These are Python source code strings that get registered via client.tools.create().
"""

# Note: Letta tools are registered as source code strings.
# They execute inside the Letta server sandbox.
# For archive search, agents use the built-in archival_memory_search tool.
# These custom tools provide additional GMP-specific capabilities.

TOOL_DEFINITIONS = {
    "validate_gmp_section": {
        "source_code": '''
def validate_gmp_section(content: str, section_type: str) -> str:
    """
    Validate generated SOP section content against EU GMP requirements.

    Args:
        content: The generated section text to validate.
        section_type: Type of section (purpose, scope, procedure, etc.)

    Returns:
        JSON string with validation results: issues found, score, recommendations.
    """
    import json

    issues = []
    score = 100

    # Check for placeholder text
    placeholders = ["[INSERT", "[TODO", "[PLACEHOLDER", "TBD", "XXX", "FILL IN"]
    for p in placeholders:
        if p.upper() in content.upper():
            issues.append(f"Placeholder text found: {p}")
            score -= 15

    # Check minimum length per section type
    min_lengths = {
        "purpose": 200, "scope": 200, "definitions": 100,
        "raci": 150, "regulatory": 300, "procedure": 500,
        "documentation": 200, "training": 200, "annex": 100,
    }
    min_len = min_lengths.get(section_type, 100)
    if len(content) < min_len:
        issues.append(f"Section too short ({len(content)} chars, minimum {min_len})")
        score -= 20

    # Check for cannabis/GMP specificity
    gmp_terms = ["EU GMP", "GMP", "SOP", "quality", "compliance"]
    cannabis_terms = ["cannabis", "cannabinoid", "THC", "CBD", "cultivation", "herbal"]
    has_gmp = any(t.lower() in content.lower() for t in gmp_terms)
    has_cannabis = any(t.lower() in content.lower() for t in cannabis_terms)

    if not has_gmp and section_type in ("purpose", "regulatory", "scope"):
        issues.append("No GMP terminology found — content may not be regulatory-specific")
        score -= 10

    return json.dumps({
        "valid": len(issues) == 0,
        "score": max(0, score),
        "issues": issues,
        "section_type": section_type,
        "char_count": len(content),
    })
''',
        "description": "Validate SOP section content against EU GMP requirements. Checks for placeholders, minimum length, and regulatory specificity.",
    },

    "format_raci_matrix": {
        "source_code": '''
def format_raci_matrix(activities: list, roles: list, assignments: list) -> str:
    """
    Format a RACI matrix as a markdown table.

    Args:
        activities: List of activity/step names (rows).
        roles: List of role names (columns).
        assignments: 2D list where assignments[i][j] is R/A/C/I for activity i, role j.

    Returns:
        Markdown-formatted RACI table.
    """
    if not activities or not roles or not assignments:
        return "Error: Empty input"

    # Header
    header = "| Activity | " + " | ".join(roles) + " |"
    separator = "|" + "---|" * (len(roles) + 1)

    # Rows
    rows = []
    for i, activity in enumerate(activities):
        if i < len(assignments):
            cells = assignments[i]
            # Pad if needed
            while len(cells) < len(roles):
                cells.append("")
            row = f"| {activity} | " + " | ".join(cells[:len(roles)]) + " |"
        else:
            row = f"| {activity} | " + " | ".join([""] * len(roles)) + " |"
        rows.append(row)

    return "\\n".join([header, separator] + rows)
''',
        "description": "Format a RACI responsibility matrix as a markdown table from structured data.",
    },

    "generate_mermaid_flowchart": {
        "source_code": '''
def generate_mermaid_flowchart(title: str, steps: list) -> str:
    """
    Generate a Mermaid flowchart from procedure steps.

    Args:
        title: Flowchart title.
        steps: List of dicts with keys: id, label, type (process/decision/start/end), next (list of target ids).

    Returns:
        Mermaid flowchart syntax string.
    """
    lines = [f"```mermaid", f"flowchart TD"]
    lines.append(f"    title[{title}]")

    for step in steps:
        sid = step.get("id", "")
        label = step.get("label", "")
        stype = step.get("type", "process")

        if stype == "start":
            lines.append(f"    {sid}([{label}])")
        elif stype == "end":
            lines.append(f"    {sid}([{label}])")
        elif stype == "decision":
            lines.append(f"    {sid}{{{{{label}}}}}")
        else:
            lines.append(f"    {sid}[{label}]")

    for step in steps:
        sid = step.get("id", "")
        for target in step.get("next", []):
            if isinstance(target, dict):
                tid = target.get("id", "")
                tlabel = target.get("label", "")
                lines.append(f"    {sid} -->|{tlabel}| {tid}")
            else:
                lines.append(f"    {sid} --> {target}")

    lines.append("```")
    return "\\n".join(lines)
''',
        "description": "Generate a Mermaid.js flowchart from structured procedure steps.",
    },
}


def register_all_tools(letta_service) -> dict:
    """
    Register all custom tools in Letta and return name→id mapping.

    Args:
        letta_service: LettaService instance.

    Returns:
        Dict mapping tool names to tool IDs.
    """
    tool_ids = {}
    for name, definition in TOOL_DEFINITIONS.items():
        tool_id = letta_service.register_tool(
            name=name,
            source_code=definition["source_code"],
            description=definition["description"],
        )
        tool_ids[name] = tool_id

    return tool_ids
