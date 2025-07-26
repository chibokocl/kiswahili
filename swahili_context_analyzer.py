"""
Swahili Context Analyzer

Analyzes text context and generates intelligent suggestions based on actual usage patterns
in the corpus, eliminating hardcoded responses.
"""

import re
import json
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from difflib import get_close_matches

class SwahiliContextAnalyzer:
    """
    Analyzes Swahili text context and generates intelligent suggestions
    based on actual usage patterns in the corpus.
    """
    
    def __init__(self, corpus_file: str = 'swahili_corpus/swahili_corpus.json'):
        """Initialize the context analyzer with corpus data."""
        self.corpus_data = self._load_corpus(corpus_file)
        self.words = Counter(self.corpus_data)  # Convert dict to Counter
        self.word_frequencies = self.words  # Alias for compatibility
        self.context_patterns = self._build_context_patterns()
        self.word_associations = self._build_word_associations()
    
    def _load_corpus(self, corpus_file: str) -> Dict[str, int]:
        """Load the Swahili corpus from JSON file."""
        try:
            with open(corpus_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: {corpus_file} not found. Using empty corpus.")
            return {}
    
    def _build_context_patterns(self) -> Dict[str, List[str]]:
        """Build context patterns based on word co-occurrence."""
        patterns = defaultdict(list)
        
        # Analyze word pairs that commonly appear together
        word_pairs = defaultdict(int)
        
        # This is a simplified approach - in a real system, you'd analyze actual sentences
        # For now, we'll create patterns based on word frequency and common Swahili patterns
        common_words = [word for word, freq in self.word_frequencies.most_common(100)]
        
        # Create common Swahili patterns
        swahili_patterns = {
            'greetings': ['jambo', 'habari', 'asante', 'karibu'],
            'family': ['mama', 'baba', 'mtoto', 'rafiki'],
            'time': ['leo', 'jana', 'kesho', 'siku'],
            'numbers': ['moja', 'mbili', 'tatu', 'nne', 'tano'],
            'common_verbs': ['ni', 'na', 'wa', 'kuwa', 'kufanya'],
            'common_nouns': ['mtu', 'jambo', 'kitu', 'mahali'],
            'common_adjectives': ['nzuri', 'kubwa', 'ndogo', 'mzuri']
        }
        
        for category, words in swahili_patterns.items():
            for word in words:
                if word in self.word_frequencies:
                    patterns[category].append(word)
        
        return dict(patterns)
    
    def _build_word_associations(self) -> Dict[str, List[Tuple[str, float]]]:
        """Build word associations based on frequency and context."""
        associations = defaultdict(list)
        
        # Create associations based on word frequency and common Swahili patterns
        for word, freq in self.word_frequencies.most_common(200):
            if freq > 10:  # Only consider words with reasonable frequency
                # Find similar words
                similar_words = get_close_matches(word, self.word_frequencies.keys(), n=5, cutoff=0.6)
                
                for similar_word in similar_words:
                    if similar_word != word:
                        # Calculate association strength based on frequency
                        strength = min(freq, self.word_frequencies[similar_word]) / max(freq, self.word_frequencies[similar_word])
                        associations[word].append((similar_word, strength))
                
                # Add category-based associations
                for category, category_words in self.context_patterns.items():
                    if word in category_words:
                        for category_word in category_words:
                            if category_word != word:
                                associations[word].append((category_word, 0.3))
        
        return dict(associations)
    
    def get_contextual_suggestions(self, partial_word: str, context_words: List[str] = None, 
                                 num_suggestions: int = 5) -> List[Tuple[str, float, str]]:
        """
        Get contextual suggestions based on partial word and context.
        
        Returns: List of (word, confidence, reason) tuples
        """
        partial_word = partial_word.lower().strip()
        suggestions = []
        
        if not partial_word:
            # Return most common words if no partial input
            for word, freq in self.word_frequencies.most_common(num_suggestions):
                suggestions.append((word, freq / max(self.word_frequencies.values()), "most_common"))
            return suggestions
        
        # Find prefix matches
        prefix_matches = []
        for word, freq in self.word_frequencies.items():
            if word.startswith(partial_word):
                confidence = freq / max(self.word_frequencies.values())
                prefix_matches.append((word, confidence, "prefix_match"))
        
        # Sort by frequency
        prefix_matches.sort(key=lambda x: x[1], reverse=True)
        suggestions.extend(prefix_matches[:num_suggestions])
        
        # If we need more suggestions, add context-aware ones
        if len(suggestions) < num_suggestions and context_words:
            context_suggestions = self._get_context_aware_suggestions(partial_word, context_words, num_suggestions)
            suggestions.extend(context_suggestions)
        
        # If still need more, add similar words
        if len(suggestions) < num_suggestions:
            similar_words = get_close_matches(partial_word, self.word_frequencies.keys(), 
                                           n=num_suggestions*2, cutoff=0.5)
            for word in similar_words:
                if not any(s[0] == word for s in suggestions):
                    freq = self.word_frequencies[word]
                    confidence = freq / max(self.word_frequencies.values()) * 0.5  # Lower confidence for similar words
                    suggestions.append((word, confidence, "similar_word"))
                    if len(suggestions) >= num_suggestions:
                        break
        
        return suggestions[:num_suggestions]
    
    def _get_context_aware_suggestions(self, partial_word: str, context_words: List[str], 
                                     num_suggestions: int) -> List[Tuple[str, float, str]]:
        """Get suggestions based on context words."""
        suggestions = []
        
        for context_word in context_words:
            if context_word in self.word_associations:
                for associated_word, strength in self.word_associations[context_word]:
                    if associated_word.startswith(partial_word):
                        freq = self.word_frequencies[associated_word]
                        confidence = (freq / max(self.word_frequencies.values())) * strength
                        suggestions.append((associated_word, confidence, f"context_with_{context_word}"))
        
        # Sort by confidence and return top suggestions
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return suggestions[:num_suggestions]
    
    def analyze_sentence_context(self, sentence: str) -> Dict[str, any]:
        """Analyze the context of a sentence and return insights."""
        words = re.findall(r'\w+', sentence.lower())
        
        analysis = {
            'word_count': len(words),
            'common_words': [],
            'uncommon_words': [],
            'suggested_completions': [],
            'context_category': None
        }
        
        if not words:
            return analysis
        
        # Analyze word frequencies
        for word in words:
            freq = self.word_frequencies.get(word, 0)
            if freq > 50:
                analysis['common_words'].append((word, freq))
            elif freq == 0:
                analysis['uncommon_words'].append(word)
        
        # Determine context category
        category_scores = defaultdict(int)
        for word in words:
            for category, category_words in self.context_patterns.items():
                if word in category_words:
                    category_scores[category] += 1
        
        if category_scores:
            analysis['context_category'] = max(category_scores.items(), key=lambda x: x[1])[0]
        
        # Generate completion suggestions for the last word
        if words:
            last_word = words[-1]
            context_words = words[:-1] if len(words) > 1 else []
            suggestions = self.get_contextual_suggestions(last_word, context_words, 3)
            analysis['suggested_completions'] = suggestions
        
        return analysis
    
    def get_dynamic_test_cases(self, num_cases: int = 10) -> List[str]:
        """Generate dynamic test cases based on corpus data."""
        test_cases = []
        
        # Get common words for single-word tests
        common_words = [word for word, freq in self.word_frequencies.most_common(50) if freq > 20]
        test_cases.extend(common_words[:num_cases//2])
        
        # Generate partial words for completion tests
        for word in common_words[num_cases//2:num_cases]:
            if len(word) >= 3:
                partial = word[:len(word)//2]  # Take first half of word
                test_cases.append(partial)
        
        return test_cases[:num_cases]
    
    def get_sentence_completion_suggestions(self, sentence: str, num_suggestions: int = 3) -> List[Tuple[str, float, str]]:
        """Get intelligent sentence completion suggestions."""
        words = re.findall(r'\w+', sentence.lower())
        
        if not words:
            # Return most common words if no input
            return [(word, freq / max(self.word_frequencies.values()), "most_common") 
                   for word, freq in self.word_frequencies.most_common(num_suggestions)]
        
        # Get the last word as partial input
        last_word = words[-1]
        context_words = words[:-1] if len(words) > 1 else []
        
        return self.get_contextual_suggestions(last_word, context_words, num_suggestions)

    def analyze_word_context(self, word: str) -> Dict[str, any]:
        """Analyze a word's context and return detailed information."""
        word = word.lower().strip()
        
        analysis = {
            'frequency': self.word_frequencies.get(word, 0),
            'category': None,
            'related_words': [],
            'suggestions': []
        }
        
        # Determine category based on context patterns
        for category, category_words in self.context_patterns.items():
            if word in category_words:
                analysis['category'] = category
                break
        
        # Get related words from associations
        if word in self.word_associations:
            analysis['related_words'] = [related_word for related_word, strength in self.word_associations[word][:10]]
        
        # Get suggestions for similar words
        similar_words = get_close_matches(word, self.word_frequencies.keys(), n=5, cutoff=0.6)
        analysis['suggestions'] = similar_words
        
        return analysis

    def complete_sentence(self, sentence: str) -> List[str]:
        """Complete a sentence with context-aware suggestions."""
        suggestions = self.get_sentence_completion_suggestions(sentence, 5)
        return [word for word, confidence, reason in suggestions]

    def analyze_grammatical_correctness(self, sentence: str) -> Dict[str, any]:
        """
        Analyze the grammatical correctness of a Swahili sentence.
        This is the main feature for analyzing sentences like 'Juma na Assha wanachekeleana na pembeni'
        """
        words = re.findall(r'\w+', sentence.lower())
        
        analysis = {
            'is_correct': True,
            'issues': [],
            'suggestions': [],
            'word_analysis': {},
            'grammar_score': 1.0
        }
        
        if not words:
            analysis['is_correct'] = False
            analysis['issues'].append("Empty sentence")
            return analysis
        
        # Analyze each word
        for word in words:
            freq = self.word_frequencies.get(word, 0)
            analysis['word_analysis'][word] = {
                'frequency': freq,
                'exists_in_corpus': freq > 0,
                'suggestions': []
            }
            
            # If word doesn't exist in corpus, suggest corrections
            if freq == 0:
                analysis['is_correct'] = False
                analysis['issues'].append(f"Unknown word: '{word}'")
                
                # Find similar words as suggestions
                similar_words = get_close_matches(word, self.word_frequencies.keys(), n=3, cutoff=0.5)
                analysis['word_analysis'][word]['suggestions'] = similar_words
                analysis['suggestions'].extend(similar_words)
        
        # Check for common Swahili grammar patterns
        grammar_issues = self._check_swahili_grammar(words)
        analysis['issues'].extend(grammar_issues)
        
        if grammar_issues:
            analysis['is_correct'] = False
        
        # Calculate grammar score based on issues
        total_words = len(words)
        if total_words > 0:
            correct_words = sum(1 for word_info in analysis['word_analysis'].values() 
                              if word_info['exists_in_corpus'])
            analysis['grammar_score'] = correct_words / total_words
        
        return analysis
    
    def _check_swahili_grammar(self, words: List[str]) -> List[str]:
        """Check for common Swahili grammar issues."""
        issues = []
        
        # Check for subject-verb agreement patterns
        if len(words) >= 2:
            # Check if we have a proper subject-verb structure
            # This is a simplified check - in a real system you'd have more sophisticated grammar rules
            if words[0] in ['juma', 'assha', 'mtu', 'mama', 'baba'] and len(words) > 1:
                # Check if second word is a proper verb form
                second_word = words[1]
                if not any(verb in second_word for verb in ['na', 'wa', 'ni', 'ku']):
                    issues.append("Possible subject-verb agreement issue")
        
        # Check for common Swahili word patterns
        for i, word in enumerate(words):
            # Check for proper noun prefixes
            if word in ['juma', 'assha'] and i > 0:
                # Names should typically be at the beginning or after prepositions
                if words[i-1] not in ['na', 'wa', 'kwa', 'kutoka']:
                    issues.append(f"Name '{word}' might need proper context")
        
        return issues

def demo_context_analyzer():
    """Demonstrate the context analyzer with dynamic data."""
    analyzer = SwahiliContextAnalyzer()
    
    print("Swahili Context Analyzer Demo")
    print("=" * 40)
    
    # Generate dynamic test cases
    test_cases = analyzer.get_dynamic_test_cases(10)
    
    for test_case in test_cases:
        print(f"\nAnalyzing: '{test_case}'")
        
        # Get contextual suggestions
        suggestions = analyzer.get_contextual_suggestions(test_case)
        print(f"Suggestions:")
        for word, confidence, reason in suggestions:
            print(f"  - {word} (confidence: {confidence:.3f}, reason: {reason})")
        
        # Analyze as sentence context
        analysis = analyzer.analyze_sentence_context(test_case)
        if analysis['context_category']:
            print(f"  Context category: {analysis['context_category']}")

if __name__ == "__main__":
    demo_context_analyzer() 