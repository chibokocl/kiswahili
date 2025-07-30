"""
Type definitions for the Ki-Micheweni grammar engine
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class SemanticFunction(Enum):
    """
    Semantic functions that can trigger ngeli changes in Ki-Micheweni.
    
    Based on research by Hamad Khamis Juma (2015) on ngeli za nomino za Ki-Micheweni.
    """
    NEUTRAL = "neutral"
    UKUZAJI = "ukuzaji"          # Augmentative - size, fear, respect
    UDOGOSHAJI = "udogoshaji"    # Diminutive - small, endearing
    DHARAU = "dharau"            # Contempt, bad behavior
    SIFA_NZURI = "sifa_nzuri"    # Good qualities, beauty
    MZAHA = "mzaha"              # Humor, joking
    CHUKI = "chuki"              # Hatred, disgust


@dataclass
class NgeliInfo:
    """
    Complete information about a ngeli classification.
    
    Attributes:
        ngeli_class: The ngeli class (e.g., "1/2", "7/8")
        number: Grammatical number ("singular" or "plural")
        semantic_function: The semantic function applied
        confidence: Confidence score (0.0-1.0)
        morphological_analysis: Detailed morphological breakdown
    """
    ngeli_class: str
    number: str
    semantic_function: SemanticFunction
    confidence: float
    morphological_analysis: Dict[str, Any]
    
    def __str__(self) -> str:
        return f"Ngeli {self.ngeli_class} ({self.number}) - {self.semantic_function.value}"
    
    def is_migrated(self) -> bool:
        """Check if this represents a migrated ngeli assignment"""
        return self.semantic_function != SemanticFunction.NEUTRAL


@dataclass
class VerbAnalysis:
    """
    Detailed verb morphological analysis.
    
    Attributes:
        word: Original verb form
        structure: Morphological components
        ngeli: Subject ngeli class
        number: Subject number
        tense: Tense/aspect marker
        explanation: Human-readable explanation
    """
    word: str
    structure: Dict[str, Any]
    ngeli: str = None
    number: str = None
    tense: str = None
    explanation: list = None
    
    def __post_init__(self):
        if self.explanation is None:
            self.explanation = []


@dataclass
class AgreementAnalysis:
    """
    Results of agreement checking between sentence elements.
    
    Attributes:
        subject_verb_agreement: Whether subject and verb agree
        noun_adjective_agreement: Whether nouns and adjectives agree
        overall_coherence: Overall sentence coherence
        issues: List of detected issues
        detailed_analysis: Detailed explanations
        ngeli_consistency: Ngeli usage patterns
    """
    subject_verb_agreement: bool = True
    noun_adjective_agreement: bool = True
    overall_coherence: bool = True
    issues: list = None
    detailed_analysis: list = None
    ngeli_consistency: Dict[str, list] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.detailed_analysis is None:
            self.detailed_analysis = []
        if self.ngeli_consistency is None:
            self.ngeli_consistency = {}


class SentenceType(Enum):
    """Sentence types based on OFP 008 classification"""
    SAHILI = "Sahili (Statement)"
    ULIZI = "Ulizi (Question)"
    AMRI = "Amri (Command)"
    CHANGAMANI = "Changamani (Conditional)"
    AMBATANO = "Ambatano (Conjunctive)"


class SyntacticRole(Enum):
    """Syntactic roles for sentence elements"""
    KIIMA = "kiima"              # Subject
    KIARIFU = "kiarifu"          # Predicate
    KITENZI = "kitenzi"          # Verb
    NOMINO = "nomino"            # Noun
    KIVUMISHI = "kivumishi"      # Adjective
    KIELEZI = "kielezi"          # Adverb