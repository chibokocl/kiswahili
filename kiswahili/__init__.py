"""
Kiswahili NLP Toolkit

A comprehensive Swahili language processing toolkit for text analysis,
spell checking, word prediction, and grammatical analysis.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .context_analyzer import SwahiliContextAnalyzer
from .spell_checker import SwahiliSpellChecker
from .predictor import SwahiliPredictor
from .grammar_engine import SwahiliGrammarEngine

__all__ = [
    "SwahiliContextAnalyzer",
    "SwahiliSpellChecker", 
    "SwahiliPredictor",
    "SwahiliGrammarEngine",
]

# Convenience function for quick analysis
def analyze_text(text: str, analysis_type: str = "grammar"):
    """
    Quick analysis function for common use cases.
    
    Args:
        text: Text to analyze
        analysis_type: Type of analysis ("grammar", "spell", "context")
    
    Returns:
        Analysis results
    """
    analyzer = SwahiliContextAnalyzer()
    
    if analysis_type == "grammar":
        return analyzer.analyze_grammatical_correctness(text)
    elif analysis_type == "context":
        return analyzer.analyze_sentence_context(text)
    elif analysis_type == "spell":
        spell_checker = SwahiliSpellChecker()
        return spell_checker.correction(text)
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}") 