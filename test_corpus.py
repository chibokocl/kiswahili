#!/usr/bin/env python3
"""
Test script for the Swahili Corpus Builder
"""

import time
from swahili_spell.corpus import CorpusBuilder

def test_corpus_builder():
    """Test the corpus builder with existing Swahili files."""
    
    print("=== Swahili Corpus Builder Test ===\n")
    overall_start = time.time()
    
    # Initialize the corpus builder
    builder = CorpusBuilder()
    
    # Add the existing files
    print("1. Adding text sources...")
    
    # Add the text file
    success = builder.add_text_file("swahili_corpus/azimio.text")
    print(f"   - azimio.text: {'✓' if success else '✗'}")
    
    # Add PDF files
    success = builder.add_pdf("swahili_corpus/Biblia.pdf")
    print(f"   - Biblia.pdf: {'✓' if success else '✗'}")
    
    success = builder.add_pdf("swahili_corpus/kamusi.pdf")
    print(f"   - kamusi.pdf: {'✓' if success else '✗'}")
    
    # Process the texts
    print("\n2. Processing texts...")
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
    success = builder.save_corpus("swahili_corpus/swahili_corpus.json")
    print(f"   - Corpus saved: {'✓' if success else '✗'}")
    
    success = builder.save_dictionary("swahili_corpus/swahili_words.txt")
    print(f"   - Dictionary saved: {'✓' if success else '✗'}")
    
    overall_elapsed = time.time() - overall_start
    print(f"\n=== Test Complete in {overall_elapsed:.1f}s ===")

if __name__ == "__main__":
    test_corpus_builder() 