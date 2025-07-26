import re
import json
from collections import Counter

def words(text): 
    """Extract words from text."""
    return re.findall(r'\w+', text.lower())

# Load Swahili corpus
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

def P(word, N=sum(WORDS.values())): 
    """Probability of `word`."""
    return WORDS[word] / N if N > 0 else 0

def correction(word): 
    """Most probable spelling correction for word."""
    return max(candidates(word), key=P)

def candidates(word): 
    """Generate possible spelling corrections for word."""
    return (known([word]) or known(edits1(word)) or known(edits2(word)) or [word])

def known(words): 
    """The subset of `words` that appear in the dictionary of WORDS."""
    return set(w for w in words if w in WORDS)

def edits1(word):
    """All edits that are one edit away from `word`."""
    letters = 'abcdefghijklmnopqrstuvwxyz'
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [L + R[1:] for L, R in splits if R]
    transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
    replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
    inserts = [L + c + R for L, R in splits for c in letters]
    return set(deletes + transposes + replaces + inserts)

def edits2(word): 
    """All edits that are two edits away from `word`."""
    return (e2 for e1 in edits1(word) for e2 in edits1(e1))

def spell_check_text(text):
    """Check spelling for a whole text and return corrections."""
    words_list = words(text)
    corrections = {}
    
    for word in words_list:
        if word not in WORDS:
            corrected = correction(word)
            if corrected != word:
                corrections[word] = corrected
    
    return corrections

def interactive_spell_checker():
    """Interactive spell checker for testing."""
    print("Swahili Spell Checker")
    print("Type 'quit' to exit")
    print("-" * 30)
    
    while True:
        word = input("Enter a word to check: ").strip().lower()
        if word == 'quit':
            break
        
        if word in WORDS:
            print(f"✓ '{word}' is correct (frequency: {WORDS[word]})")
        else:
            corrected = correction(word)
            if corrected != word:
                print(f"✗ '{word}' -> '{corrected}' (frequency: {WORDS[corrected]})")
            else:
                print(f"? '{word}' not found in corpus, no suggestion available")

def test_spell_checker():
    """Test the spell checker with dynamically generated test cases from corpus data."""
    print("Testing Swahili Spell Checker")
    print("=" * 40)
    
    # Generate test cases dynamically from corpus data
    test_cases = []
    
    # Get common words from corpus
    common_words = [word for word, freq in WORDS.most_common(100) if freq > 10]
    
    # Test correct words
    for word in common_words[:20]:
        test_cases.append((word, word))  # Correct word should remain correct
    
    # Generate misspellings for testing
    for word in common_words[:10]:
        if len(word) >= 3:
            # Create common misspellings
            misspellings = []
            
            # Remove last character
            if len(word) > 2:
                misspellings.append((word[:-1], word))
            
            # Add extra character at end
            misspellings.append((word + word[-1], word))
            
            # Replace last character with similar one
            if word[-1] in 'aeiou':
                for vowel in 'aeiou':
                    if vowel != word[-1]:
                        misspellings.append((word[:-1] + vowel, word))
                        break
            
            # Transpose last two characters
            if len(word) >= 3:
                misspellings.append((word[:-2] + word[-1] + word[-2], word))
            
            test_cases.extend(misspellings[:3])  # Limit to 3 misspellings per word
    
    # Limit total test cases to reasonable number
    test_cases = test_cases[:50]
    
    correct = 0
    total = len(test_cases)
    
    for original, expected in test_cases:
        corrected = correction(original)
        status = "✓" if corrected == expected else "✗"
        print(f"{status} '{original}' -> '{corrected}' (expected: '{expected}')")
        if corrected == expected:
            correct += 1
    
    accuracy = (correct / total) * 100
    print(f"\nAccuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    return accuracy

if __name__ == "__main__":
    print(f"Loaded {len(WORDS)} words from Swahili corpus")
    print(f"Total word frequency: {sum(WORDS.values())}")
    
    # Show some statistics
    print("\nMost common Swahili words:")
    for word, count in WORDS.most_common(10):
        print(f"  {word}: {count}")
    
    # Run tests
    print("\n" + "="*50)
    test_spell_checker()
    
    # Interactive mode
    print("\n" + "="*50)
    interactive_spell_checker() 