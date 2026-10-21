"""§5A fidelity counts the Markdown source without its grammar (21.10.2026)."""
from app.builder import _source_word_char_counts


def test_block_markers_are_not_counted_as_text():
    """A form with a stamp box failed fidelity: '[[BOX:3]]' and '[[/BOX]]' were counted as source characters."""
    plain = "# 1 Печат | Stamp\nПечат ||| Stamp\n"
    boxed = "# 1 Печат | Stamp\n[[BOX:3]]\nПечат ||| Stamp\n[[/BOX]]\n[[PAGEBREAK]]\n"
    assert _source_word_char_counts(boxed) == _source_word_char_counts(plain)
