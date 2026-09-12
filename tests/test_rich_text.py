import json

import pytest

from isabelle.utils.rich_text import column_to_markdown
from isabelle.utils.rich_text import from_rich_text_column
from isabelle.utils.rich_text import to_rich_text_column

TEXT = "Venue fell through at short notice."


class TestToRichTextColumn:
    def test_wraps_plain_text_in_the_canonical_shape(self):
        parsed = json.loads(to_rich_text_column(TEXT))
        assert parsed["type"] == "rich_text"
        assert parsed["elements"][0]["elements"][0]["text"] == TEXT

    def test_passes_an_elements_list_through(self):
        elements = [
            {"type": "rich_text_section", "elements": [{"type": "text", "text": "hi"}]}
        ]
        assert json.loads(to_rich_text_column(elements))["elements"] == elements


class TestFromRichTextColumn:
    def test_reads_the_canonical_shape(self):
        assert from_rich_text_column(to_rich_text_column(TEXT))["type"] == "rich_text"

    def test_wraps_a_bare_elements_list(self):
        value = json.dumps([{"type": "rich_text_section", "elements": []}])
        assert from_rich_text_column(value)["type"] == "rich_text"

    def test_synthesises_from_a_legacy_plain_string(self):
        block = from_rich_text_column("cancelled because of the weather")
        assert block["elements"][0]["elements"][0]["text"] == (
            "cancelled because of the weather"
        )

    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_returns_none_for_nothing(self, value):
        assert from_rich_text_column(value) is None

    def test_accepts_an_already_parsed_dict(self):
        block = {"type": "rich_text", "elements": []}
        assert from_rich_text_column(block) is block


class TestColumnToMarkdown:
    def test_round_trips_plain_text(self):
        assert column_to_markdown(to_rich_text_column(TEXT)) == TEXT

    def test_round_trips_a_legacy_plain_string(self):
        assert column_to_markdown(TEXT) == TEXT

    def test_returns_none_for_nothing(self):
        assert column_to_markdown(None) is None

    def test_does_not_raise_on_malformed_json(self):
        assert column_to_markdown('{"type": "rich_text", "elements": ') is not None
