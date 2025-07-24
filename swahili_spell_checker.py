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
    """Test the spell checker with some common Swahili words and misspellings."""
    test_cases = [
        # Correct words
        ("jambo", "jambo"),
        ("asante", "asante"),
        ("karibu", "karibu"),
        ("habari", "habari"),
        
        # Common misspellings
        ("jambo", "jambo"),  # correct
        ("jambu", "jambo"),  # missing 'o'
        ("jamboo", "jambo"),  # extra 'o'
        ("jamb", "jambo"),    # missing 'o'
        
        # More complex cases
        ("asante", "asante"),  # correct
        ("asanti", "asante"),  # 'i' instead of 'e'
        ("asante", "asante"),  # correct
        
        # Numbers and common words
        ("moja", "moja"),      # correct
        ("mbili", "mbili"),    # correct
        ("tatu", "tatu"),      # correct
        
        # Common Swahili words
        ("mungu", "mungu"),    # correct
        ("bwana", "bwana"),    # correct
        ("mama", "mama"),      # correct
        ("baba", "baba"),      # correct
    ]
    
    print("Testing Swahili Spell Checker")
    print("=" * 40)
    
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