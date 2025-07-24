import re
import json
from collections import Counter
from difflib import get_close_matches

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
    Predict word completions with context awareness.
    Context words can help improve predictions.
    """
    partial_word = partial_word.lower().strip()
    
    if not partial_word:
        return [word for word, _ in WORDS.most_common(num_suggestions)]
    
    # Basic prefix matching
    prefix_matches = []
    for word, frequency in WORDS.items():
        if word.startswith(partial_word):
            # Boost frequency if word appears in context
            boost = 1.0
            if context_words:
                for context_word in context_words:
                    if context_word.lower() in word or word in context_word.lower():
                        boost *= 1.5
            prefix_matches.append((word, frequency * boost))
    
    # Sort by boosted frequency
    prefix_matches.sort(key=lambda x: x[1], reverse=True)
    
    suggestions = [word for word, _ in prefix_matches[:num_suggestions]]
    
    # Fill remaining slots with similar words if needed
    if len(suggestions) < num_suggestions:
        all_words = list(WORDS.keys())
        similar_words = get_close_matches(partial_word, all_words, n=num_suggestions*2, cutoff=0.5)
        
        for word in similar_words:
            if word not in suggestions and len(suggestions) < num_suggestions:
                suggestions.append(word)
    
    return suggestions[:num_suggestions]

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
    """Test the predictor with various inputs."""
    test_cases = [
        "ja",      # Should suggest jambo, jana, etc.
        "as",      # Should suggest asante, asubuhi, etc.
        "ka",      # Should suggest karibu, kama, etc.
        "ha",      # Should suggest habari, hakuna, etc.
        "mu",      # Should suggest mungu, mtu, etc.
        "ba",      # Should suggest baba, bado, etc.
        "ma",      # Should suggest mama, mambo, etc.
        "wa",      # Should suggest watu, wana, etc.
        "ni",      # Should suggest nini, nina, etc.
        "si",      # Should suggest siku, sisi, etc.
    ]
    
    print("Testing Swahili Word Predictor")
    print("=" * 40)
    
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
    """Demonstrate sentence completion."""
    test_sentences = [
        "jambo",
        "asante sana",
        "habari za",
        "karibu",
        "mungu",
        "bwana asifiwe",
        "mama na",
        "baba yangu",
        "siku ya",
        "mtu wa",
    ]
    
    print("Sentence Completion Demo")
    print("=" * 30)
    
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