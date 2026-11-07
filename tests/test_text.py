import pytest

from bot.services.text import split_text


def test_split_text_returns_empty_list_for_blank_text() -> None:
    assert split_text("   ", 100) == []


def test_split_text_keeps_short_text_whole() -> None:
    assert split_text("short text", 100) == ["short text"]


def test_split_text_prefers_paragraph_boundary() -> None:
    text = "First paragraph.\n\nSecond paragraph."
    assert split_text(text, 20) == ["First paragraph.", "Second paragraph."]


def test_split_text_hard_cuts_when_no_boundary_exists() -> None:
    chunks = split_text("a" * 25, 10)
    assert chunks == ["a" * 10, "a" * 10, "a" * 5]


def test_split_text_rejects_invalid_chunk_size() -> None:
    with pytest.raises(ValueError):
        split_text("text", 0)
