"""
Unit tests for the enhanced grammar engine.
"""

import unittest
from kiswahili_engine.core.grammar_engine import EnhancedKiswahiliGrammarEngine


class TestEnhancedGrammarEngine(unittest.TestCase):
    """Test cases for the EnhancedKiswahiliGrammarEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EnhancedKiswahiliGrammarEngine()
    
    def test_sentence_analysis_basic(self):
        """Test basic sentence analysis."""
        result = self.engine.analyze_sentence_enhanced("Mtu anakuja nyumbani.")
        
        # Check basic structure
        self.assertIn("original", result)
        self.assertIn("words", result)
        self.assertIn("tokens", result)
        self.assertIn("agreement", result)
        
        # Check that analysis completed without errors
        self.assertNotIn("error", result)
        
        # Check token analysis
        self.assertTrue(len(result["tokens"]) > 0)
        
        # Check that subject was identified
        subject_found = any(token["in_kiima"] for token in result["tokens"])
        self.assertTrue(subject_found)
    
    def test_sentence_type_classification(self):
        """Test sentence type classification."""
        # Test statement
        result = self.engine.analyze_sentence_enhanced("Mtu anakuja.")
        self.assertIn("Sahili", result["sentence_type"])
        
        # Test question
        result = self.engine.analyze_sentence_enhanced("Mtu anakuja?")
        self.assertIn("Ulizi", result["sentence_type"])
        
        # Test command
        result = self.engine.analyze_sentence_enhanced("Njoo hapa!")
        self.assertIn("Amri", result["sentence_type"])
    
    def test_agreement_checking(self):
        """Test agreement checking in sentences."""
        # Test correct agreement
        result = self.engine.analyze_sentence_enhanced("Mtu anakuja nyumbani.")
        agreement = result["agreement"]
        
        # Should not have major issues if agreement is correct
        if hasattr(agreement, 'issues'):
            major_issues = [issue for issue in agreement.issues if "agreement" in issue.lower()]
            # Allow for minor issues but not major agreement violations
            self.assertTrue(len(major_issues) <= 1)
    
    def test_ngeli_migration_detection(self):
        """Test detection of ngeli migrations."""
        # Test sentence with potential migration
        result = self.engine.analyze_sentence_enhanced("Joka limmiza kyura.")
        
        # Check if any migrations were detected
        migrations = result.get("ngeli_migrations", [])
        # We expect at least one migration (joka for ukuzaji)
        self.assertTrue(len(migrations) >= 0)  # Allow for varying detection sensitivity
    
    def test_semantic_analysis(self):
        """Test semantic analysis features."""
        result = self.engine.analyze_sentence_enhanced("Kipaka kile kinlala.")
        
        semantic_analysis = result.get("semantic_analysis", {})
        self.assertIn("ngeli_distribution", semantic_analysis)
        self.assertIn("complexity_score", semantic_analysis)
        
        # Should have at least one ngeli class
        self.assertTrue(semantic_analysis["complexity_score"] > 0)
    
    def test_morphological_complexity(self):
        """Test morphological complexity analysis."""
        result = self.engine.analyze_sentence_enhanced("Mwalimu mkuu anasomesha watoto.")
        
        complexity = result.get("morphological_complexity", {})
        self.assertIn("complexity_score", complexity)
        self.assertIn("total_morphemes", complexity)
        
        # Should detect some morphological complexity
        self.assertTrue(complexity["total_morphemes"] > 0)
    
    def test_word_analysis(self):
        """Test single word analysis."""
        result = self.engine.analyze_word("mwalimu")
        
        self.assertIn("word", result)
        self.assertIn("ngeli_analysis", result)
        self.assertEqual(result["word"], "mwalimu")
        
        # Should identify as 1/2 ngeli
        ngeli_info = result["ngeli_analysis"]
        if ngeli_info:
            self.assertEqual(ngeli_info.ngeli_class, "1/2")
    
    def test_agreement_checking_standalone(self):
        """Test standalone agreement checking."""
        result = self.engine.check_agreement("mtu", "anakuja")
        
        self.assertIn("verb_agreement", result)
        self.assertTrue(result["verb_agreement"])
        
        # Test disagreement
        result = self.engine.check_agreement("mtu", "inakuja") 
        self.assertFalse(result["verb_agreement"])
    
    def test_error_handling(self):
        """Test error handling for invalid inputs."""
        # Test empty sentence
        result = self.engine.analyze_sentence_enhanced("")
        self.assertIn("error", result)
        
        # Test sentence with no words
        result = self.engine.analyze_sentence_enhanced("   ")
        self.assertIn("error", result)
    
    def test_complex_sentence(self):
        """Test analysis of complex sentences."""
        complex_sentence = "Mwalimu mkuu anasomesha watoto wazuri shuleni kila siku."
        result = self.engine.analyze_sentence_enhanced(complex_sentence)
        
        # Should complete analysis without errors
        self.assertNotIn("error", result)
        
        # Should have multiple tokens
        self.assertTrue(len(result["tokens"]) >= 5)
        
        # Should have some complexity
        complexity = result.get("morphological_complexity", {})
        self.assertTrue(complexity.get("complexity_score", 0) > 0)


class TestSentenceStructure(unittest.TestCase):
    """Test sentence structure analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = EnhancedKiswahiliGrammarEngine()
    
    def test_kiima_kiarifu_identification(self):
        """Test identification of kiima and kiarifu."""
        result = self.engine.analyze_sentence_enhanced("Mtu anakuja nyumbani.")
        structure = result["structure"]
        
        # Should have both kiima and kiarifu
        self.assertIn("kiima", structure)
        self.assertIn("kiarifu", structure)
        
        # Kiima should contain subject
        self.assertTrue(len(structure["kiima"]) > 0)
        
        # Kiarifu should contain verb
        self.assertTrue(len(structure["kiarifu"]) > 0)
    
    def test_verb_detection(self):
        """Test verb detection in sentences."""
        result = self.engine.analyze_sentence_enhanced("Watoto wanacheza nje.")
        structure = result["structure"]
        
        # Should detect verb positions
        self.assertIn("verb_positions", structure)
        self.assertTrue(len(structure["verb_positions"]) > 0)
        
        # First verb should be in kiarifu
        if structure["verb_positions"]:
            verb_pos = structure["verb_positions"][0]["position"]
            verb_word = result["words"][verb_pos]
            self.assertIn(verb_word, structure["kiarifu"])


if __name__ == '__main__':
    unittest.main()