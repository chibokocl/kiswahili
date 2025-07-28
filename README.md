# Kiswahili NLP Toolkit

A comprehensive Swahili language processing toolkit that provides intelligent text analysis, spell checking, word prediction, and grammatical analysis based on actual corpus data.

## Features

### ✅ Working Features (v0.1.0)

1. **Spell Checking** - Intelligent spell correction with context awareness
2. **Word Prediction** - Autocomplete suggestions based on partial input
3. **Context Analysis** - Analyze word relationships and usage patterns
4. **Sentence Completion** - Context-aware sentence completion suggestions
5. **Grammatical Analysis** - Check grammatical correctness of Swahili sentences

### 🔧 Core Components

- **SwahiliContextAnalyzer** - Main analysis engine for context and grammar
- **SwahiliSpellChecker** - Spell checking and correction
- **SwahiliPredictor** - Word prediction and autocomplete
- **SwahiliGrammarEngine** - Grammar analysis and validation

## Installation

### From Source

```bash
git clone https://github.com/yourusername/kiswahili.git
cd kiswahili
pip install -e .
```

### Dependencies

The package requires:
- Python 3.8+
- PyPDF2>=3.0.0
- pdfplumber>=0.9.0
- nltk>=3.8
- regex>=2023.0.0

## Quick Start

### Interactive Demo

Run the interactive demo to explore all features:

```bash
python swahili_terminal_demo.py
```

Or after installation:

```bash
kiswahili-demo
```

### Programmatic Usage

```python
from kiswahili import SwahiliContextAnalyzer, SwahiliSpellChecker, SwahiliPredictor

# Initialize analyzers
analyzer = SwahiliContextAnalyzer()
spell_checker = SwahiliSpellChecker()
predictor = SwahiliPredictor()

# Spell checking
corrected = spell_checker.correction("karieni")  # Returns "kazini"

# Word prediction
suggestions = predictor.predict_word("na")  # Returns suggestions starting with "na"

# Grammatical analysis
analysis = analyzer.analyze_grammatical_correctness("Juma na Assha wanachekeleana na pembeni")
print(f"Grammar score: {analysis['grammar_score']}")
print(f"Issues: {analysis['issues']}")

# Context analysis
context = analyzer.analyze_word_context("juma")
print(f"Frequency: {context['frequency']}")
print(f"Category: {context['category']}")
```

## Example: Grammatical Analysis

```python
from kiswahili import SwahiliContextAnalyzer

analyzer = SwahiliContextAnalyzer()

# Analyze a sentence for grammatical correctness
sentence = "Juma na Assha wanachekeleana na pembeni"
result = analyzer.analyze_grammatical_correctness(sentence)

print(f"Sentence: {sentence}")
print(f"Correct: {result['is_correct']}")
print(f"Grammar Score: {result['grammar_score']:.2f}")

if result['issues']:
    print("Issues found:")
    for issue in result['issues']:
        print(f"  • {issue}")

if result['suggestions']:
    print(f"Suggestions: {', '.join(result['suggestions'])}")
```

## Corpus Data

The toolkit uses a comprehensive Swahili corpus including:
- Biblical texts
- Modern literature
- Common vocabulary
- Grammar patterns

The corpus is automatically loaded and provides the foundation for all analysis features.

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
flake8 .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

### v0.2.0 (Planned)
- Enhanced grammar rules
- Better context understanding
- Performance optimizations
- More comprehensive corpus

### v0.3.0 (Future)
- Machine learning integration
- Advanced sentence parsing
- Translation assistance
- API endpoints

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{kiswahili_nlp_2024,
  title={Kiswahili NLP Toolkit},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/kiswahili}
}
```

## Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation
- Review the examples in the demo

---

**Note**: This is a v0.1.0 release. The toolkit is functional but may have limitations with complex grammatical structures. Feedback and contributions are welcome! 