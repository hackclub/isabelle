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
