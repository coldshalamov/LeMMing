from __future__ import annotations

from lemming.engine import _strip_fences


def test_simple_fence():
    raw = "preamble\n```json\n{\"foo\": \"bar\"}\n```\npostamble"
    expected = "{\"foo\": \"bar\"}"
    assert _strip_fences(raw) == expected


def test_fence_no_lang():
    raw = "```\ncontent\n```"
    expected = "content"
    assert _strip_fences(raw) == expected


def test_fence_with_newlines():
    raw = "```\nline1\nline2\n```"
    expected = "line1\nline2"
    assert _strip_fences(raw) == expected


def test_fence_carriage_returns():
    # The current implementation (and optimized one) should handle mixed newlines or CRLF
    raw = "pre\r\n```\r\ncontent\r\n```\r\npost"
    # Existing implementation preserves \r if split('\n') is used on a string with \r\n.
    expected = "content\r"
    assert _strip_fences(raw) == expected


def test_unclosed_fence():
    raw = "pre\n```\ncontent\nmore content"
    # Should take everything after the opening fence line
    expected = "content\nmore content"
    assert _strip_fences(raw) == expected


def test_nested_fences():
    # Should take the outer block
    raw = "pre\n```\nouter start\n```\ninner\n```\nouter end\n```\npost"
    # Existing implementation returns "outer start" because it stops at first closing fence.
    expected = "outer start"
    assert _strip_fences(raw) == expected


def test_multiple_sequential_fences():
    # Should take the first block
    raw = "pre\n```\nblock1\n```\ntext\n```\nblock2\n```"
    expected = "block1"
    assert _strip_fences(raw) == expected


def test_no_fences():
    raw = "just some text"
    assert _strip_fences(raw) == raw


def test_fence_not_at_start_of_line():
    # If ``` is inside a line, it is ignored.
    # We ensure there are NO valid start-of-line fences in this input.
    raw = "text ```json\ncontent\n end"
    assert _strip_fences(raw) == raw


def test_fence_indented():
    # Indented fences are ignored by startswith("```")
    raw = "  ```\ncontent\n  ```"
    assert _strip_fences(raw) == raw


def test_empty_block():
    raw = "```\n```"
    # Fix: Returns empty string (correctly strips fences)
    assert _strip_fences(raw) == ""

def test_empty_block_with_lang():
    raw = "```json\n```"
    # Fix: Returns empty string
    assert _strip_fences(raw) == ""
