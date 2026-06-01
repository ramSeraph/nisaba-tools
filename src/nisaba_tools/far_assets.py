from __future__ import annotations

from nisaba_tools.languages import (
    LANGUAGE_DEFINITION_BY_LANGUAGE,
    SCRIPT_BY_KEY,
)

UPSTREAM_COMMIT_ID = "fe8f9c"
RELEASES_DOWNLOAD_BASE_URL = "https://github.com/ramSeraph/nisaba/releases/download"

DEFAULT_RELEASE_TAG = f"brahmic-upstream-{UPSTREAM_COMMIT_ID}"
ABJAD_DEFAULT_RELEASE_TAG = f"abjad_alphabet-upstream-{UPSTREAM_COMMIT_ID}"
NATURAL_ROMANIZATION_RELEASE_TAG = (
    f"natural_translit-romanization-upstream-{UPSTREAM_COMMIT_ID}"
)
NATURAL_G2P_RELEASE_TAG = f"natural_translit-g2p-upstream-{UPSTREAM_COMMIT_ID}"
NATURAL_DEROMANIZATION_RELEASE_TAG = (
    f"natural_translit-deromanization-upstream-{UPSTREAM_COMMIT_ID}"
)
_RELEASE_BASE_URL = f"{RELEASES_DOWNLOAD_BASE_URL}/{DEFAULT_RELEASE_TAG}"
_ABJAD_RELEASE_BASE_URL = f"{RELEASES_DOWNLOAD_BASE_URL}/{ABJAD_DEFAULT_RELEASE_TAG}"
_NATURAL_ROMANIZATION_RELEASE_BASE_URL = (
    f"{RELEASES_DOWNLOAD_BASE_URL}/{NATURAL_ROMANIZATION_RELEASE_TAG}"
)
_NATURAL_G2P_RELEASE_BASE_URL = (
    f"{RELEASES_DOWNLOAD_BASE_URL}/{NATURAL_G2P_RELEASE_TAG}"
)
_NATURAL_DEROMANIZATION_RELEASE_BASE_URL = (
    f"{RELEASES_DOWNLOAD_BASE_URL}/{NATURAL_DEROMANIZATION_RELEASE_TAG}"
)

DEFAULT_WELLFORMED_FAR_URL = f"{_RELEASE_BASE_URL}/wellformed.far"
DEFAULT_READING_NORM_FAR_URL = f"{_RELEASE_BASE_URL}/reading_norm.far"
DEFAULT_FIXED_FAR_URL = f"{_RELEASE_BASE_URL}/fixed.far"
DEFAULT_ISO_FAR_URL = f"{_RELEASE_BASE_URL}/iso.far"
DEFAULT_REVERSIBLE_ROMAN_FAR_URL = f"{_ABJAD_RELEASE_BASE_URL}/reversible_roman.far"
DEFAULT_EN_SPELLOUT_FAR_URL = (
    f"{_NATURAL_DEROMANIZATION_RELEASE_BASE_URL}/en_spellout.far"
)

_VISUAL_NORM_ASSET_NAMES = {
    "AS": "visual_norm.Beng.as.far",
    "BENG": "visual_norm.Beng.far",
    "BN": "visual_norm.Beng.bn.far",
    "BUGI": "visual_norm.Bugi.far",
    "DEVA": "visual_norm.Deva.far",
    "GUJR": "visual_norm.Gujr.far",
    "GURU": "visual_norm.Guru.far",
    "KNDA": "visual_norm.Knda.far",
    "LEPC": "visual_norm.Lepc.far",
    "LIMB": "visual_norm.Limb.far",
    "MLYM": "visual_norm.Mlym.far",
    "MTEI": "visual_norm.Mtei.far",
    "NEWA": "visual_norm.Newa.far",
    "ORYA": "visual_norm.Orya.far",
    "SINH": "visual_norm.Sinh.far",
    "SYLO": "visual_norm.Sylo.far",
    "TAKR": "visual_norm.Takr.far",
    "TAML": "visual_norm.Taml.far",
    "TELU": "visual_norm.Telu.far",
    "TGLG": "visual_norm.Tglg.far",
    "THAA": "visual_norm.Thaa.far",
    "TIRH": "visual_norm.Tirh.far",
}

_READING_NORM_ASSET_NAMES = {
    "BENG": "reading_norm.Beng.far",
    "HI": "reading_norm.Deva.hi.far",
    "LEPC": "reading_norm.Lepc.far",
    "MLYM": "reading_norm.Mlym.far",
}

_ABJAD_VISUAL_NORM_ASSET_NAMES = {
    "AR": "visual_norm.Arab.ar.far",
    "AZB": "visual_norm.Arab.azb.far",
    "BAL": "visual_norm.Arab.bal.far",
    "CKB": "visual_norm.Arab.ckb.far",
    "FA": "visual_norm.Arab.fa.far",
    "KS": "visual_norm.Arab.ks.far",
    "MS": "visual_norm.Arab.ms.far",
    "PA": "visual_norm.Arab.pa.far",
    "PRS": "visual_norm.Arab.prs.far",
    "PS": "visual_norm.Arab.ps.far",
    "SD": "visual_norm.Arab.sd.far",
    "UG": "visual_norm.Arab.ug.far",
    "UR": "visual_norm.Arab.ur.far",
    "UZ": "visual_norm.Arab.uz.far",
}

_ABJAD_READING_NORM_ASSET_NAMES = {
    "AR": "reading_norm.Arab.ar.far",
    "AZB": "reading_norm.Arab.azb.far",
    "BAL": "reading_norm.Arab.bal.far",
    "CKB": "reading_norm.Arab.ckb.far",
    "FA": "reading_norm.Arab.fa.far",
    "KS": "reading_norm.Arab.ks.far",
    "MS": "reading_norm.Arab.ms.far",
    "PA": "reading_norm.Arab.pa.far",
    "PRS": "reading_norm.Arab.prs.far",
    "PS": "reading_norm.Arab.ps.far",
    "SD": "reading_norm.Arab.sd.far",
    "UG": "reading_norm.Arab.ug.far",
    "UR": "reading_norm.Arab.ur.far",
    "UZ": "reading_norm.Arab.uz.far",
}

_NATURAL_ROMANIZATION_SCHEMES = frozenset({"nat", "psac", "psaf"})


def _language_definition_or_raise(language: str, feature_name: str):
    definition = LANGUAGE_DEFINITION_BY_LANGUAGE.get(language)
    if definition is None:
        raise ValueError(f"No default {feature_name} asset for language {language}")
    return definition


def default_visual_norm_far_url(key: str) -> str:
    asset_name = _VISUAL_NORM_ASSET_NAMES.get(key)
    if asset_name is not None:
        return f"{_RELEASE_BASE_URL}/{asset_name}"
    asset_name = _ABJAD_VISUAL_NORM_ASSET_NAMES.get(key)
    if asset_name is None:
        raise ValueError(f"No default visual_norm FAR asset for key {key}")
    return f"{_ABJAD_RELEASE_BASE_URL}/{asset_name}"


def default_reading_norm_far_url(key: str) -> str:
    asset_name = _READING_NORM_ASSET_NAMES.get(key)
    if asset_name is not None:
        return f"{_RELEASE_BASE_URL}/{asset_name}"
    asset_name = _ABJAD_READING_NORM_ASSET_NAMES.get(key)
    if asset_name is None:
        raise ValueError(f"No default reading_norm FAR asset for key {key}")
    return f"{_ABJAD_RELEASE_BASE_URL}/{asset_name}"


def default_natural_roman_far_url(language: str, scheme: str) -> str:
    definition = _language_definition_or_raise(language, "natural romanization FAR")
    if not definition.translit_support.natural_roman:
        raise ValueError(
            f"No default natural romanization FAR asset for language {language}"
        )
    if scheme not in _NATURAL_ROMANIZATION_SCHEMES:
        raise ValueError(
            f"No default natural romanization FAR asset for language {language} "
            f"and scheme {scheme}"
        )
    asset_name = f"{definition.language}_iso_{scheme}.far"
    return f"{_NATURAL_ROMANIZATION_RELEASE_BASE_URL}/{asset_name}"


def default_ipa_far_url(language: str) -> str:
    definition = _language_definition_or_raise(language, "IPA FAR")
    if not definition.translit_support.ipa:
        raise ValueError(f"No default IPA FAR asset for language {language}")
    asset_name = f"{definition.language}_iso_ipa.far"
    return f"{_NATURAL_G2P_RELEASE_BASE_URL}/{asset_name}"


def default_natural_deroman_far_url(language: str, target: str) -> str:
    definition = _language_definition_or_raise(language, "natural deromanization FAR")
    if target not in definition.translit_support.deroman_targets:
        raise ValueError(
            f"No default natural deromanization FAR asset for language {language} "
            f"and target {target}"
        )
    if target == "script":
        target_name = SCRIPT_BY_KEY[definition.script_key].script_subtag.lower()
    else:
        target_name = target
    asset_name = f"{definition.language}_{target_name}.far"
    return f"{_NATURAL_DEROMANIZATION_RELEASE_BASE_URL}/{asset_name}"


def default_english_spellout_far_key(language: str) -> str:
    definition = _language_definition_or_raise(language, "English spellout FAR key")
    if not definition.translit_support.english_spellout:
        raise ValueError(f"No default English spellout FAR key for language {language}")
    return f"{definition.language.split('-', 1)[0].upper()}_{definition.script_key}"
