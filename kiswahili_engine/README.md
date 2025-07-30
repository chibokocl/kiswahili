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