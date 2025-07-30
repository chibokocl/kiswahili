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

__version__ = "2.0.0"
__author__ = "Ki-Micheweni Grammar Engine Team"

# Main exports
__all__ = [
    "EnhancedNgeliSystem",
    "EnhancedKiswahiliGrammarEngine", 
    "SemanticFunction",
    "NgeliInfo",
    "PhonologicalRules"
]

# Convenience imports
def create_engine():
    """Create a new instance of the enhanced grammar engine"""
    return EnhancedKiswahiliGrammarEngine()

def analyze_sentence(sentence: str):
    """Quick sentence analysis using default engine"""
    engine = create_engine()
    return engine.analyze_sentence_enhanced(sentence)