from __future__ import annotations

from nisaba_tools.languages import normalized_alias


def test_normalized_alias_normalizes_case_spacing_and_separators() -> None:
    assert normalized_alias("HI") == "hi"
    assert normalized_alias(" hi_Deva ") == "hi-deva"
    assert normalized_alias("syloti nagri") == "syloti-nagri"
    assert normalized_alias("  Urdu---Arab  ") == "urdu-arab"
