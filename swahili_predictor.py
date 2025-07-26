import re
import json
from collections import Counter
from difflib import get_close_matches
from swahili_context_analyzer import SwahiliContextAnalyzer

def load_swahili_corpus():
    """Load the Swahili corpus from JSON file."""
    try:
        with open('swahili_corpus/swahili_corpus.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: swahili_corpus.json not found. Using empty corpus.")
        return {}

# Load the word frequency data
WORDS = Counter(load_swahili_corpus())

def predict_word(partial_word, num_suggestions=3):
    """
    Predict word completions based on partial input.
    Returns top N suggestions based on frequency and similarity.
    """
    partial_word = partial_word.lower().strip()
    
    if not partial_word:
        # If no input, return most common words
        return [word for word, _ in WORDS.most_common(num_suggestions)]
    
    # Find words that start with the partial word
    prefix_matches = []
    for word, frequency in WORDS.items():
        if word.startswith(partial_word):
            prefix_matches.append((word, frequency))
    
    # Sort by frequency (highest first)
    prefix_matches.sort(key=lambda x: x[1], reverse=True)
    
    # If we have enough prefix matches, return top N
    if len(prefix_matches) >= num_suggestions:
        return [word for word, _ in prefix_matches[:num_suggestions]]
    
    # If not enough prefix matches, add similar words
    suggestions = [word for word, _ in prefix_matches]
    
    # Find similar words using difflib
    all_words = list(WORDS.keys())
    similar_words = get_close_matches(partial_word, all_words, n=num_suggestions*2, cutoff=0.6)
    
    # Add similar words that aren't already in suggestions
    for word in similar_words:
        if word not in suggestions and len(suggestions) < num_suggestions:
            suggestions.append(word)
    
    return suggestions[:num_suggestions]

def predict_with_context(partial_word, context_words=None, num_suggestions=3):
    """
    Predict word completions with context awareness using the context analyzer.
    """
    # Use the context analyzer for more intelligent predictions
    analyzer = SwahiliContextAnalyzer()
    suggestions = analyzer.get_contextual_suggestions(partial_word, context_words, num_suggestions)
    
    # Return just the words (without confidence scores for backward compatibility)
    return [word for word, confidence, reason in suggestions]

def interactive_predictor():
    """Interactive word predictor for testing."""
    print("Swahili Word Predictor/Autocomplete")
    print("Type 'quit' to exit")
    print("Type 'stats' to see corpus statistics")
    print("-" * 40)
    
    while True:
        user_input = input("Enter partial word: ").strip()
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'stats':
            print(f"Corpus size: {len(WORDS)} words")
            print(f"Total frequency: {sum(WORDS.values())}")
            print("Most common words:")
            for word, count in WORDS.most_common(10):
                print(f"  {word}: {count}")
            continue
        
        if user_input:
            suggestions = predict_word(user_input)
            print(f"Suggestions for '{user_input}':")
            for i, suggestion in enumerate(suggestions, 1):
                frequency = WORDS[suggestion]
                print(f"  {i}. {suggestion} (frequency: {frequency})")
        else:
            print("Please enter a partial word.")

def test_predictor():
    """Test the predictor with dynamically generated inputs based on corpus data."""
    print("Testing Swahili Word Predictor")
    print("=" * 40)
    
    # Generate test cases dynamically from corpus data
    # Find common prefixes and create realistic test inputs
    common_words = [word for word, freq in WORDS.most_common(200) if freq > 50]
    
    # Extract common prefixes (2-3 characters) from frequent words
    prefixes = set()
    for word in common_words:
        if len(word) >= 3:
            prefixes.add(word[:2])  # 2-letter prefixes
        if len(word) >= 4:
            prefixes.add(word[:3])  # 3-letter prefixes
    
    # Convert to list and sort by frequency of words starting with that prefix
    prefix_frequency = {}
    for prefix in prefixes:
        count = sum(freq for word, freq in WORDS.items() if word.startswith(prefix))
        prefix_frequency[prefix] = count
    
    # Get top prefixes by frequency
    top_prefixes = sorted(prefix_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    test_cases = [prefix for prefix, freq in top_prefixes]
    
    for partial in test_cases:
        suggestions = predict_word(partial)
        print(f"\n'{partial}' -> {suggestions}")
        for suggestion in suggestions:
            print(f"  - {suggestion} (freq: {WORDS[suggestion]})")

def predict_sentence_completion(sentence, num_suggestions=3):
    """
    Predict the next word in a sentence.
    """
    words_in_sentence = re.findall(r'\w+', sentence.lower())
    
    if not words_in_sentence:
        return [word for word, _ in WORDS.most_common(num_suggestions)]
    
    # Get the last word as partial input
    last_word = words_in_sentence[-1]
    
    # Use context from previous words
    context_words = words_in_sentence[:-1] if len(words_in_sentence) > 1 else []
    
    return predict_with_context(last_word, context_words, num_suggestions)

def demo_sentence_completion():
    """Demonstrate sentence completion using dynamic data from corpus."""
    print("Sentence Completion Demo")
    print("=" * 30)
    
    # Generate test cases dynamically from corpus data
    # Find common word patterns and create realistic test sentences
    common_words = [word for word, freq in WORDS.most_common(50) if freq > 100]
    
    # Create test sentences based on common word combinations
    test_sentences = []
    
    # Single word completions (most common words)
    for word in common_words[:5]:
        test_sentences.append(word)
    
    # Two-word combinations (common patterns)
    common_two_word_patterns = []
    for word1 in common_words[:10]:
        for word2 in common_words[:10]:
            if word1 != word2:
                # Check if this combination appears frequently in context
                combined = f"{word1} {word2}"
                if combined in WORDS or any(f"{word1} {word2}" in context for context in WORDS.keys()):
                    common_two_word_patterns.append(combined)
                    if len(common_two_word_patterns) >= 5:
                        break
        if len(common_two_word_patterns) >= 5:
            break
    
    test_sentences.extend(common_two_word_patterns)
    
    # Generate partial sentences for completion testing
    for pattern in common_two_word_patterns[:3]:
        words = pattern.split()
        if len(words) >= 2:
            # Create partial sentence by removing last word
            partial = " ".join(words[:-1])
            test_sentences.append(partial)
    
    # If we don't have enough dynamic test cases, create some based on word frequency
    if len(test_sentences) < 10:
        # Find words that commonly appear at sentence beginnings
        sentence_starters = [word for word, freq in WORDS.most_common(100) 
                           if freq > 50 and len(word) > 2]
        for starter in sentence_starters[:10-len(test_sentences)]:
            test_sentences.append(starter)
    
    # Limit to reasonable number of test cases
    test_sentences = test_sentences[:10]
    
    for sentence in test_sentences:
        suggestions = predict_sentence_completion(sentence)
        print(f"\n'{sentence}' -> {suggestions}")

if __name__ == "__main__":
    print(f"Loaded {len(WORDS)} words from Swahili corpus")
    print(f"Total word frequency: {sum(WORDS.values())}")
    
    # Show some statistics
    print("\nMost common Swahili words:")
    for word, count in WORDS.most_common(10):
        print(f"  {word}: {count}")
    
    # Run tests
    print("\n" + "="*50)
    test_predictor()
    
    # Demo sentence completion
    print("\n" + "="*50)
    demo_sentence_completion()
    
    # Interactive mode
    print("\n" + "="*50)
    interactive_predictor() 