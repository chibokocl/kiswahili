# Ki-Micheweni Grammar Engine

A comprehensive morphological and syntactic analysis engine for the Ki-Micheweni dialect of Kiswahili, implementing the full 18-ngeli system with semantic functions.

## Overview

This engine is based on the research by **Hamad Khamis Juma (2015)** on "Ngeli za Nomino za Ki-Micheweni" and implements advanced features not found in standard Kiswahili grammar tools:

- **Complete 18-ngeli system** (vs. the typical 16-class system)
- **Semantic function detection** (ukuzaji, udogoshaji, dharau, sifa nzuri)
- **Ngeli migration analysis** with explanations
- **Advanced phonological rules** (nasal mutation, vowel coalescence)
- **Context-aware morphological analysis**
- **Comprehensive agreement checking**

## Features

### 🏗️ Core Features
- **18 Ngeli Classes**: Full implementation including locative ngeli 16/17/18
- **Semantic Functions**: Automatic detection of augmentative, diminutive, and evaluative uses
- **Phonological Rules**: Proper handling of sound changes and morphological processes
- **Agreement Analysis**: KK (subject), KY (demonstrative), KV (adjective) agreement patterns
- **Migration Detection**: Identifies when words move between ngeli classes

### 🔍 Analysis Capabilities
- **Morphological Segmentation**: Prefix + root + extensions breakdown
- **Syntactic Analysis**: Kiima/kiarifu sentence structure identification
- **Verb Analysis**: Tense, aspect, and agreement marker extraction
- **Context Sensitivity**: Analysis adapts based on surrounding words
- **Confidence Scoring**: Reliability estimates for classifications

### 🛠️ Advanced Features
- **Zero Morpheme Handling**: Proper analysis of words with Ø- prefixes
- **Complex Verb Forms**: Multi-part tense and aspect combinations
- **Dialectal Variations**: Ki-Micheweni specific patterns vs. standard Kiswahili
- **Batch Processing**: Analyze multiple sentences efficiently
- **JSON Export**: Structured data output for integration

## Writing checker ("Kiswahili Grammarly")

```python
from kiswahili_engine import Checker
from kiswahili_engine.checker import apply_suggestions

text = "kitabu umeanguka. Watoto anacheza mpira. Alikwenda shule kila sikuu."
chk = Checker()
for issue in chk.check(text):
    print(issue.rule, issue.text, issue.start, issue.end, [s.text for s in issue.suggestions])
print(apply_suggestions(text, chk.check(text)))
# Kitabu kimeanguka. Watoto wanacheza mpira. Alikwenda shule kila siku.
```

Or from a shell: `python -m kiswahili_engine "Kitabu umeanguka."` (`--json` for machine output).

**Try it in a browser** (no installs, standard library only):

```bash
python -m kiswahili_engine.server        # then open http://127.0.0.1:8000
```

One page: type text, see highlighted issues with explanations, click a fix to apply it, and
look up any word (noun class, verb breakdown, adjective forms).

Each `Issue` has a character span, rule id, category, severity, an explanation in English
and Kiswahili, ranked suggestions and a confidence; `check(min_confidence=0.6)` filters.
Rules today: `AGR-SV` (subject-verb agreement), `AGR-NA` (noun + adjective/numeral/possessive/connective *-a*), `PREP-KWA` (*kwa* before a place after a verb of motion), `STD-IMP` (*enda* → *nenda*), `SPELL`, `CAP`. The checker is
precision-first: it deliberately skips patterns that are correct Kiswahili but look wrong
(animate nouns taking a-/wa-, respect plurals, adverbial nouns like *leo*, vocatives).

Measure it with `python tools/evaluate_checker.py`. See [ROADMAP.md](../ROADMAP.md) for what is
measured, what is not, and what comes next.

## Learning noun classes from text

The dictionary is incomplete (no *nyumba*, no *kituo*), so `python -m kiswahili_engine.learn`
learns classes from running text instead of a word list: for every word it counts the agreeing
words that follow it (*ya, cha, kizuri, changu, hiki*, a verb's subject marker) and keeps every
ngeli pair consistent with them. A noun seen with both *ya* and *za* can only be 9/10; one seen
only in the singular with *wa* stays ambiguous (1/2, 3/4, 11/10, 14/6), because those classes
share every singular form, and consumers accept a modifier that fits any candidate.

```bash
python -m kiswahili_engine.learn corpus.txt other.pdf -o learned.json --source-note "CC BY-SA ..."
python tools/evaluate_learner.py learned.json
```

`NounLexicon` uses the packaged model (`data/learned_noun_classes.json`, built from the Bible)
only for words the dictionary lacks. Against the dictionary, its candidate pairs include the
right one for 92% of shared words (single-candidate words: ~91% correct), and it classifies ~900
words the dictionary does not have. Use well-edited modern text: whatever the corpus treats as
correct becomes correct. Plain UTF-8 `.txt` is better than PDF. See `DATA_LICENSES.md`.

## Animacy

Animate nouns take a-/wa- agreement whatever their prefix (*kijana mzuri*, *simba anakuja*), so a
checker that flags *kitabu mzuri* must know *kitabu* is inanimate. The noun lexicon stores an
animacy flag derived from the opening words of each definition (*mtu…*, *mnyama…*, *aina ya ndege*
vs *chombo cha…*, *hali ya…*); only the flag is kept, never the definition.
`NounLexicon.is_inanimate(word)` is true when the dictionary lists no a-/wa- reading and no animate
sense. Both `AGR-SV` and `AGR-NA` use it, so *Kitabu mzuri* → *kizuri* and *Kitabu wa mtoto* → *cha*
are flagged while *Kijana mzuri* is left alone.

## Adjective lexicon and concord

`data/adjective_lexicon.json` (`tools/build_adjective_lexicon.py`) holds 61 inflecting stems
(dictionary `kv` entries plus a short hand-curated core of basics the school dictionary omits,
tagged `curated`) and ~650 invariable adjectives. `core/concord.py` generates every class form
(*-zuri* → mzuri, wazuri, mizuri, kizuri, nzuri ...), plus the connective *-a*, possessives and
*-ote*, and indexes them by surface form. The checker only suggests a generated form that is
also attested in the corpus.

## Verb lexicon

`VerbParser.from_kamusi()` (the engine default) loads ~3,700 verb roots from the same
dictionary, with transitivity and the extensions the dictionary attests for each root
(`tools/build_verb_lexicon.py`). Attested derivations outrank other root/extension splits.

## Verb morphology

`VerbParser` (`core/verb_morphology.py`) segments verbs by slot:

```
[NEG] SM [NEG2] [TAM] [REL] [OM] [ku] ROOT [EXT...] FV [REL-suffix]
```

```python
from kiswahili_engine import VerbParser

parser = VerbParser()
parser.best("hatupendi").segmentation()      # 'hatu-pend-i'
parser.best("anakula").segmentation()        # 'a-na-ku-l-a'
parser.best("atakupenda").object_marker      # 'ku'
for p in parser.parse("alipikiwa"):          # every plausible analysis, ranked
    print(p.segmentation(), round(p.score, 2))
```

Covers positive and negative tenses (na/li/me/ta/ka/ki/nge/ngali/ja/ku, habitual hu-),
subjunctive, infinitive, relatives (infixed and suffixed), object markers,
and the extensions applicative, stative, causative, reciprocal and passive with vowel
harmony. Not covered: reversive/positional extensions, reduplication, `amba-` relatives,
`-ile` perfect.

Verbs are ambiguous without a lexicon (is `pikia` a root, or `pik` + applicative?), so
`parse()` returns ranked alternatives. Pass a root lexicon to sharpen the ranking:

```python
parser = VerbParser.from_wordlist("swahili_corpus/swahili_words.txt")
engine = create_engine({"verb_lexicon_path": "swahili_corpus/swahili_words.txt"})
```

Run the tests with `python -m unittest discover -s kiswahili_engine/tests`.

## Noun lexicon

Prefix rules alone classify only ~23% of dictionary nouns correctly (they can't tell `mtoto`
1/2 from `mti` 3/4, or see that `chakula` is 7/8), so the engine looks nouns up in a lexicon
built from *Kamusi Teule ya Kiswahili* (`data/noun_lexicon.json`: ~13k headwords with
ngeli and explicit plurals; definitions are not stored). Unknown words fall back to the
prefix heuristics.

```python
from kiswahili_engine import NounLexicon

lex = NounLexicon.load()
lex.best("chakula")          # ngeli 7/8, singular
lex.candidates("mtoto")      # [('1/2','singular'), ('3/4','singular')]  ambiguous headword
lex.best("watoto").source    # 'plural' (explicit); derived plurals are 'plural_rule', lower confidence
```

When a noun has several readings, subject-verb agreement checks accept any reading that
agrees with the verb and say which one was used. To regenerate the data (needs poppler's
`pdftotext`):

```bash
python tools/build_noun_lexicon.py swahili_corpus/kamusi.pdf kiswahili_engine/data/noun_lexicon.json
```

Disable with `create_engine({"use_noun_lexicon": False})`. Known gaps: the dictionary has
no entry for some common nouns (e.g. `nyumba`), and ~130 entries are skipped because the
PDF's two-column layout separates the headword from its ngeli tag.

## Installation

```bash
# Clone or download the kiswahili_engine package
# Then install dependencies (if any)
pip install -r requirements.txt  # if requirements.txt exists
```

## Quick Start

```python
from kiswahili_engine import create_engine, analyze_sentence

# Create engine instance
engine = create_engine()

# Analyze a sentence
result = engine.analyze_sentence_enhanced("Mwalimu anasomesha watoto shuleni.")

# Print results
print(result['explanation'])

# Quick analysis function
result = analyze_sentence("Joka kubwa limmiza chura.")
```

## Basic Usage Examples

### Sentence Analysis
```python
from kiswahili_engine import create_engine

engine = create_engine()

# Standard sentence
result = engine.analyze_sentence_enhanced("Mtu anakuja nyumbani.")
print(f"Sentence type: {result['sentence_type']}")
print(f"Agreement: {'✅' if result['agreement'].subject_verb_agreement else '❌'}")

# Sentence with semantic function
result = engine.analyze_sentence_enhanced("Kipaka kidogo kinlala.")
# Detects 'udogoshaji' (diminutive) function
```

### Word Analysis
```python
# Analyze individual words
word_result = engine.analyze_word("mwalimu")
ngeli_info = word_result['ngeli_analysis']

print(f"Word: {word_result['word']}")
print(f"Ngeli: {ngeli_info.ngeli_class} ({ngeli_info.number})")
print(f"Confidence: {ngeli_info.confidence:.2f}")
```

### Agreement Checking
```python
# Check agreement between elements
agreement = engine.check_agreement("mtu", "anakuja")
print(f"Agreement: {'✅' if agreement['verb_agreement'] else '❌'}")

# With adjective
agreement = engine.check_agreement("mtu", "anakuja", "mzuri")
```

## Advanced Usage

### Custom Context Analysis
```python
# Provide context for better analysis
context = {
    "sentence": "Paka mdogo anacheza",
    "semantic_function": "udogoshaji"
}
result = engine.analyze_word("paka", context)
```

### Batch Processing
```python
sentences = [
    "Mwalimu anasomesha watoto.",
    "Joka kubwa limemeza chura.",
    "Kipaka kidogo kinlala."
]

results = []
for sentence in sentences:
    result = engine.analyze_sentence_enhanced(sentence)
    results.append(result)

# Format comparison
from kiswahili_engine.utils.formatters import ResultFormatter
comparison = ResultFormatter.format_comparison(results)
print(comparison)
```

### JSON Export
```python
from kiswahili_engine.utils.formatters import ResultFormatter

result = engine.analyze_sentence_enhanced("Complex sentence here.")
json_output = ResultFormatter.format_for_json(result)

# Save to file
with open('analysis.json', 'w', encoding='utf-8') as f:
    f.write(json_output)
```

## Ngeli System Reference

### Standard Ngeli Classes (1-15)
| Ngeli | Singular | Plural | Examples | Semantic Domain |
|-------|----------|--------|----------|-----------------|
| 1/2   | mu-, m-, mw- | wa- | mtu, mwalimu | Humans, professions |
| 3/4   | mu-, m-, mw- | mi- | mti, mto | Plants, tools |
| 5/6   | j-, Ø-, i- | ma- | jicho, goti | Body parts, fruits |
| 7/8   | ki-, ky- | vi-, vy- | kisu, kiti | Tools, languages |
| 9/10  | n-, Ø- | n-, Ø- | nyumba, ndizi | Animals, objects |
| 11/10a| u- | n- | ulimi, uso | Abstract concepts |
| 14/6a | u- | ma- | upendo, ugonjwa | Abstract concepts |
| 15    | ku- | ku- | kuja, kula | Infinitives |

### Locative Ngeli Classes (16-18)
| Ngeli | Prefix | Meaning | Examples |
|-------|--------|---------|----------|
| 16    | pa- | Definite location | pahali, pangoni |
| 17    | ku-, kwa- | Indefinite/distant | kule, kwahali |
| 18    | mu- | Interior location | mahali (inside) |

### Semantic Functions

#### Ukuzaji (Augmentative)
- **Target ngeli**: 5/6, 5/4
- **Purpose**: Express large size, fear, respect
- **Example**: *joka* (large snake) instead of standard *nyoka*

#### Udogoshaji (Diminutive)
- **Target ngeli**: 7/8
- **Purpose**: Express smallness, endearment
- **Example**: *kipaka* (small cat) instead of *paka*

#### Dharau (Contempt)
- **Target ngeli**: 7/8
- **Purpose**: Express contempt, bad behavior
- **Example**: *kizee* (contemptuous old person)

#### Sifa Nzuri (Positive qualities)
- **Target ngeli**: 7/8
- **Purpose**: Express positive characteristics
- **Example**: *kitoto* (cute child)

## Phonological Rules

### Nasal Mutation
- `mu-` + consonant → `n-` + consonant (except before p, b, f, v)
- Examples: `mu + tu` → `ntu`, `mu + papa` → `mpapa`

### Vowel Coalescence
- `mu-` + vowel → `mw-` + vowel
- `ki-` + vowel → `ky-` + vowel
- Examples: `mu + embe` → `mwembe`, `ki + atu` → `kyatu`

## API Reference

### Core Classes

#### `EnhancedKiswahiliGrammarEngine`
Main interface for sentence analysis.

**Methods:**
- `analyze_sentence_enhanced(sentence: str) -> Dict`
- `analyze_word(word: str, context: Dict = None) -> Dict`
- `check_agreement(subject: str, verb: str, adjective: str = None) -> Dict`

#### `EnhancedNgeliSystem`
Core ngeli classification and analysis.

**Methods:**
- `identify_ngeli_enhanced(word: str, context: Dict = None) -> NgeliInfo`
- `detect_ngeli_migration(word: str, context: Dict = None) -> Dict`
- `check_enhanced_agreement(...) -> Dict`

#### `PhonologicalRules`
Phonological process handling.

**Methods:**
- `apply_nasal_mutation(prefix: str, root: str) -> str`
- `handle_vowel_coalescence(prefix: str, root: str) -> Tuple[str, str]`

### Data Types

#### `NgeliInfo`
Complete ngeli classification result.
- `ngeli_class: str` - The ngeli (e.g., "7/8")
- `number: str` - "singular" or "plural"
- `semantic_function: SemanticFunction` - Detected semantic function
- `confidence: float` - Classification confidence (0-1)
- `morphological_analysis: Dict` - Detailed breakdown

#### `SemanticFunction`
Enumeration of semantic functions:
- `NEUTRAL`, `UKUZAJI`, `UDOGOSHAJI`, `DHARAU`, `SIFA_NZURI`, `MZAHA`, `CHUKI`

## Testing

Run the test suite:
```bash
cd kiswahili_engine
python -m pytest tests/
```

Or run specific test modules:
```bash
python -m pytest tests/test_ngeli_system.py
python -m pytest tests/test_grammar_engine.py
```

## Examples

See the `examples/` directory for comprehensive usage examples:
- `basic_usage.py` - Basic features demonstration
- `advanced_features.py` - Advanced capabilities and integration

Run examples:
```bash
cd kiswahili_engine/examples
python basic_usage.py
python advanced_features.py
```

## Research Background

This implementation is based on:

**"Ngeli za Nomino za Ki-Micheweni"** by Hamad Khamis Juma (2015)
- Published in *Mulika Na. 35*
- Documents the complete 18-ngeli system of Ki-Micheweni dialect
- Identifies semantic functions unique to this dialect
- Analyzes morphophonological processes and agreement patterns

Key differences from standard Kiswahili:
- 18 ngeli classes vs. typical 16
- Productive semantic function system
- Dialectal-specific phonological rules
- Unique locative system (ngeli 16/17/18)

## Contributing

Contributions are welcome! Areas for enhancement:
- Additional dialect support
- Machine learning integration
- Performance optimizations
- Extended semantic domain coverage
- Integration with other NLP tools

## License

[Specify your license here]

## Citation

If you use this engine in research, please cite:

```
Ki-Micheweni Grammar Engine (2024)
Based on research by Hamad Khamis Juma (2015)
"Ngeli za Nomino za Ki-Micheweni", Mulika Na. 35
```

## Acknowledgments

- **Hamad Khamis Juma** for the foundational research on Ki-Micheweni ngeli system
- The University of Dar es Salaam for linguistic research
- The Ki-Micheweni speaking community of Pemba Island