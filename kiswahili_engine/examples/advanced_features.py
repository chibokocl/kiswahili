#!/usr/bin/env python3
"""
Advanced features demonstration for the Ki-Micheweni Grammar Engine.

This script showcases advanced capabilities including custom analysis,
batch processing, and integration with other tools.
"""

import sys
import os
import json

# Add the parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from kiswahili_engine import create_engine
from kiswahili_engine.core.types import SemanticFunction
from kiswahili_engine.utils.formatters import ResultFormatter
from kiswahili_engine.utils.validation import InputValidator


def demonstrate_custom_context():
    """Demonstrate analysis with custom context."""
    print("🔧 Custom Context Analysis")
    print("=" * 50)
    
    engine = create_engine()
    
    # Example with custom semantic function context
    word = "paka"
    contexts = [
        {"sentence": "Paka mdogo anacheza", "semantic_function": "udogoshaji"},
        {"sentence": "Paka mkubwa anasonga", "semantic_function": "ukuzaji"},
        {"sentence": "Paka mbaya ameiba", "semantic_function": "dharau"}
    ]
    
    for context in contexts:
        print(f"\n🔍 Word: '{word}' in context: '{context['sentence']}'")
        result = engine.analyze_word(word, context)
        
        ngeli_info = result.get('ngeli_analysis')
        if ngeli_info:
            print(f"  Ngeli: {ngeli_info.ngeli_class}")
            print(f"  Semantic function: {ngeli_info.semantic_function.value}")
            print(f"  Confidence: {ngeli_info.confidence:.2f}")


def demonstrate_batch_processing():
    """Demonstrate batch processing of multiple sentences."""
    print("\n\n📦 Batch Processing")
    print("=" * 50)
    
    sentences = [
        "Mwalimu anasomesha watoto.",
        "Joka kubwa limemeza chura.",
        "Kipaka kidogo kinlala.",
        "Macho yamejaa maji.",
        "Ng'ombe wanachunga majani."
    ]
    
    engine = create_engine()
    results = []
    
    print("Processing sentences...")
    for i, sentence in enumerate(sentences, 1):
        print(f"  {i}. {sentence}")
        result = engine.analyze_sentence_enhanced(sentence)
        results.append(result)
    
    # Generate comparison
    print("\n📊 Batch Analysis Results:")
    comparison = ResultFormatter.format_comparison(results)
    print(comparison)
    
    return results


def demonstrate_json_export():
    """Demonstrate exporting results to JSON."""
    print("\n\n💾 JSON Export")
    print("=" * 50)
    
    engine = create_engine()
    sentence = "Mwalimu mkuu anawasomesha watoto wazuri masomo magumu."
    
    result = engine.analyze_sentence_enhanced(sentence)
    
    # Export to JSON
    json_output = ResultFormatter.format_for_json(result)
    
    print(f"📝 Analyzed: {sentence}")
    print("🔍 JSON Output (first 500 characters):")
    print(json_output[:500] + "..." if len(json_output) > 500 else json_output)
    
    # Optionally save to file
    # with open('analysis_result.json', 'w', encoding='utf-8') as f:
    #     f.write(json_output)
    # print("\n💾 Full result saved to 'analysis_result.json'")


def demonstrate_input_validation():
    """Demonstrate input validation features."""
    print("\n\n🛡️ Input Validation")
    print("=" * 50)
    
    test_inputs = [
        "Mtu anakuja.",           # Valid
        "",                      # Empty
        "A" * 1000,             # Too long
        "Hello world!",         # English (still valid characters)
        "Mtu@#$%",              # Invalid characters
        "bcdfghjkl"             # No vowels
    ]
    
    for test_input in test_inputs:
        display_input = test_input if len(test_input) < 50 else test_input[:47] + "..."
        
        # Validate sentence
        is_valid, error = InputValidator.validate_sentence(test_input)
        
        print(f"\n🔍 Input: '{display_input}'")
        if is_valid:
            print("  ✅ Valid")
        else:
            print(f"  ❌ Invalid: {error}")


def demonstrate_ngeli_system_details():
    """Demonstrate detailed ngeli system information."""
    print("\n\n🏗️ Ngeli System Details")
    print("=" * 50)
    
    engine = create_engine()
    ngeli_system = engine.ngeli_system
    
    print("📊 Available Ngeli Classes:")
    for ngeli_class, data in ngeli_system.ngeli_classes.items():
        examples = ", ".join(data.get("examples", [])[:3])
        domains = ", ".join(data.get("semantic_domains", [])[:2])
        
        print(f"  • {ngeli_class}: {examples}")
        print(f"    Domains: {domains}")
        
        if data.get("can_migrate_to"):
            print(f"    Can migrate to: {', '.join(data['can_migrate_to'])}")
        
        if data.get("special_rules"):
            print(f"    Special: {data['special_rules'][0]}")
        print()


def demonstrate_phonological_analysis():
    """Demonstrate phonological rule analysis."""
    print("\n\n🔊 Phonological Analysis")
    print("=" * 50)
    
    engine = create_engine()
    phonology = engine.ngeli_system.phonological_rules
    
    test_cases = [
        ("mu", "embe", "Vowel coalescence"),
        ("m", "tu", "Nasal mutation"),
        ("ki", "atu", "Vowel coalescence"),
        ("m", "papa", "No mutation (bilabial)")
    ]
    
    for prefix, root, description in test_cases:
        print(f"\n🔍 {description}: {prefix} + {root}")
        
        # Test nasal mutation
        mutated = phonology.apply_nasal_mutation(prefix, root)
        if mutated != prefix:
            print(f"  Nasal mutation: {prefix} → {mutated}")
        
        # Test vowel coalescence
        coalesced_prefix, coalesced_root = phonology.handle_vowel_coalescence(prefix, root)
        if coalesced_prefix != prefix:
            print(f"  Vowel coalescence: {prefix} + {root} → {coalesced_prefix} + {coalesced_root}")
        
        if mutated == prefix and coalesced_prefix == prefix:
            print(f"  No changes applied")


def demonstrate_error_handling():
    """Demonstrate error handling and recovery."""
    print("\n\n🚨 Error Handling")
    print("=" * 50)
    
    engine = create_engine()
    
    error_cases = [
        ("", "Empty sentence"),
        ("   ", "Whitespace only"),
        ("12345", "Numbers only"),
        ("@#$%", "Special characters only")
    ]
    
    for test_input, description in error_cases:
        print(f"\n🔍 {description}: '{test_input}'")
        
        try:
            result = engine.analyze_sentence_enhanced(test_input)
            
            if "error" in result:
                print(f"  ✅ Error handled gracefully: {result['error']}")
            else:
                print(f"  ⚠️ Unexpected success")
                
        except Exception as e:
            print(f"  ❌ Unhandled exception: {e}")


def demonstrate_performance_analysis():
    """Demonstrate performance analysis features."""
    print("\n\n⚡ Performance Analysis")
    print("=" * 50)
    
    import time
    
    engine = create_engine()
    
    # Test sentences of varying complexity
    test_sentences = [
        "Mtu anakuja.",  # Simple
        "Mwalimu anasomesha watoto shuleni.",  # Medium
        "Mwalimu mkuu anawasomesha watoto wazuri masomo magumu shuleni kila siku."  # Complex
    ]
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n🔍 Test {i}: {len(sentence.split())} words")
        
        start_time = time.time()
        result = engine.analyze_sentence_enhanced(sentence)
        end_time = time.time()
        
        processing_time = end_time - start_time
        complexity_score = result.get('morphological_complexity', {}).get('complexity_score', 0)
        ngeli_count = len(result.get('semantic_analysis', {}).get('ngeli_distribution', {}))
        
        print(f"  ⏱️ Processing time: {processing_time:.3f}s")
        print(f"  📊 Complexity score: {complexity_score:.2f}")
        print(f"  📊 Ngeli classes used: {ngeli_count}/18")


def main():
    """Run all advanced demonstrations."""
    print("🚀 Ki-Micheweni Grammar Engine - Advanced Features")
    print("=" * 60)
    print("Demonstrating advanced capabilities and integration features")
    print("=" * 60)
    
    try:
        demonstrate_custom_context()
        demonstrate_batch_processing()
        demonstrate_json_export()
        demonstrate_input_validation()
        demonstrate_ngeli_system_details()
        demonstrate_phonological_analysis()
        demonstrate_error_handling()
        demonstrate_performance_analysis()
        
        print("\n\n🎉 All advanced demonstrations completed successfully!")
        print("\nThese examples show the engine's capabilities for:")
        print("  • Custom context analysis")
        print("  • Batch processing")
        print("  • Data export and integration")
        print("  • Robust error handling")
        print("  • Performance monitoring")
        
    except Exception as e:
        print(f"\n❌ Error during advanced demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()