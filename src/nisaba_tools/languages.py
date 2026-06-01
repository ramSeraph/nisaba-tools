"""Language and script resolution helpers.

This module keeps the canonical identifiers that the public APIs accept and
return:

- `language` is the user-facing canonical tag. Where possible this is a BCP47
  language tag such as `hi`, `ur`, or `pa-Arab`.
- When only a script is known, we use a script-only BCP47 tag such as
  `und-Deva` or `und-Arab`.
- `script_key` is the four-letter internal Nisaba key used by the release FARs,
  for example `DEVA`, `ARAB`, or `TAML`.
- `visual_norm_key` and `wellformed_key` are the upstream FAR keys for those
  features. Some are script-wide keys such as `DEVA`, while others are
  language-specific keys such as `HI` or `UR`.

The definition tables below are the single source of truth for accepted
languages, scripts, and aliases. Inputs such as `bn`, `bn-Beng`, and `bengali`
all resolve to the same entry.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class TransliterationSupport:
    natural_roman: bool = False
    ipa: bool = False
    deroman_targets: tuple[str, ...] = ()
    english_spellout: bool = False


def _translit_support(
    *,
    natural_roman: bool = False,
    ipa: bool = False,
    deroman_targets: tuple[str, ...] = (),
    english_spellout: bool = False,
) -> TransliterationSupport:
    return TransliterationSupport(
        natural_roman=natural_roman,
        ipa=ipa,
        deroman_targets=deroman_targets,
        english_spellout=english_spellout,
    )


@dataclass(frozen=True)
class ScriptDefinition:
    script_key: str
    script_subtag: str
    unicode_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolvedLanguage:
    """Canonical language/script resolution result.

    `language` is the canonical public tag, `script_key` is the internal
    release-asset script key, `visual_norm_key` and `wellformed_key` are the
    feature-specific FAR keys, `family` distinguishes Brahmic vs. Abjad assets,
    and `guessed` indicates that the script came from text inspection rather
    than an explicit user input.
    """

    language: str
    script_key: str
    visual_norm_key: str
    wellformed_key: str
    family: str
    guessed: bool


@dataclass(frozen=True)
class LanguageDefinition:
    language: str
    script_key: str
    aliases: tuple[str, ...] = ()
    visual_norm_key: str | None = None
    wellformed_key: str | None = None
    family: str | None = None
    translit_support: TransliterationSupport = TransliterationSupport()


# Canonical script definitions used throughout the module.
SCRIPT_DEFINITIONS = (
    ScriptDefinition("ARAB", "Arab", "ARABIC", aliases=()),  # Arabic script.
    ScriptDefinition(
        "BENG", "Beng", "BENGALI", aliases=("bengali-script",)
    ),  # Bengali script.
    ScriptDefinition(
        "BUGI", "Bugi", "BUGINESE", aliases=("buginese-script",)
    ),  # Buginese / Lontara script.
    ScriptDefinition(
        "DEVA", "Deva", "DEVANAGARI", aliases=("devanagari",)
    ),  # Devanagari script.
    ScriptDefinition("GUJR", "Gujr", "GUJARATI", aliases=()),  # Gujarati script.
    ScriptDefinition(
        "GURU", "Guru", "GURMUKHI", aliases=("gurmukhi",)
    ),  # Gurmukhi script.
    ScriptDefinition(
        "KNDA", "Knda", "KANNADA", aliases=("kannada-script",)
    ),  # Kannada script.
    ScriptDefinition("LEPC", "Lepc", "LEPCHA", aliases=()),  # Lepcha script.
    ScriptDefinition("LIMB", "Limb", "LIMBU", aliases=()),  # Limbu script.
    ScriptDefinition(
        "MLYM", "Mlym", "MALAYALAM", aliases=("malayalam-script",)
    ),  # Malayalam script.
    ScriptDefinition(
        "MTEI", "Mtei", "MEETEI MAYEK", aliases=()
    ),  # Meetei Mayek script.
    ScriptDefinition("NEWA", "Newa", "NEWA", aliases=()),  # Newa / Nepal Bhasa script.
    ScriptDefinition(
        "ORYA",
        "Orya",
        "ORIYA",
        aliases=("oriya-script", "odia-script"),
    ),  # Odia script; Unicode still uses the older "Oriya" name.
    ScriptDefinition(
        "SINH", "Sinh", "SINHALA", aliases=("sinh-script",)
    ),  # Sinhala script.
    ScriptDefinition(
        "SYLO", "Sylo", "SYLOTI NAGRI", aliases=()
    ),  # Syloti Nagri script.
    ScriptDefinition(
        "TGLG", "Tglg", "TAGALOG", aliases=()
    ),  # Tagalog / Baybayin script.
    ScriptDefinition("TAKR", "Takr", "TAKRI", aliases=()),  # Takri script.
    ScriptDefinition(
        "TAML", "Taml", "TAMIL", aliases=("tamil-script",)
    ),  # Tamil script.
    ScriptDefinition(
        "TELU", "Telu", "TELUGU", aliases=("telugu-script",)
    ),  # Telugu script.
    ScriptDefinition("THAA", "Thaa", "THAANA", aliases=()),  # Thaana script.
    ScriptDefinition(
        "TIRH", "Tirh", "TIRHUTA", aliases=("tirhuta",)
    ),  # Tirhuta / Mithilakshar script.
)

# Canonical language definitions used throughout the module.
LANGUAGE_DEFINITIONS = (
    LanguageDefinition(
        "as", "BENG", aliases=("as-Beng", "assamese")
    ),  # Assamese in Bengali script.
    LanguageDefinition(
        "ar",
        "ARAB",
        aliases=("ar-Arab", "arabic"),
        visual_norm_key="AR",
        wellformed_key="AR",
        family="abjad",
    ),  # Arabic in Arabic script.
    LanguageDefinition(
        "bn",
        "BENG",
        aliases=("bn-Beng", "bengali", "bangla"),
        visual_norm_key="BN",
        wellformed_key="BENG",
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Bengali / Bangla in Bengali script.
    LanguageDefinition(
        "azb",
        "ARAB",
        aliases=("azb-Arab", "south-azerbaijani"),
        visual_norm_key="AZB",
        wellformed_key="AZB",
        family="abjad",
    ),  # South Azerbaijani in Arabic script.
    LanguageDefinition(
        "bal",
        "ARAB",
        aliases=("bal-Arab", "balochi"),
        visual_norm_key="BAL",
        wellformed_key="BAL",
        family="abjad",
    ),  # Balochi in Arabic script.
    LanguageDefinition(
        "bug", "BUGI", aliases=("bug-Bugi", "buginese")
    ),  # Buginese in Buginese script.
    LanguageDefinition(
        "ckb",
        "ARAB",
        aliases=("ckb-Arab", "central-kurdish", "sorani"),
        visual_norm_key="CKB",
        wellformed_key="CKB",
        family="abjad",
    ),  # Central Kurdish / Sorani in Arabic script.
    LanguageDefinition(
        "doi", "DEVA", aliases=("doi-Deva", "dogri")
    ),  # Dogri in Devanagari script.
    LanguageDefinition(
        "dv", "THAA", aliases=("dv-Thaa", "thaana")
    ),  # Dhivehi in Thaana script.
    LanguageDefinition(
        "fa",
        "ARAB",
        aliases=("fa-Arab", "farsi", "persian"),
        visual_norm_key="FA",
        wellformed_key="FA",
        family="abjad",
    ),  # Persian / Farsi in Arabic script.
    LanguageDefinition(
        "gu",
        "GUJR",
        aliases=("gu-Gujr", "gujarati"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Gujarati in Gujarati script.
    LanguageDefinition(
        "hi",
        "DEVA",
        aliases=("hi-Deva", "hindi"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            deroman_targets=("script", "iso"),
            english_spellout=True,
        ),
    ),  # Hindi in Devanagari script.
    LanguageDefinition(
        "kn",
        "KNDA",
        aliases=("kn-Knda", "kannada"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Kannada in Kannada script.
    LanguageDefinition(
        "kok", "DEVA", aliases=("kok-Deva", "konkani")
    ),  # Konkani in Devanagari script.
    LanguageDefinition(
        "ks",
        "ARAB",
        aliases=("ks-Arab", "kashmiri"),
        visual_norm_key="KS",
        wellformed_key="KS",
        family="abjad",
    ),  # Kashmiri in Arabic script.
    LanguageDefinition(
        "lep", "LEPC", aliases=("lep-Lepc", "lepcha")
    ),  # Lepcha in Lepcha script.
    LanguageDefinition(
        "lif", "LIMB", aliases=("lif-Limb", "limbu")
    ),  # Limbu in Limbu script.
    LanguageDefinition(
        "mai", "DEVA", aliases=("mai-Deva", "maithili")
    ),  # Maithili in Devanagari script.
    LanguageDefinition(
        "ml",
        "MLYM",
        aliases=("ml-Mlym", "malayalam"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Malayalam in Malayalam script.
    LanguageDefinition(
        "ms",
        "ARAB",
        aliases=("ms-Arab", "jawi"),
        visual_norm_key="MS",
        wellformed_key="MS",
        family="abjad",
    ),  # Malay in Jawi (Arabic) script.
    LanguageDefinition(
        "mni",
        "MTEI",
        aliases=("mni-Mtei", "meetei", "meitei"),
    ),  # Meitei / Meetei Manipuri in Meetei Mayek script.
    LanguageDefinition(
        "mr",
        "DEVA",
        aliases=("mr-Deva", "marathi"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Marathi in Devanagari script.
    LanguageDefinition(
        "ne", "DEVA", aliases=("ne-Deva", "nepali")
    ),  # Nepali in Devanagari script.
    LanguageDefinition(
        "new", "NEWA", aliases=("new-Newa", "newa")
    ),  # Newa / Nepal Bhasa in Newa script.
    LanguageDefinition(
        "or",
        "ORYA",
        aliases=("or-Orya", "oria", "oriya", "odia"),
        translit_support=_translit_support(english_spellout=True),
    ),  # Odia / Oriya in Odia script.
    LanguageDefinition(
        "pa",
        "GURU",
        aliases=("pa-Guru", "punjabi"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Punjabi in Gurmukhi script.
    LanguageDefinition(
        "pa-Arab",
        "ARAB",
        aliases=("shahmukhi",),
        visual_norm_key="PA",
        wellformed_key="PA",
        family="abjad",
    ),  # Punjabi in Shahmukhi (Arabic) script.
    LanguageDefinition(
        "prs",
        "ARAB",
        aliases=("prs-Arab", "dari"),
        visual_norm_key="PRS",
        wellformed_key="PRS",
        family="abjad",
    ),  # Dari Persian in Arabic script.
    LanguageDefinition(
        "ps",
        "ARAB",
        aliases=("ps-Arab", "pashto"),
        visual_norm_key="PS",
        wellformed_key="PS",
        family="abjad",
    ),  # Pashto in Arabic script.
    LanguageDefinition(
        "sa", "DEVA", aliases=("sa-Deva", "sanskrit")
    ),  # Sanskrit in Devanagari script.
    LanguageDefinition(
        "sd",
        "ARAB",
        aliases=("sd-Arab", "sindhi"),
        visual_norm_key="SD",
        wellformed_key="SD",
        family="abjad",
        translit_support=_translit_support(english_spellout=True),
    ),  # Sindhi in Arabic script.
    LanguageDefinition(
        "si",
        "SINH",
        aliases=("si-Sinh", "sinhala"),
        translit_support=_translit_support(english_spellout=True),
    ),  # Sinhala in Sinhala script.
    LanguageDefinition(
        "syl",
        "SYLO",
        aliases=("syl-Sylo", "syloti", "syloti-nagri"),
    ),  # Sylheti in Syloti Nagri script.
    LanguageDefinition(
        "ta",
        "TAML",
        aliases=("ta-Taml", "tamil"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            deroman_targets=("script", "iso"),
            english_spellout=True,
        ),
    ),  # Tamil in Tamil script.
    LanguageDefinition(
        "te",
        "TELU",
        aliases=("te-Telu", "telugu"),
        translit_support=_translit_support(
            natural_roman=True,
            ipa=True,
            english_spellout=True,
        ),
    ),  # Telugu in Telugu script.
    LanguageDefinition(
        "tl", "TGLG", aliases=("tl-Tglg", "tagalog")
    ),  # Tagalog in Tagalog / Baybayin script.
    LanguageDefinition(
        "ug",
        "ARAB",
        aliases=("ug-Arab", "uighur", "uyghur"),
        visual_norm_key="UG",
        wellformed_key="UG",
        family="abjad",
    ),  # Uyghur in Arabic script.
    LanguageDefinition(
        "ur",
        "ARAB",
        aliases=("ur-Arab", "urdu"),
        visual_norm_key="UR",
        wellformed_key="UR",
        family="abjad",
        translit_support=_translit_support(english_spellout=True),
    ),  # Urdu in Arabic script.
    LanguageDefinition(
        "uz",
        "ARAB",
        aliases=("uz-Arab",),
        visual_norm_key="UZ",
        wellformed_key="UZ",
        family="abjad",
    ),  # Uzbek in Arabic script.
)

SCRIPT_BY_KEY = {definition.script_key: definition for definition in SCRIPT_DEFINITIONS}
LANGUAGE_DEFINITION_BY_LANGUAGE = {
    definition.language: definition for definition in LANGUAGE_DEFINITIONS
}

# Unicode character names use long script names such as "DEVANAGARI"; map them
# to the shorter internal script keys we use throughout the package.
UNICODE_SCRIPT_NAMES = {
    definition.unicode_name: definition.script_key for definition in SCRIPT_DEFINITIONS
}

# Internal script keys map to BCP47 script subtags used in public tags such as
# `und-Deva` and `und-Arab`.
SCRIPT_SUBTAGS = {
    definition.script_key: definition.script_subtag for definition in SCRIPT_DEFINITIONS
}


def normalized_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")


def script_language_tag(script_key: str) -> str:
    return f"und-{SCRIPT_SUBTAGS[script_key]}"


def script_family(script_key: str) -> str:
    return "abjad" if script_key == "ARAB" else "brahmic"


def _resolved(
    language: str,
    script_key: str,
    visual_norm_key: str | None = None,
    wellformed_key: str | None = None,
    family: str | None = None,
    *,
    guessed: bool = False,
) -> ResolvedLanguage:
    return ResolvedLanguage(
        language=language,
        script_key=script_key,
        visual_norm_key=visual_norm_key or script_key,
        wellformed_key=wellformed_key or script_key,
        family=family or script_family(script_key),
        guessed=guessed,
    )


def _resolve_script_definition(
    definition: ScriptDefinition, *, guessed: bool = False
) -> ResolvedLanguage:
    return _resolved(
        script_language_tag(definition.script_key),
        definition.script_key,
        guessed=guessed,
    )


def _resolve_language_definition(
    definition: LanguageDefinition, *, guessed: bool = False
) -> ResolvedLanguage:
    return _resolved(
        definition.language,
        definition.script_key,
        visual_norm_key=definition.visual_norm_key,
        wellformed_key=definition.wellformed_key,
        family=definition.family,
        guessed=guessed,
    )


CANONICAL_SCRIPT_RESOLUTIONS = tuple(
    _resolve_script_definition(definition) for definition in SCRIPT_DEFINITIONS
)
CANONICAL_LANGUAGE_RESOLUTIONS = tuple(
    _resolve_language_definition(definition) for definition in LANGUAGE_DEFINITIONS
)
CANONICAL_RESOLVED_LANGUAGES = tuple(
    sorted(
        (*CANONICAL_SCRIPT_RESOLUTIONS, *CANONICAL_LANGUAGE_RESOLUTIONS),
        key=lambda resolved: resolved.language,
    )
)

SCRIPT_RESOLUTION_BY_KEY = {
    resolved.script_key: resolved for resolved in CANONICAL_SCRIPT_RESOLUTIONS
}
LANGUAGE_RESOLUTION_BY_LANGUAGE = {
    resolved.language: resolved for resolved in CANONICAL_LANGUAGE_RESOLUTIONS
}
SUPPORTED_NATURAL_ROMAN_LANGUAGES = frozenset(
    definition.language
    for definition in LANGUAGE_DEFINITIONS
    if definition.translit_support.natural_roman
)
SUPPORTED_IPA_LANGUAGES = frozenset(
    definition.language
    for definition in LANGUAGE_DEFINITIONS
    if definition.translit_support.ipa
)
SUPPORTED_DEROMANIZATION_LANGUAGES = frozenset(
    definition.language
    for definition in LANGUAGE_DEFINITIONS
    if definition.translit_support.deroman_targets
)
SUPPORTED_ENGLISH_SPELLOUT_LANGUAGES = frozenset(
    definition.language
    for definition in LANGUAGE_DEFINITIONS
    if definition.translit_support.english_spellout
)


def _alias_lookup_items() -> list[tuple[str, ResolvedLanguage]]:
    items: list[tuple[str, ResolvedLanguage]] = []
    for definition in SCRIPT_DEFINITIONS:
        resolved = SCRIPT_RESOLUTION_BY_KEY[definition.script_key]
        items.extend(
            (
                alias,
                resolved,
            )
            for alias in (
                definition.script_key,
                definition.script_subtag,
                script_language_tag(definition.script_key),
                *definition.aliases,
            )
        )
    for definition in LANGUAGE_DEFINITIONS:
        resolved = LANGUAGE_RESOLUTION_BY_LANGUAGE[definition.language]
        items.extend(
            (alias, resolved) for alias in (definition.language, *definition.aliases)
        )
    return items


LANGUAGE_ALIASES = {
    normalized_alias(alias): resolved for alias, resolved in _alias_lookup_items()
}


def _resolve_alias(language: str) -> ResolvedLanguage:
    alias = normalized_alias(language)
    if alias not in LANGUAGE_ALIASES:
        raise ValueError(f"Unsupported language or script: {language}")
    return LANGUAGE_ALIASES[alias]


def guess_script_key(text: str) -> str | None:
    counts: dict[str, int] = {}
    for character in text:
        name = unicodedata.name(character, "")
        for unicode_name, script_key in UNICODE_SCRIPT_NAMES.items():
            if name.startswith(unicode_name):
                counts[script_key] = counts.get(script_key, 0) + 1
                break
    if not counts:
        return None
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None
    return ranked[0][0]


def resolve_language(language: str | None, text: str) -> ResolvedLanguage | None:
    if language is not None:
        return _resolve_alias(language)
    guessed_script = guess_script_key(text)
    if guessed_script is None:
        return None
    return _resolve_script_definition(SCRIPT_BY_KEY[guessed_script], guessed=True)


def resolve_explicit_language(
    language: str | None, *, purpose: str
) -> ResolvedLanguage:
    if language is None:
        raise ValueError(
            f"{purpose} requires an explicit language or script because the input "
            "does not identify the target script."
        )
    return _resolve_alias(language)
