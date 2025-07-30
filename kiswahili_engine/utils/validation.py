"""
Input validation utilities for the Ki-Micheweni grammar engine.
"""

import re
from typing import Dict, List, Optional, Tuple


class InputValidator:
    """Validates input for the grammar engine."""
    
    # Valid Swahili characters (basic Latin + common diacritics)
    VALID_CHARS = re.compile(r'^[a-zA-Z\s\'\-\.!?]+$')
    
    # Maximum reasonable lengths
    MAX_WORD_LENGTH = 50
    MAX_SENTENCE_LENGTH = 500
    MAX_TEXT_LENGTH = 5000
    
    @classmethod
    def validate_word(cls, word: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a single word input.
        
        Returns:
            (is_valid, error_message)
        """
        if not word:
            return False, "Empty word"
        
        if not isinstance(word, str):
            return False, "Word must be a string"
        
        if len(word) > cls.MAX_WORD_LENGTH:
            return False, f"Word too long (max {cls.MAX_WORD_LENGTH} characters)"
        
        if not cls.VALID_CHARS.match(word):
            return False, "Word contains invalid characters"
        
        # Check for reasonable word structure
        if not re.search(r'[aeiou]', word.lower()):
            return False, "Word appears to lack vowels"
        
        return True, None
    
    @classmethod
    def validate_sentence(cls, sentence: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a sentence input.
        
        Returns:
            (is_valid, error_message)
        """
        if not sentence:
            return False, "Empty sentence"
        
        if not isinstance(sentence, str):
            return False, "Sentence must be a string"
        
        if len(sentence) > cls.MAX_SENTENCE_LENGTH:
            return False, f"Sentence too long (max {cls.MAX_SENTENCE_LENGTH} characters)"
        
        if not cls.VALID_CHARS.match(sentence):
            return False, "Sentence contains invalid characters"
        
        # Check for at least one word
        words = re.findall(r'\b\w+\b', sentence)
        if not words:
            return False, "Sentence contains no valid words"
        
        return True, None
    
    @classmethod
    def validate_text(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate longer text input.
        
        Returns:
            (is_valid, error_message)
        """
        if not text:
            return False, "Empty text"
        
        if not isinstance(text, str):
            return False, "Text must be a string"
        
        if len(text) > cls.MAX_TEXT_LENGTH:
            return False, f"Text too long (max {cls.MAX_TEXT_LENGTH} characters)"
        
        return True, None
    
    @classmethod
    def validate_context(cls, context: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate context dictionary.
        
        Returns:
            (is_valid, error_message)
        """
        if not isinstance(context, dict):
            return False, "Context must be a dictionary"
        
        # Check for valid keys
        valid_keys = {
            'sentence', 'position', 'neighboring_words', 
            'semantic_function', 'sentence_structure'
        }
        
        for key in context:
            if key not in valid_keys:
                return False, f"Invalid context key: {key}"
        
        return True, None
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitize input text for safe processing.
        
        Args:
            text: Raw input text
            
        Returns:
            Sanitized text
        """
        if not isinstance(text, str):
            return ""
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Limit length
        if len(text) > InputValidator.MAX_TEXT_LENGTH:
            text = text[:InputValidator.MAX_TEXT_LENGTH]
        
        return text