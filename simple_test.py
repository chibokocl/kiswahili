#!/usr/bin/env python3
"""
Simple test for the Swahili Corpus Builder - Text file only
"""

import time
from swahili_spell.corpus import CorpusBuilder

def test_text_file_only():
    """Test the corpus builder with just the text file first."""
    
    print("=== Simple Corpus Builder Test (Text File Only) ===\n")
    overall_start = time.time()
    
    # Initialize the corpus builder
    builder = CorpusBuilder()
    
    # Add only the text file first
    print("1. Adding text source...")
    success = builder.add_text_file("swahili_corpus/azimio.text")
    print(f"   - azimio.text: {'✓' if success else '✗'}")
    
    # Process the texts
    print("\n2. Processing text...")
    builder.process_texts(
        remove_punctuation=True,
        lowercase=True,
        min_word_length=2,
        remove_numbers=True
    )
    
    # Get statistics
    print("\n3. Corpus Statistics:")
    stats = builder.get_stats()
    print(f"   - Total words: {stats['total_words']:,}")
    print(f"   - Unique words: {stats['unique_words']:,}")
    print(f"   - Sources: {', '.join(stats['sources'])}")
    
    # Show top 10 words
    print("\n4. Top 10 most frequent words:")
    for i, (word, count) in enumerate(stats['top_words'][:10], 1):
        print(f"   {i:2d}. {word:15s} ({count:,} times)")
    
    # Save the corpus
    print("\n5. Saving corpus...")
    success = builder.save_corpus("swahili_corpus/simple_corpus.json")
    print(f"   - Corpus saved: {'✓' if success else '✗'}")
    
    overall_elapsed = time.time() - overall_start
    print(f"\n=== Simple Test Complete in {overall_elapsed:.1f}s ===")

if __name__ == "__main__":
    test_text_file_only() 