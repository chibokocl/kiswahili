#!/usr/bin/env python3
"""
Basic usage examples for the Ki-Micheweni Grammar Engine.

This script demonstrates the key features of the enhanced grammar engine
including ngeli identification, semantic functions, and agreement checking.
"""

import sys
import os

# Add the parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from kiswahili_engine import create_engine, analyze_sentence
from kiswahili_engine.utils.formatters import ResultFormatter


def demonstrate_basic_analysis():
    """Demonstrate basic sentence analysis."""
    print("🔍 Basic Sentence Analysis")
    print("=" * 50)
    
    sentences = [
        "Mwalimu anasomesha watoto shuleni.",
        "Joka kubwa limmiza chura.",
        "Kipaka kidogo kinlala kitandani.",
        "Macho yamejaa maji."
    ]
    
    engine = create_engine()
    
    for sentence in sentences:
        print(f"\n📝 Analyzing: '{sentence}'")
        print("-" * 40)
        
        result = engine.analyze_sentence_enhanced(sentence)
        summary = ResultFormatter.format_summary(result)
        print(summary)


def demonstrate_word_analysis():
    """Demonstrate individual word analysis."""
    print("\n\n🔤 Individual Word Analysis")
    print("=" * 50)
    
    words = ["mwalimu", "joka", "kipaka", "macho"]
    engine = create_engine()
    
    for word in words:
        print(f"\n🔍 Word: '{word}'")
        print("-" * 20)
        
        result = engine.analyze_word(word)
        formatted = ResultFormatter.format_word_analysis(result)
        print(formatted)


def demonstrate_semantic_functions():
    """Demonstrate semantic function detection."""
    print("\n\n🎭 Semantic Functions")
    print("=" * 50)
    
    examples = [
        ("Joka kubwa limmiza chura", "Ukuzaji (Augmentative)"),
        ("Kipaka kidogo kinlala", "Udogoshaji (Diminutive)"),
        ("Kizee kibaya kinaiba", "Dharau (Contempt)"),
        ("Kitoto kizuri kinacheza", "Sifa Nzuri (Positive qualities)")
    ]
    
    engine = create_engine()
    
    for sentence, expected_function in examples:
        print(f"\n📝 {sentence}")
        print(f"Expected: {expected_function}")
        
        result = engine.analyze_sentence_enhanced(sentence)
        
        # Extract semantic functions from tokens
        semantic_functions = []
        for token in result.get('tokens', []):
            if token.get('semantic_function') and token['semantic_function'] != 'neutral':
                semantic_functions.append(f"{token['word']}: {token['semantic_function']}")
        
        if semantic_functions:
            print(f"Detected: {', '.join(semantic_functions)}")
        else:
            print("Detected: No special semantic functions")


def demonstrate_agreement_checking():
    """Demonstrate agreement checking."""
    print("\n\n✅ Agreement Checking")
    print("=" * 50)
    
    test_cases = [
        ("mtu", "anakuja", "✅ Correct agreement"),
        ("mtu", "inakuja", "❌ Incorrect agreement"),
        ("watu", "wanakuja", "✅ Correct agreement"),
        ("watu", "anakuja", "❌ Incorrect agreement")
    ]
    
    engine = create_engine()
    
    for subject, verb, expected in test_cases:
        print(f"\n🔍 {subject} + {verb}")
        print(f"Expected: {expected}")
        
        result = engine.check_agreement(subject, verb)
        
        if result.get('verb_agreement'):
            print("Result: ✅ Agreement is correct")
        else:
            print("Result: ❌ Agreement violation detected")


def demonstrate_ngeli_migrations():
    """Demonstrate ngeli migration detection."""
    print("\n\n🔄 Ngeli Migrations")
    print("=" * 50)
    
    sentences_with_migrations = [
        "Ng'ombe in'chinjwa sokoni.",
        "Kipaka kidogo kinlala vizuri.",
        "Joka kubwa limemeza chura."
    ]
    
    engine = create_engine()
    
    for sentence in sentences_with_migrations:
        print(f"\n📝 {sentence}")
        
        result = engine.analyze_sentence_enhanced(sentence)
        migrations = result.get('ngeli_migrations', [])
        
        if migrations:
            print("🔄 Migrations detected:")
            for migration in migrations:
                mig = migration['migration']
                print(f"  • {migration['word']}: {mig['canonical_ngeli']} → {mig['current_ngeli']}")
                print(f"    Reason: {mig['reason']}")
        else:
            print("No migrations detected")


def demonstrate_morphological_analysis():
    """Demonstrate morphological complexity analysis."""
    print("\n\n🔬 Morphological Analysis")
    print("=" * 50)
    
    complex_sentence = "Mwalimu mkuu anawasomesha watoto wazuri masomo magumu shuleni kila siku."
    
    engine = create_engine()
    result = engine.analyze_sentence_enhanced(complex_sentence)
    
    print(f"📝 Sentence: {complex_sentence}")
    print("\n🔍 Morphological Breakdown:")
    
    for token in result.get('tokens', []):
        word = token['word']
        breakdown = token.get('morphological_breakdown', {})
        
        if breakdown.get('prefix') and breakdown.get('root'):
            print(f"  • {word}: {breakdown['prefix']} + {breakdown['root']}")
        else:
            print(f"  • {word}: (no clear morphological structure)")
        
        if token.get('phonological_processes'):
            for process in token['phonological_processes']:
                print(f"    └─ {process}")
    
    complexity = result.get('morphological_complexity', {})
    print(f"\n📊 Complexity Score: {complexity.get('complexity_score', 0):.2f}")
    print(f"📊 Total Morphemes: {complexity.get('total_morphemes', 0)}")


def main():
    """Run all demonstrations."""
    print("🇹🇿 Ki-Micheweni Grammar Engine - Usage Examples")
    print("=" * 60)
    print("Based on research by Hamad Khamis Juma (2015)")
    print("Enhanced with 18-ngeli system and semantic functions")
    print("=" * 60)
    
    try:
        demonstrate_basic_analysis()
        demonstrate_word_analysis()
        demonstrate_semantic_functions()
        demonstrate_agreement_checking()
        demonstrate_ngeli_migrations()
        demonstrate_morphological_analysis()
        
        print("\n\n✨ All demonstrations completed successfully!")
        print("\nFor more advanced usage, see the API documentation.")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("Please check that the kiswahili_engine package is properly installed.")


if __name__ == "__main__":
    main()