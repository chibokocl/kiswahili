"""
Ki-Micheweni Grammar Engine Package

A comprehensive morphological and syntactic analysis engine for the Ki-Micheweni 
dialect of Kiswahili, implementing the full 18-ngeli system with semantic functions.

Author: Enhanced based on research by Hamad Khamis Juma (2015)
"""

from .core.ngeli_system import EnhancedNgeliSystem
from .core.grammar_engine import EnhancedKiswahiliGrammarEngine
from .core.types import SemanticFunction, NgeliInfo
from .core.phonology import PhonologicalRules
from .core.verb_morphology import VerbParser, VerbParse
from .core.noun_lexicon import NounLexicon, NounEntry
from .checker import Checker, Issue, Suggestion

__version__ = "2.0.0"
__author__ = "Ki-Micheweni Grammar Engine Team"

# Main exports
__all__ = [
    "EnhancedNgeliSystem",
    "EnhancedKiswahiliGrammarEngine", 
    "SemanticFunction",
    "NgeliInfo",
    "PhonologicalRules",
    "VerbParser",
    "VerbParse",
    "NounLexicon",
    "NounEntry",
    "Checker",
    "Issue",
    "Suggestion",
]

# Convenience imports
def create_engine(config=None):
    """Create a new instance of the enhanced grammar engine.

    ``config={"verb_lexicon_path": "swahili_corpus/swahili_words.txt"}`` builds a
    verb-root lexicon from a word list, which sharpens root/extension analysis.
    """
    return EnhancedKiswahiliGrammarEngine(config)

def analyze_sentence(sentence: str):
    """Quick sentence analysis using default engine"""
    engine = create_engine()
    return engine.analyze_sentence_enhanced(sentence)