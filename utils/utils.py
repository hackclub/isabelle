from .env import env

import re

from slack_sdk import WebClient

client = WebClient(token=env.slack_bot_token)


def user_in_safehouse(user_id: str):
    sad_members = client.conversations_members(channel=env.slack_sad_channel)["members"]
    return user_id in sad_members


def parse_elements(elements):
    markdown = ""
    for element in elements:
        if element["type"] == "text":
            text = element["text"]
            if "style" in element:
                if element["style"].get("bold"):
                    text = f"**{text}**"
                if element["style"].get("italic"):
                    text = f"*{text}*"
                if element["style"].get("strike"):
                    text = f"~~{text}~~"
                if element["style"].get("code"):
                    text = f"`{text}`"
            markdown += text
        elif element["type"] == "link":
            markdown += f"[{element['text']}]({element['url']})"
    return markdown


def rich_text_to_md(input_data, indent_level=0, in_quote=False):
    markdown = ""
    for block in input_data:
        if isinstance(block, dict) and block["type"] == "rich_text_section":
            markdown += parse_elements(block["elements"]) + "\n"
        elif isinstance(block, dict) and block["type"] == "rich_text_quote":
            markdown += "> " + parse_elements(block["elements"]) + "\n"
            # Handle nested lists within quotes
            markdown += rich_text_to_md(block["elements"], indent_level, in_quote=True)
        elif isinstance(block, dict) and block["type"] == "rich_text_preformatted":
            markdown += "```\n" + parse_elements(block["elements"]) + "\n```\n"
        elif isinstance(block, dict) and block["type"] == "rich_text_list":
            for item in block["elements"]:
                prefix = "> " if in_quote else ""
                markdown += (
                    "  " * indent_level
                    + prefix
                    + f"- {parse_elements(item['elements'])}\n"
                )
                # Recursively parse nested lists
                if "elements" in item:
                    markdown += rich_text_to_md(
                        item["elements"], indent_level + 1, in_quote
                    )
    return markdown


def md_to_rich_text(md):
    rich_text = []

    # Convert code blocks
    code_block_pattern = re.compile(r"```(.*?)```", re.DOTALL)
    md = code_block_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_preformatted",
                "elements": [{"type": "text", "text": m.group(1)}],
            }
        )
        or "",
        md,
    )

    # Convert blockquotes
    blockquote_pattern = re.compile(r"^> (.*)", re.MULTILINE)
    md = blockquote_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_quote",
                "elements": [{"type": "text", "text": m.group(1)}],
            }
        )
        or "",
        md,
    )

    # Convert unordered lists
    unordered_list_pattern = re.compile(r"^\s*-\s+(.*)", re.MULTILINE)
    md = unordered_list_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_list",
                "style": "bullet",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [{"type": "text", "text": m.group(1)}],
                    }
                ],
            }
        )
        or "",
        md,
    )

    # Convert ordered lists
    ordered_list_pattern = re.compile(r"^\s*\d+\.\s+(.*)", re.MULTILINE)
    md = ordered_list_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_list",
                "style": "numbered",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [{"type": "text", "text": m.group(1)}],
                    }
                ],
            }
        )
        or "",
        md,
    )

    # Convert inline code
    inline_code_pattern = re.compile(r"`(.*?)`")
    md = inline_code_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "text", "text": m.group(1), "style": {"code": True}}
                ],
            }
        )
        or "",
        md,
    )

    # Convert bold and italic text
    bold_italic_pattern = re.compile(r"\*\*\*(.*?)\*\*\*")
    md = bold_italic_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [
                    {
                        "type": "text",
                        "text": m.group(1),
                        "style": {"bold": True, "italic": True},
                    }
                ],
            }
        )
        or "",
        md,
    )

    bold_pattern = re.compile(r"\*\*(.*?)\*\*")
    md = bold_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "text", "text": m.group(1), "style": {"bold": True}}
                ],
            }
        )
        or "",
        md,
    )

    italic_pattern = re.compile(r"\*(.*?)\*")
    md = italic_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "text", "text": m.group(1), "style": {"italic": True}}
                ],
            }
        )
        or "",
        md,
    )

    # Convert strikethrough text
    strikethrough_pattern = re.compile(r"~~(.*?)~~")
    md = strikethrough_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [
                    {"type": "text", "text": m.group(1), "style": {"strike": True}}
                ],
            }
        )
        or "",
        md,
    )

    # Convert links
    link_pattern = re.compile(r"\[(.*?)\]\((.*?)\)")
    md = link_pattern.sub(
        lambda m: rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [{"type": "link", "url": m.group(2), "text": m.group(1)}],
            }
        )
        or "",
        md,
    )

    # Convert plain text
    if md.strip():
        rich_text.append(
            {
                "type": "rich_text_section",
                "elements": [{"type": "text", "text": md.strip()}],
            }
        )

    return rich_text


def md_to_mrkdwn(md):
    # Convert bold and italic text (bold first to avoid conflicts)
    md = re.sub(r"\*\*\*(.*?)\*\*\*", r"***\1***", md)  # Bold and italic
    md = re.sub(r"\*\*(.*?)\*\*", r"*\1*", md)  # Bold
    md = re.sub(r"\b\*(.*?)\*\b", r"_\1_", md)  # Italic
    # Convert strikethrough text
    md = re.sub(r"~~(.*?)~~", r"~\1~", md)
    # Convert inline code
    md = re.sub(r"`(.*?)`", r"`\1`", md)
    # Convert links
    md = re.sub(r"\[(.*?)\]\((.*?)\)", r"<\2|\1>", md)
    # Convert blockquotes
    md = re.sub(r"^> (.*)", r"> \1", md, flags=re.MULTILINE)
    # Convert code blocks
    md = re.sub(r"```(.*?)```", r"```\1```", md, flags=re.DOTALL)
    # Convert unordered lists
    md = re.sub(r"^\s*-\s+(.*)", r"• \1", md, flags=re.MULTILINE)
    # Convert ordered lists
    md = re.sub(r"^\s*\d+\.\s+(.*)", r"1. \1", md, flags=re.MULTILINE)
    # Handle nested lists
    md = re.sub(r"(\n\s*)•", r"\1  •", md)
    md = re.sub(r"(\n\s*)1\.", r"\1  1.", md)
    return md
