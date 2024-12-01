from .env import env
from slack_sdk import WebClient
from urllib.parse import quote

import re

client = WebClient(token=env.slack_bot_token)
ZWSP = "\u200B"


def user_in_safehouse(user_id: str):
    sad_members = client.conversations_members(channel=env.slack_sad_channel)["members"]
    return user_id in sad_members


def parse_elements(elements):
    markdown = ""
    for element in elements:
        if element["type"] == "text":
            text = element["text"]
            if "style" in element:
                styles = element["style"]
                if styles.get("bold") and styles.get("italic"):
                    text = f"**_{text}_**"
                elif styles.get("bold"):
                    text = f"**{text}**"
                elif styles.get("italic"):
                    text = f"_{text}_"
                if styles.get("strike"):
                    text = f"~~{text}~~"
                if styles.get("code"):
                    text = f"`{text}`"
            markdown += text
        elif element["type"] == "link":
            markdown += f"[{element['text']}]({element['url']})"
        elif element["type"] == "user":
            markdown += f"<@{element['user_id']}>"
        elif element["type"] == "emoji":
            markdown += f":{element['name']}:"
        elif element["type"] == "channel":
            markdown += f"<#{element['channel_id']}>"
        elif element["type"] == "subteam":
            markdown += f"<!subteam^{element['subteam_id']}|{element['name']}>"
        elif element["type"] == "date":
            markdown += f"<!date^{element['timestamp']}^{element['format']}|{element['fallback']}>"
        elif element["type"] == "url":
            markdown += f"<{element['url']}>"
        elif element["type"] == "line_break":
            markdown += "\n"
        elif element["type"] == "usergroup":
            markdown += f"<!subteam^{element['usergroup_id']}>"
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


def parse_elements_to_mrkdwn(elements):
    mrkdwn = ""
    for element in elements:
        if element["type"] == "text":
            text = element["text"]
            if "style" in element:
                styles = element["style"]
                words = re.split(
                    r"(\s+)", text
                )  # Split by whitespace but keep the whitespace
                formatted_words = []
                for word in words:
                    if word.strip():  # Only apply formatting to non-whitespace words
                        if styles.get("bold") and styles.get("italic"):
                            word = f"*_{word.strip()}_*"
                        elif styles.get("bold"):
                            word = f"*{word.strip()}*"
                        elif styles.get("italic"):
                            word = f"_{word.strip()}_"
                        if styles.get("strike"):
                            word = f"~{word.strip()}~"
                        if styles.get("code"):
                            word = f"`{word.strip()}`"
                    formatted_words.append(word)
                text = "".join(formatted_words)  # Join without adding extra spaces
            mrkdwn += text
        elif element["type"] == "link":
            mrkdwn += f"<{element['url']}|{element['text']}>"
        elif element["type"] == "user":
            mrkdwn += f"<@{element['user_id']}>"
        elif element["type"] == "emoji":
            mrkdwn += f":{element['name']}:"
        elif element["type"] == "channel":
            mrkdwn += f"<#{element['channel_id']}>"
        elif element["type"] == "subteam":
            mrkdwn += f"<!subteam^{element['subteam_id']}|{element['name']}>"
        elif element["type"] == "date":
            mrkdwn += f"<!date^{element['timestamp']}^{element['format']}|{element['fallback']}>"
        elif element["type"] == "url":
            mrkdwn += f"<{element['url']}>"
        elif element["type"] == "line_break":
            mrkdwn += "\n"
        elif element["type"] == "usergroup":
            mrkdwn += f"<!subteam^{element['usergroup_id']}>"
    return mrkdwn


def rich_text_to_mrkdwn(data):
    mrkdwn = ""
    for block in data:
        if isinstance(block, dict) and block["type"] == "rich_text_section":
            mrkdwn += parse_elements_to_mrkdwn(block["elements"]) + "\n"
        elif isinstance(block, dict) and block["type"] == "rich_text_quote":
            mrkdwn += "> " + parse_elements_to_mrkdwn(block["elements"]) + "\n"
            # Handle nested lists within quotes
            mrkdwn += rich_text_to_mrkdwn(block["elements"])
        elif isinstance(block, dict) and block["type"] == "rich_text_preformatted":
            mrkdwn += "```\n" + parse_elements_to_mrkdwn(block["elements"]) + "\n```\n"
        elif isinstance(block, dict) and block["type"] == "rich_text_list":
            for item in block["elements"]:
                mrkdwn += f"- {parse_elements_to_mrkdwn(item['elements'])}\n"
                # Recursively parse nested lists
                if "elements" in item:
                    mrkdwn += rich_text_to_mrkdwn(item["elements"])
    return mrkdwn
