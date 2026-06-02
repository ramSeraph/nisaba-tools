# nisaba-tools

[![PyPI - Latest version](https://img.shields.io/pypi/v/nisaba-tools)](https://pypi.org/project/nisaba-tools/) [![GitHub Tag](https://img.shields.io/github/v/tag/ramSeraph/nisaba-tools?filter=v*)](https://github.com/ramSeraph/nisaba-tools/releases/latest)

`nisaba-tools` provides a small Python API for
[`Nisaba`](https://github.com/google-research/nisaba) normalization and
transliteration FARs:

- Brahmic
  [`visual_norm`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#visual_norm),
  `reading_norm`,
  [`iso`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#iso),
  [`fixed`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#fixed),
  [`natural_translit` romanization](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#romanization),
  [`deromanization`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#deromanization),
  [`IPA transcription`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#phonological-transcription),
  and
  [`wellformed`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#wellformed)
- English letter spellout for selected Brahmic and Arabic-script languages
- Abjad/alphabet `visual_norm`, `reading_norm`, and
  [`reversible_roman`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/abjad_alphabet/README.md#reversible-romanization)

This project is **not affiliated with
[`Nisaba`](https://github.com/google-research/nisaba)**. It is a convenience wrapper
around a useful upstream project whose Bazel-centric build and packaging are
harder to consume directly from a small Python package.

People should not hold the
[`Nisaba`](https://github.com/google-research/nisaba) maintainers responsible for breakages in this
wrapper, its packaging, or these convenience release assets.

This wrapper exists because
[`Nisaba`](https://github.com/google-research/nisaba) exposes useful
functionality that was not readily available elsewhere in a small Python
package, especially its visual
normalization, reading normalization, and well-formedness checks.

It uses byte-mode FAR assets from these releases in
[`ramSeraph/nisaba`](https://github.com/ramSeraph/nisaba) by default:

- [`brahmic-upstream-fe8f9c`](https://github.com/ramSeraph/nisaba/releases/tag/brahmic-upstream-fe8f9c)
- [`abjad_alphabet-upstream-fe8f9c`](https://github.com/ramSeraph/nisaba/releases/tag/abjad_alphabet-upstream-fe8f9c)
- [`natural_translit-romanization-upstream-fe8f9c`](https://github.com/ramSeraph/nisaba/releases/tag/natural_translit-romanization-upstream-fe8f9c)
- [`natural_translit-g2p-upstream-fe8f9c`](https://github.com/ramSeraph/nisaba/releases/tag/natural_translit-g2p-upstream-fe8f9c)
- [`natural_translit-deromanization-upstream-fe8f9c`](https://github.com/ramSeraph/nisaba/releases/tag/natural_translit-deromanization-upstream-fe8f9c)

Default assets include:

- Brahmic per-script or per-language
  [`visual_norm.*.far`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#visual_norm)
  assets such as `visual_norm.Deva.far` or `visual_norm.Beng.bn.far`
- Brahmic per-script or per-language `reading_norm.*.far` assets where
  [`Nisaba`](https://github.com/google-research/nisaba) publishes them, such as
  `reading_norm.Beng.far` or `reading_norm.Deva.hi.far`
- Abjad per-language `visual_norm.Arab.<lang>.far` assets such as
  `visual_norm.Arab.ur.far` or `visual_norm.Arab.fa.far`
- Abjad per-language `reading_norm.Arab.<lang>.far` assets such as
  `reading_norm.Arab.ur.far` or `reading_norm.Arab.fa.far`
- combined
  [`reversible_roman.far`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/abjad_alphabet/README.md#reversible-romanization)
- combined
  [`iso.far`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#iso)
- combined
  [`fixed.far`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#fixed)
- per-language natural-translit
  [romanization](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#romanization)
  FARs such as `hi_iso_nat.far`, `hi_iso_psac.far`, and `hi_iso_psaf.far`
- per-language natural-translit
  [IPA](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#phonological-transcription)
  FARs such as `hi_iso_ipa.far`
- per-language natural-translit
  [deromanization](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#deromanization)
  FARs such as `hi_deva.far`, `hi_iso.far`, `ta_taml.far`, and `ta_iso.far`
- combined
  [`en_spellout.far`](https://github.com/google-research/nisaba/blob/main/nisaba/scripts/natural_translit/README.md#L83-L86)
- [`wellformed.far`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#wellformed)

## Requirements

- Python 3.13
- `rustfst-python`

`nisaba-tools` currently depends on `rustfst-python`, and the practical Python
version requirement comes from that upstream package rather than from
[`Nisaba`](https://github.com/google-research/nisaba)
itself. Upstream currently declares `requires-python = ">=3.13,<3.14"` and is
only being published with Python 3.13 wheels on some Linux/macOS targets and no
source distribution, so Python 3.13 is required for installation here. See the
upstream issue:
[`garvys-org/rustfst#301`](https://github.com/garvys-org/rustfst/issues/301).
This package uses `rustfst` rather than the `openfst`/`pynini` stack partly
because packaging and installation are also much harder to rely on there.

If upstream packaging improves, this requirement can likely be relaxed later.

## Install

```bash
uv python install 3.13
uv venv --python 3.13
uv sync --python 3.13
```

If you prefer not to activate the virtual environment, you can pin the version
per command with `uv run`:

```bash
uv run --python 3.13 python -c "from nisaba_tools import visual_normalize; print(visual_normalize('क़', language='hi'))"
```

## Development checks

```bash
uv run --python 3.13 --extra dev ruff check .
uv run --python 3.13 --extra dev ruff format --check .
uv run --python 3.13 --extra dev python -m pytest
```

## FAR caching

Downloaded FAR assets are cached on disk by default and reused across
processes. Every public transliterator/normalizer accepts:

- `disk_cache=True` (default) to use the OS cache directory
- `disk_cache=<path>` to use a specific persistent cache directory
- `disk_cache=False` to use a per-process temporary cache directory

The default persistent cache location is:

- macOS: `~/Library/Caches/nisaba-tools`
- Windows: `%LOCALAPPDATA%\\nisaba-tools`
- Linux/other Unix: `$XDG_CACHE_HOME/nisaba-tools` or `~/.cache/nisaba-tools`

Cache downloads are written to a unique temporary file in the chosen cache
directory and then atomically moved into place, so concurrent processes can
share the same persistent cache safely even if they occasionally duplicate a
download.

## Brahmic

These APIs use canonical language or script tags such as `hi`, `ta`, or
`und-Deva`. Script guessing is best-effort: it can infer a supported script
like `DEVA` or `BENG`, but it cannot distinguish Assamese from Bengali
automatically, so pass `language="as"` or `language="bn"` when that matters.

### Visual normalization

`visual_normalize(...)` is the explicit source-side normalization API. Upstream
`visual_norm` includes NFC internally and then applies broader script-specific
visual-normalization rewrites.

By default, the package prefers smaller standalone `visual_norm.*.far` assets
instead of the larger combined `visual_norm.far` when
[`Nisaba`](https://github.com/google-research/nisaba) publishes them.

```python
from nisaba_tools import visual_normalize

normalized = visual_normalize("क़", language="hi")
```

```python
from nisaba_tools import VisualNormalizer

result = VisualNormalizer().normalize("क़", language="hi")

print(result.normalized_text)
print(result.resolved_language)
```

### Well-formedness

`is_wellformed(...)` is currently Brahmic-only. It applies `visual_norm`
automatically before checking well-formedness, and the default release surface
is the combined byte-mode `wellformed.far`.

```python
from nisaba_tools import is_wellformed

ok = is_wellformed("क़", language="hi")
```

```python
from nisaba_tools import WellFormednessChecker

result = WellFormednessChecker().check("क़", language="hi")

print(result.is_wellformed)
print(result.resolved_language)
```

### Reading normalization

`reading_normalize(...)` applies `visual_norm` before `reading_norm` by default,
matching the intended pipeline even though the upstream `reading_norm` FARs do
not currently compose that preprocessing step themselves.

By default, the package prefers smaller standalone `reading_norm.*.far` assets
when [`Nisaba`](https://github.com/google-research/nisaba) publishes them. For
Brahmic, the current default releases cover Bengali script, Malayalam, Lepcha,
and Hindi-in-Devanagari.

```python
from nisaba_tools import reading_normalize

reading = reading_normalize("क़", language="hi")
raw_reading = reading_normalize("क़", language="hi", apply_visual_norm=False)
```

```python
from nisaba_tools import ReadingNormalizer

normalizer = ReadingNormalizer()
reading = normalizer.normalize("क़", language="hi")
raw_reading = normalizer.normalize("क़", language="hi", apply_visual_norm=False)

print(reading.normalized_text)
print(raw_reading.normalized_text)
```

### ISO transliteration

`to_iso(...)` and `from_iso(...)` are currently Brahmic-only. `to_iso(...)`
applies `visual_norm` before `FROM_*` by default because upstream `iso.far`
already includes NFC but not the broader script-specific `visual_norm`
rewrites in the native-to-ISO direction. That means `to_iso(...)` output is
still NFC-normalized even if you disable the explicit `visual_norm` prepass.
`from_iso(...)` requires an explicit target language or script.

The default release surface is the combined byte-mode `iso.far`.

```python
from nisaba_tools import from_iso, to_iso

iso_text = to_iso("क़", language="hi")
native_text = from_iso(iso_text, language="hi")
raw_iso = to_iso("क़", language="hi", apply_visual_norm=False)
```

```python
from nisaba_tools import IsoTransliterator

transliterator = IsoTransliterator()
to_iso_result = transliterator.transliterate_to_iso("क़", language="hi")
from_iso_result = transliterator.transliterate_from_iso(
    to_iso_result.output_text or "",
    language="hi",
)

print(to_iso_result.output_text)
print(from_iso_result.output_text)
```

### Brahmic script-to-script transliteration

`brahmic_transliterate(...)` is currently Brahmic-only. It composes
`to_iso(...) -> from_iso(...)`, so it also applies source-side `visual_norm`
automatically.

If you enable `apply_reading_norm=True`, pass an explicit `source_language=`
when language-specific source rules matter, such as Hindi `reading_norm`.

```python
from nisaba_tools import brahmic_transliterate

telugu_text = brahmic_transliterate(
    "अन्त",
    source_language="hi",
    target_language="te",
    apply_reading_norm=True,
)
```

```python
from nisaba_tools import BrahmicTransliterator

result = BrahmicTransliterator().transliterate(
    "अन्त",
    source_language="hi",
    target_language="te",
    apply_reading_norm=True,
)

print(result.output_text)
print(result.iso_text)
```

### Fixed transliteration

`fixed_transliterate(...)` is currently Brahmic-only. It requires an explicit
language or script because the Latin-script input does not identify the target
Brahmic script. It also accepts a `scheme=` parameter. For Malayalam, it
defaults to
[`Mozhi`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/brahmic/README.md#fixed).

The default release surface is the combined byte-mode `fixed.far`, and the
current upstream `fixed.far` only contains `MLYM`, so default fixed-rule
transliteration is currently Malayalam-only unless you pass a custom FAR.

```python
from nisaba_tools import fixed_transliterate

fixed_text = fixed_transliterate("m", language="ml", scheme="Mozhi")
```

```python
from nisaba_tools import FixedTransliterator

result = FixedTransliterator().transliterate("m", language="ml", scheme="Mozhi")

print(result.output_text)
print(result.scheme)
```

### Natural romanization

Natural-translit romanization is a separate Brahmic romanization surface built
on [`Nisaba`](https://github.com/google-research/nisaba)'s
[`natural_translit` romanization
docs](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#romanization)
and grammars. Upstream published grammars are **ISO-input** grammars, but the
convenience APIs in this package start from either native script or ISO:

- `natural_romanize(...)` composes
  `to_iso(...) -> natural_romanize_from_iso(...)`
- `natural_romanize_from_iso(...)` starts from
  [`Nisaba`](https://github.com/google-research/nisaba) ISO text

The default release assets currently cover `bn`, `gu`, `hi`, `kn`, `ml`, `mr`,
`pa`, `ta`, and `te`. Pass an explicit language code like `hi`, `ml`, or `ta`;
a script-only tag like `und-Deva` is not enough to choose a language-specific
romanization asset.

Available schemes:

- [`nat`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/brahmic/README.md#nat)
  = natural everyday romanization, the default
- [`psac`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/brahmic/README.md#psac)
  = Pan South Asian coarse-grained romanization
- [`psaf`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/brahmic/README.md#psaf)
  = Pan South Asian fine-grained romanization

For example, [`Nisaba`](https://github.com/google-research/nisaba)'s docs use
Hindi `āṭīna` to illustrate the difference:
[`nat`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/brahmic/README.md#nat)
might look like `ateen`,
[`psac`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/brahmic/README.md#psac)
like `atin`, and
[`psaf`](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/brahmic/README.md#psaf)
like `aatiin`.

[`Nisaba`](https://github.com/google-research/nisaba) ISO is a useful shared
Brahmic transliteration layer, but it is not a language-agnostic promise that
every downstream grammar will interpret a given ISO string the same way. The
release assets are per-language byte-mode `*_iso_nat.far`, `*_iso_psac.far`,
and `*_iso_psaf.far` files.

```python
from nisaba_tools import natural_romanize, natural_romanize_from_iso

nat_from_script = natural_romanize("अटीना", language="hi")
nat_from_iso = natural_romanize_from_iso("āṭīna", language="hi", scheme="psac")
```

```python
from nisaba_tools import NaturalRomanTransliterator

transliterator = NaturalRomanTransliterator()
script_result = transliterator.transliterate("अटीना", language="hi")
iso_result = transliterator.transliterate_iso("āṭīna", language="hi", scheme="psac")

print(script_result.output_text)
print(iso_result.output_text)
```

### IPA transcription

IPA transcription is a separate
[`natural_translit` phonological-transcription
surface](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#phonological-transcription).
Upstream published grammars are also **ISO-input** grammars, but the
convenience APIs in this package start from either native script or ISO:

- `to_ipa(...)` composes `to_iso(...) -> to_ipa_from_iso(...)`
- `to_ipa_from_iso(...)` starts from
  [`Nisaba`](https://github.com/google-research/nisaba) ISO text

The default IPA release assets cover `bn`, `gu`, `hi`, `kn`, `ml`, `mr`, `pa`,
`ta`, and `te`. Pass an explicit language code like `hi`, `ml`, or `ta`; a
script-only tag like `und-Deva` is not enough to choose a language-specific
asset. The release assets are per-language byte-mode `*_iso_ipa.far` files with
`ISO_TO_IPA`.

This is best thought of as
[`Nisaba`](https://github.com/google-research/nisaba)'s
transliteration-oriented phonological transcription layer, not a general
high-coverage G2P system for every spelling or pronunciation edge case.

```python
from nisaba_tools import to_ipa, to_ipa_from_iso

ipa_from_script = to_ipa("अटीना", language="hi")
ipa_from_iso = to_ipa_from_iso("āṭīna", language="hi")
```

```python
from nisaba_tools import IpaTranscriber

transcriber = IpaTranscriber()
script_result = transcriber.transcribe("अटीना", language="hi")
iso_result = transcriber.transcribe_iso("āṭīna", language="hi")

print(script_result.output_text)
print(iso_result.output_text)
```

### Natural deromanization

Natural-translit deromanization is the reverse surface published in upstream
[`natural_translit`
deromanization](https://github.com/google-research/nisaba/tree/main/nisaba/scripts/natural_translit/README.md#deromanization).
It starts from Latin-script input and currently has two published output
targets:

- `natural_deromanize(...)` for Latin text to native script
- `natural_deromanize_to_iso(...)` for Latin text to
  [`Nisaba`](https://github.com/google-research/nisaba) ISO

The default deromanization release assets only cover `hi` and `ta`. Pass an
explicit language code like `hi` or `ta`; a script-only tag like `und-Deva` is
not enough to choose a language-specific asset. The release assets are
byte-mode `hi_deva.far`, `hi_iso.far`, `ta_taml.far`, and `ta_iso.far`.

Treat this as a plausible inference layer, not as a guaranteed inverse of
`natural_romanize(...)` or `to_iso(...)`. In particular,
`natural_deromanize_to_iso(...)` produces an inferred ISO transliteration from
Latin input, not a round-trip reconstruction of `to_iso(...)`.

```python
from nisaba_tools import natural_deromanize, natural_deromanize_to_iso

derom_script = natural_deromanize("namaste", language="hi")
derom_iso = natural_deromanize_to_iso("namaste", language="hi")
```

```python
from nisaba_tools import NaturalDeromanizer

deromanizer = NaturalDeromanizer()
script_result = deromanizer.transliterate("namaste", language="hi")
iso_result = deromanizer.transliterate_to_iso("namaste", language="hi")

print(script_result.output_text)
print(iso_result.output_text)
```

## Abjad

For Arabic-script normalization and reading normalization, pass an explicit
language code such as `ur`, `fa`, `ckb`, or `ar`; script guessing cannot choose
the right abjad rules.

### Visual normalization

`visual_normalize(...)` is also the explicit normalization API for abjad input.
Upstream `visual_norm` includes NFC internally there as well. By default, the
package prefers smaller standalone `visual_norm.Arab.*.far` assets instead of
the larger combined `visual_norm.far` when
[`Nisaba`](https://github.com/google-research/nisaba) publishes them.

```python
from nisaba_tools import visual_normalize

urdu_visual = visual_normalize("ك", language="ur")
```

```python
from nisaba_tools import VisualNormalizer

result = VisualNormalizer().normalize("ك", language="ur")

print(result.normalized_text)
print(result.resolved_language)
```

### Reading normalization

`reading_normalize(...)` applies `visual_norm` before `reading_norm` by default
for abjad input as well.

By default, the package prefers smaller standalone `reading_norm.*.far` assets
when [`Nisaba`](https://github.com/google-research/nisaba) publishes them. For
abjad, the current default releases cover published Arabic-script language
assets such as `ur`, `fa`, `ckb`, and `ar`.

```python
from nisaba_tools import reading_normalize

urdu_reading = reading_normalize("ك", language="ur")
```

```python
from nisaba_tools import ReadingNormalizer

result = ReadingNormalizer().normalize("ك", language="ur")

print(result.normalized_text)
print(result.resolved_language)
```

### Reversible romanization

`to_reversible_roman(...)` and `from_reversible_roman(...)` are currently
abjad/alphabet-only. The default release surface is the combined byte-mode
`reversible_roman.far` with `FROM_ARAB` and `TO_ARAB`.

`to_reversible_roman(...)` can infer `Arab` script text directly. `Arab` is the
script subtag; `ar` is Arabic the language. `from_reversible_roman(...)` can
default to `und-Arab` because the target script is always Arabic script.

```python
from nisaba_tools import from_reversible_roman, to_reversible_roman

urdu_roman = to_reversible_roman("اردو، اردو!")
urdu_script = from_reversible_roman(urdu_roman)
```

```python
from nisaba_tools import ReversibleRomanTransliterator

transliterator = ReversibleRomanTransliterator()
to_roman_result = transliterator.transliterate_to_roman("اردو، اردو!")
from_roman_result = transliterator.transliterate_from_roman(
    to_roman_result.output_text or ""
)

print(to_roman_result.output_text)
print(from_roman_result.output_text)
```

## Shared helpers

### English spellout

`english_spellout(...)` is a separate helper built from the combined byte-mode
[`en_spellout.far`](https://github.com/google-research/nisaba/blob/main/nisaba/scripts/natural_translit/README.md#L83-L86).
It spells out English or Latin letters as target-language letter names, which
is useful for acronyms or initialisms rather than normal lexical
transliteration.

The published English spellout grammar currently supports `bn`, `gu`, `hi`,
`kn`, `ml`, `mr`, `or`, `pa`, `sd`, `si`, `ta`, `te`, and `ur`.

```python
from nisaba_tools import english_spellout

english_letters = english_spellout("ATM", language="hi")
```

```python
from nisaba_tools import EnglishSpelloutTransliterator

result = EnglishSpelloutTransliterator().transliterate("ATM", language="hi")

print(result.output_text)
print(result.resolved_language)
```

### Support matrix

`api_support()` reports the languages covered by the package's default
published FAR assets. Returned identifiers are canonical language or script tags
such as `hi`, `ur`, or `und-Deva`; custom FARs can extend support beyond this
default matrix.

```python
from nisaba_tools import api_support

support = api_support()
to_ipa_support = support.support_for_api("to_ipa")

print(support.languages_for_api("to_ipa"))
print(support.languages_for_api("visual_normalize"))
print(support.apis_for_language("ta"))
print(support.apis_for_language("und-Deva"))
print(to_ipa_support.languages)
```

### Custom FAR reuse

The object APIs are also the easiest way to reuse explicit FAR paths across
many calls.

```python
from nisaba_tools import WellFormednessChecker

checker = WellFormednessChecker(
    visual_norm_far="/path/to/visual_norm.Beng.bn.far",
    wellformed_far="/path/to/wellformed.far",
)

result = checker.check("বাংলা", language="bn")

print(result.is_wellformed)
print(result.resolved_language)
```

## Citation

If you use `nisaba-tools` in academic writing or publications, please cite the
original [`Nisaba`](https://github.com/google-research/nisaba) authors and
papers rather than citing this wrapper alone.

See the upstream citation guidance in the original repository:
[`google-research/nisaba#citation`](https://github.com/google-research/nisaba#citation).

## License

`nisaba-tools` is licensed under the Apache License 2.0. See
[`LICENSE`](LICENSE).
