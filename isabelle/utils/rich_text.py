import json

from isabelle.web_submission import as_rich_text


def to_rich_text_column(value) -> str:
    elements = value if isinstance(value, list) else as_rich_text(str(value or ""))
    return json.dumps({"type": "rich_text", "elements": elements})


def from_rich_text_column(value):
    if value is None:
        return None

    if isinstance(value, dict):
        return value

    if isinstance(value, list):
        return {"type": "rich_text", "elements": value}

    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = json.loads(value)
    except (ValueError, TypeError):
        return {"type": "rich_text", "elements": as_rich_text(value)}

    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list):
        return {"type": "rich_text", "elements": parsed}
    return {"type": "rich_text", "elements": as_rich_text(value)}


def column_to_markdown(value):
    from isabelle.utils.utils import rich_text_to_md

    block = from_rich_text_column(value)
    if not block:
        return None
    try:
        return rich_text_to_md(block.get("elements") or []).strip() or None
    except Exception:
        return None
