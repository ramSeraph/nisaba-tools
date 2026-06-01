from __future__ import annotations

import re

from nisaba_tools._natural_translit import _supported_language_examples
from nisaba_tools.languages import (
    SUPPORTED_DEROMANIZATION_LANGUAGES,
    SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES,
    SUPPORTED_IPA_LANGUAGES,
    SUPPORTED_NATURAL_ROMAN_LANGUAGES,
)


def _example_languages(example_text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"'([^']+)'", example_text))


def test_supported_language_examples_use_supported_languages() -> None:
    for supported_languages in (
        SUPPORTED_NATURAL_ROMAN_LANGUAGES,
        SUPPORTED_IPA_LANGUAGES,
        SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES,
    ):
        examples = _example_languages(_supported_language_examples(supported_languages))

        assert 2 <= len(examples) <= 3
        assert set(examples) <= supported_languages


def test_supported_language_examples_format_two_languages() -> None:
    assert _supported_language_examples(SUPPORTED_DEROMANIZATION_LANGUAGES) == (
        "'hi' or 'ta'"
    )
