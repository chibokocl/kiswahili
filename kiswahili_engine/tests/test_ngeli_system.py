"""
Unit tests for the enhanced ngeli system.
"""

import unittest
from kiswahili_engine.core.ngeli_system import EnhancedNgeliSystem
from kiswahili_engine.core.types import SemanticFunction


class TestEnhancedNgeliSystem(unittest.TestCase):
    """Test cases for the EnhancedNgeliSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ngeli_system = EnhancedNgeliSystem()
    
    def test_identify_ngeli_basic(self):
        """Test basic ngeli identification."""
        # Test 1/2 ngeli
        result = self.ngeli_system.identify_ngeli_enhanced("mtu")
        self.assertIsNotNone(result)
        self.assertEqual(result.ngeli_class, "1/2")
        self.assertEqual(result.number, "singular")
        
        # Test 3/4 ngeli
        result = self.ngeli_system.identify_ngeli_enhanced("mti")
        self.assertIsNotNone(result)
        self.assertEqual(result.ngeli_class, "3/4")
        self.assertEqual(result.number, "singular")
        
        # Test 7/8 ngeli
        result = self.ngeli_system.identify_ngeli_enhanced("kisu")
        self.assertIsNotNone(result)
        self.assertEqual(result.ngeli_class, "7/8")
        self.assertEqual(result.number, "singular")
    
    def test_phonological_rules(self):
        """Test phonological rule application."""
        # Test nasal mutation
        result = self.ngeli_system.phonological_rules.apply_nasal_mutation("m", "tu")
        self.assertEqual(result, "n")
        
        # Test vowel coalescence
        prefix, root = self.ngeli_system.phonological_rules.handle_vowel_coalescence("mu", "embe")
        self.assertEqual(prefix, "mw")
        self.assertEqual(root, "embe")
    
    def test_semantic_functions(self):
        """Test semantic function detection."""
        context = {"sentence": "Joka kubwa limmiza kyura"}
        result = self.ngeli_system.identify_ngeli_enhanced("joka", context)
        # Should detect ukuzaji due to "kubwa" in context
        self.assertEqual(result.semantic_function, SemanticFunction.UKUZAJI)
    
    def test_agreement_checking(self):
        """Test agreement between sentence elements."""
        result = self.ngeli_system.check_enhanced_agreement("mtu", "anakuja")
        self.assertTrue(result["verb_agreement"])
        
        # Test disagreement
        result = self.ngeli_system.check_enhanced_agreement("mtu", "inakuja")
        self.assertFalse(result["verb_agreement"])
    
    def test_zero_morpheme_handling(self):
        """Test handling of zero morphemes."""
        result = self.ngeli_system.identify_ngeli_enhanced("mama")
        self.assertIsNotNone(result)
        # Should identify as 1a/2a with zero prefix
        self.assertIn(result.ngeli_class, ["1/2", "1a/2a"])
    
    def test_migration_detection(self):
        """Test ngeli migration detection."""
        # Test known migration case
        migration = self.ngeli_system.detect_ngeli_migration("ng'ombe")
        if migration["migration_detected"]:
            self.assertEqual(migration["canonical_ngeli"], "1/2")
            self.assertEqual(migration["current_ngeli"], "9/10")
    
    def test_verb_analysis(self):
        """Test verb structure analysis."""
        result = self.ngeli_system.analyze_verb_structure_enhanced("anakuja")
        self.assertIsNotNone(result["tense"])
        self.assertEqual(result["tense"], "present")
        self.assertIsNotNone(result["structure"]["subject_prefix"])


class TestPhonologicalRules(unittest.TestCase):
    """Test cases for phonological rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        from kiswahili_engine.core.phonology import PhonologicalRules
        self.phonology = PhonologicalRules()
    
    def test_nasal_mutation(self):
        """Test nasal mutation rules."""
        # Should mutate before most consonants
        self.assertEqual(self.phonology.apply_nasal_mutation("m", "tu"), "n")
        self.assertEqual(self.phonology.apply_nasal_mutation("m", "ti"), "n")
        
        # Should not mutate before bilabials/labiodentals
        self.assertEqual(self.phonology.apply_nasal_mutation("m", "papa"), "m")
        self.assertEqual(self.phonology.apply_nasal_mutation("m", "baba"), "m")
    
    def test_vowel_coalescence(self):
        """Test vowel coalescence rules."""
        # mu- + V -> mw- + V
        prefix, root = self.phonology.handle_vowel_coalescence("mu", "embe")
        self.assertEqual(prefix, "mw")
        self.assertEqual(root, "embe")
        
        # ki- + V -> ky- + V
        prefix, root = self.phonology.handle_vowel_coalescence("ki", "atu")
        self.assertEqual(prefix, "ky")
        self.assertEqual(root, "atu")
    
    def test_morphophonological_analysis(self):
        """Test comprehensive morphophonological analysis."""
        analyses = self.phonology.analyze_morphophonology("mwembe", ["mu-", "m-"])
        self.assertTrue(len(analyses) > 0)
        
        # Should find the coalescence analysis
        found_coalescence = False
        for prefix, root, processes in analyses:
            if "coalescence" in str(processes):
                found_coalescence = True
                break
        self.assertTrue(found_coalescence)


if __name__ == '__main__':
    unittest.main()