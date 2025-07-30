"""
Text processing utilities for the Ki-Micheweni grammar engine.
"""

import re
from typing import List, Dict, Any


class TextProcessor:
    """Handles text cleaning and preprocessing for analysis."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize input text."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Handle common punctuation
        text = re.sub(r'([.!?])\s*$', r'\1', text)
        
        return text
    
    @staticmethod
    def tokenize_words(text: str) -> List[str]:
        """Tokenize text into words."""
        # Simple word tokenization
        words = re.findall(r'\b\w+\b', text)
        return [w for w in words if w]
    
    @staticmethod
    def extract_morphemes(word: str, prefix: str) -> Dict[str, str]:
        """Extract morphemes from a word given a prefix."""
        if not word.startswith(prefix):
            return {"prefix": "", "root": word}
        
        root = word[len(prefix):]
        return {"prefix": prefix, "root": root}


class SentenceTokenizer:
    """Handles sentence-level tokenization and analysis."""
    
    def __init__(self):
        # Sentence boundary patterns
        self.sentence_endings = re.compile(r'[.!?]+')
        self.abbreviations = {'Dr', 'Prof', 'Mhe', 'Dk'}  # Common Swahili abbreviations
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = []
        
        # Simple sentence splitting
        potential_sentences = self.sentence_endings.split(text)
        
        for sentence in potential_sentences:
            cleaned = sentence.strip()
            if cleaned:
                sentences.append(cleaned)
        
        return sentences
    
    def is_sentence_complete(self, sentence: str) -> bool:
        """Check if a sentence appears to be complete."""
        sentence = sentence.strip()
        
        # Basic completeness checks
        if not sentence:
            return False
        
        # Has ending punctuation
        if sentence[-1] in '.!?':
            return True
        
        # Contains verb-like patterns
        verb_patterns = ['-na-', '-me-', '-ta-', '-li-']
        if any(pattern in sentence.lower() for pattern in verb_patterns):
            return True
        
        return False