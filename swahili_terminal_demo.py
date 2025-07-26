"""
Swahili Terminal Demo

A comprehensive terminal-based demonstration of the Swahili language processing system
that showcases dynamic, context-aware suggestions without any hardcoded responses.
"""

import sys
import time
from swahili_context_analyzer import SwahiliContextAnalyzer
from swahili_spell_checker import spell_check_text, correction
from swahili_predictor import predict_word, predict_with_context, WORDS

class SwahiliTerminalDemo:
    """Interactive terminal demo for Swahili language processing."""
    
    def __init__(self):
        """Initialize the demo with all analyzers."""
        print("Loading Swahili language processing system...")
        self.analyzer = SwahiliContextAnalyzer()
        print("✅ System loaded successfully!")
        print()
    
    def run_interactive_demo(self):
        """Run the main interactive demo loop."""
        print("🎯 Swahili Language Processing Demo")
        print("=" * 50)
        print("This demo showcases dynamic, context-aware suggestions")
        print("No hardcoded responses - everything is generated from your corpus!")
        print()
        
        while True:
            print("\n📝 Choose a demo mode:")
            print("1. Word Prediction (type partial words)")
            print("2. Spell Checking (test misspellings)")
            print("3. Context Analysis (analyze word relationships)")
            print("4. Sentence Completion (complete sentences)")
            print("5. Grammatical Analysis (check sentence correctness)")
            print("6. Auto-generate test cases")
            print("7. Exit")
            
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                self.word_prediction_demo()
            elif choice == '2':
                self.spell_checking_demo()
            elif choice == '3':
                self.context_analysis_demo()
            elif choice == '4':
                self.sentence_completion_demo()
            elif choice == '5':
                self.grammatical_analysis_demo()
            elif choice == '6':
                self.auto_generate_tests()
            elif choice == '7':
                print("\n👋 Thanks for using the Swahili Language Processing Demo!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.")
    
    def word_prediction_demo(self):
        """Interactive word prediction demo."""
        print("\n🔤 Word Prediction Demo")
        print("-" * 30)
        print("Type partial words and see intelligent suggestions!")
        print("(Type 'back' to return to main menu)")
        
        while True:
            partial = input("\nEnter partial word: ").strip().lower()
            if partial == 'back':
                break
            
            if partial:
                suggestions = predict_word(partial)
                print(f"\n💡 Suggestions for '{partial}':")
                for i, word in enumerate(suggestions, 1):
                    freq = WORDS.get(word, 0)
                    print(f"  {i}. {word} (freq: {freq})")
            else:
                print("❌ Please enter a partial word.")
    
    def spell_checking_demo(self):
        """Interactive spell checking demo."""
        print("\n✅ Spell Checking Demo")
        print("-" * 30)
        print("Test misspellings and see corrections!")
        print("(Type 'back' to return to main menu)")
        
        while True:
            word = input("\nEnter word to check: ").strip().lower()
            if word == 'back':
                break
            
            if word:
                corrected = correction(word)
                if corrected != word:
                    print(f"🔧 Correction: '{word}' → '{corrected}'")
                else:
                    print(f"✅ '{word}' is correct!")
            else:
                print("❌ Please enter a word.")
    
    def context_analysis_demo(self):
        """Interactive context analysis demo."""
        print("\n🧠 Context Analysis Demo")
        print("-" * 30)
        print("See how words relate to each other in context!")
        print("(Type 'back' to return to main menu)")
        
        while True:
            word = input("\nEnter a word to analyze: ").strip().lower()
            if word == 'back':
                break
            
            if word:
                context_info = self.analyzer.analyze_word_context(word)
                print(f"\n📊 Context analysis for '{word}':")
                print(f"  Frequency: {context_info['frequency']}")
                print(f"  Category: {context_info['category']}")
                print(f"  Related words: {', '.join(context_info['related_words'][:5])}")
            else:
                print("❌ Please enter a word.")
    
    def sentence_completion_demo(self):
        """Interactive sentence completion demo."""
        print("\n📝 Sentence Completion Demo")
        print("-" * 30)
        print("Complete sentences with context-aware suggestions!")
        print("(Type 'back' to return to main menu)")
        
        while True:
            sentence = input("\nEnter partial sentence: ").strip()
            if sentence == 'back':
                break
            
            if sentence:
                suggestions = self.analyzer.complete_sentence(sentence)
                print(f"\n💡 Completion suggestions:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"  {i}. {suggestion}")
            else:
                print("❌ Please enter a sentence.")
    
    def grammatical_analysis_demo(self):
        """Interactive grammatical analysis demo."""
        print("\n📚 Grammatical Analysis Demo")
        print("-" * 30)
        print("Check if Swahili sentences are grammatically correct!")
        print("(Type 'back' to return to main menu)")
        
        while True:
            sentence = input("\nEnter a sentence to analyze: ").strip()
            if sentence == 'back':
                break
            
            if sentence:
                analysis = self.analyzer.analyze_grammatical_correctness(sentence)
                
                print(f"\n📊 Analysis for: '{sentence}'")
                print("=" * 50)
                
                # Overall assessment
                if analysis['is_correct']:
                    print("✅ Sentence appears to be grammatically correct!")
                else:
                    print("❌ Sentence has grammatical issues.")
                
                print(f"📈 Grammar Score: {analysis['grammar_score']:.2f}")
                
                # Word-by-word analysis
                print("\n🔍 Word Analysis:")
                for word, info in analysis['word_analysis'].items():
                    status = "✅" if info['exists_in_corpus'] else "❌"
                    print(f"  {status} '{word}' (freq: {info['frequency']})")
                    if info['suggestions']:
                        print(f"     💡 Suggestions: {', '.join(info['suggestions'])}")
                
                # Issues found
                if analysis['issues']:
                    print("\n⚠️ Issues Found:")
                    for issue in analysis['issues']:
                        print(f"  • {issue}")
                
                # Suggestions
                if analysis['suggestions']:
                    print(f"\n💡 Overall Suggestions: {', '.join(set(analysis['suggestions']))}")
                
            else:
                print("❌ Please enter a sentence.")

    def auto_generate_tests(self):
        """Auto-generate and run test cases from corpus data."""
        print("\n🤖 Auto-Generated Test Cases")
        print("-" * 30)
        print("Generating test cases from your corpus data...")
        
        # Generate word prediction tests
        print("\n🔤 Word Prediction Tests:")
        common_words = [word for word, freq in self.analyzer.words.most_common(20)]
        for word in common_words[:5]:
            partial = word[:2]  # Take first 2 letters
            suggestions = predict_word(partial)
            print(f"  '{partial}' → {[w for w, _ in suggestions[:3]]}")
        
        # Generate spell checking tests
        print("\n✅ Spell Checking Tests:")
        for word in common_words[:5]:
            # Create a simple misspelling
            misspelled = word[:-1] + 'x' if len(word) > 2 else word + 'x'
            corrected = correction(misspelled)
            print(f"  '{misspelled}' → '{corrected}'")
        
        # Generate context tests
        print("\n🧠 Context Analysis Tests:")
        for word in common_words[:3]:
            context_info = self.analyzer.analyze_word_context(word)
            print(f"  '{word}' → Category: {context_info['category']}")
        
        print("\n✅ All tests completed!")

def main():
    """Main entry point."""
    demo = SwahiliTerminalDemo()
    demo.run_interactive_demo()

if __name__ == "__main__":
    main() 