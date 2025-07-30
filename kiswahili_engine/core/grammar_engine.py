"""
Enhanced Ki-Micheweni grammar engine for comprehensive sentence analysis.

This module provides the main interface for analyzing Kiswahili sentences
using the enhanced 18-ngeli system with semantic functions.
"""

from typing import Dict, List, Any, Optional
import re

from .types import SentenceType, SyntacticRole, AgreementAnalysis, VerbAnalysis
from .ngeli_system import EnhancedNgeliSystem


class EnhancedKiswahiliGrammarEngine:
    """
    Enhanced Ki-Micheweni grammar engine with full ngeli support.
    
    This is the main interface for analyzing Kiswahili sentences according to
    the Ki-Micheweni dialect patterns documented in the research by 
    Hamad Khamis Juma (2015).
    
    Features:
    - Full 18-ngeli system support
    - Semantic function detection
    - Ngeli migration analysis
    - Enhanced agreement checking
    - Comprehensive morphological analysis
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize the grammar engine.
        
        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.ngeli_system = EnhancedNgeliSystem()
        
        # Sentence type classification patterns
        self.sentence_type_patterns = {
            "conditional": [
                (["kama", "ikiwa"], ["basi", "ndipo"], "Changamani (Conditional)"),
                (["ingawa", "ijapokuwa"], [], "Changamani (Concessive)"),
                (["hata"], ["bado"], "Changamani (Even if)")
            ],
            "conjunctive": {
                "na": "Ambatano (Conjunctive)",
                "lakini": "Ambatano (Adversative)", 
                "wala": "Ambatano (Negative)",
                "au": "Ambatano (Disjunctive)",
                "kisha": "Ambatano (Sequential)",
                "tena": "Ambatano (Additive)"
            }
        }
    
    def analyze_sentence_enhanced(self, sentence: str) -> Dict[str, Any]:
        """
        Enhanced sentence analysis with full ngeli awareness.
        
        Args:
            sentence: The sentence to analyze
            
        Returns:
            Comprehensive analysis dictionary containing:
            - Basic sentence information
            - Token-level analysis
            - Agreement checking
            - Ngeli migrations
            - Semantic analysis
            - Human-readable explanation
        """
        # Clean and validate input
        sentence = re.sub(r'\s+', ' ', sentence.strip())
        if not sentence:
            return {"error": "Empty sentence"}
        
        # Tokenize
        words = [w for w in re.findall(r'\b\w+\b', sentence) if w]
        if not words:
            return {"error": "No valid words found"}
        
        # Initialize result structure
        result = {
            "original": sentence,
            "words": words,
            "sentence_type": self._classify_sentence_type_enhanced(sentence, words),
            "structure": self._analyze_sentence_structure_enhanced(sentence, words),
            "tokens": [],
            "agreement": {},
            "ngeli_migrations": [],
            "semantic_analysis": {},
            "morphological_complexity": {},
            "explanation": ""
        }
        
        # Analyze each token with enhanced context
        for i, word in enumerate(words):
            context = {
                "sentence": sentence,
                "position": i,
                "neighboring_words": words[max(0, i-1):i+2],
                "sentence_structure": result["structure"]
            }
            token_analysis = self._analyze_token_enhanced(word, context, result["structure"])
            result["tokens"].append(token_analysis)
            
            # Check for ngeli migration
            migration = self.ngeli_system.detect_ngeli_migration(word, context)
            if migration["migration_detected"]:
                result["ngeli_migrations"].append({
                    "word": word,
                    "migration": migration
                })
        
        # Enhanced agreement analysis
        result["agreement"] = self._check_sentence_agreement_enhanced(result["tokens"], sentence)
        
        # Semantic analysis summary
        result["semantic_analysis"] = self._generate_semantic_summary(result["tokens"])
        
        # Morphological complexity analysis
        result["morphological_complexity"] = self._analyze_morphological_complexity(result["tokens"])
        
        # Generate comprehensive explanation
        result["explanation"] = self._generate_enhanced_explanation(result)
        
        return result
    
    def _classify_sentence_type_enhanced(self, sentence: str, words: List[str]) -> str:
        """
        Enhanced sentence type classification using OFP 008 principles.
        
        Args:
            sentence: The complete sentence
            words: List of words in the sentence
            
        Returns:
            Classified sentence type string
        """
        # Basic punctuation check
        if sentence.endswith("?"):
            return SentenceType.ULIZI.value
        if sentence.endswith("!"):
            return SentenceType.AMRI.value
        
        # Enhanced conditional detection
        for initial_words, final_words, sentence_type in self.sentence_type_patterns["conditional"]:
            if any(word in words for word in initial_words):
                if not final_words or any(word in words for word in final_words):
                    return sentence_type
        
        # Enhanced conjunction detection
        for conjunction, sentence_type in self.sentence_type_patterns["conjunctive"].items():
            if conjunction in words:
                return sentence_type
        
        return SentenceType.SAHILI.value
    
    def _analyze_sentence_structure_enhanced(self, sentence: str, words: List[str]) -> Dict[str, Any]:
        """
        Enhanced sentence structure analysis (kiima/kiarifu).
        
        Args:
            sentence: The complete sentence
            words: List of words
            
        Returns:
            Structure analysis with kiima, kiarifu, and verb positions
        """
        structure = {
            "kiima": [],
            "kiarifu": [],
            "explanation": [],
            "verb_positions": [],
            "complex_predicates": [],
            "word_roles": {}
        }
        
        # Find all verbs with enhanced detection
        verb_indices = []
        for i, word in enumerate(words):
            verb_analysis = self.ngeli_system.analyze_verb_structure_enhanced(word)
            if verb_analysis["tense"] or self._contains_verbal_markers(word):
                verb_indices.append(i)
                structure["verb_positions"].append({
                    "position": i,
                    "word": word,
                    "analysis": verb_analysis
                })
        
        # Determine kiima/kiarifu split
        if verb_indices:
            first_verb_idx = verb_indices[0]
            structure["kiima"] = words[:first_verb_idx] if first_verb_idx > 0 else []
            structure["kiarifu"] = words[first_verb_idx:]
            
            # Handle complex predicates (multiple verbs)
            if len(verb_indices) > 1:
                main_verb = words[verb_indices[0]]
                auxiliary_verbs = [words[i] for i in verb_indices[1:]]
                structure["complex_predicates"].append({
                    "main_verb": main_verb,
                    "auxiliary_verbs": auxiliary_verbs
                })
        else:
            # Default fallback
            structure["kiima"] = [words[0]] if words else []
            structure["kiarifu"] = words[1:] if len(words) > 1 else []
        
        # Assign word roles
        for i, word in enumerate(words):
            if word in structure["kiima"]:
                structure["word_roles"][word] = SyntacticRole.KIIMA.value
            elif word in structure["kiarifu"]:
                if i in verb_indices:
                    structure["word_roles"][word] = SyntacticRole.KITENZI.value
                else:
                    structure["word_roles"][word] = SyntacticRole.NOMINO.value
        
        structure["explanation"].append(
            f"Kiima: {' '.join(structure['kiima'])} | Kiarifu: {' '.join(structure['kiarifu'])}"
        )
        
        return structure
    
    def _contains_verbal_markers(self, word: str) -> bool:
        """Check if word contains verbal tense markers"""
        tense_markers = ["-na-", "-me-", "-ta-", "-li-", "-ki-", "-se-"]
        return any(marker.strip('-') in word.lower() for marker in tense_markers)
    
    def _analyze_token_enhanced(self, word: str, context: Dict, structure: Dict) -> Dict[str, Any]:
        """
        Enhanced token analysis with full contextual information.
        
        Args:
            word: The word to analyze
            context: Contextual information
            structure: Sentence structure information
            
        Returns:
            Comprehensive token analysis
        """
        token = {
            "word": word,
            "position": context["position"],
            "in_kiima": word in structure["kiima"],
            "in_kiarifu": word in structure["kiarifu"],
            "ngeli_analysis": None,
            "verb_analysis": None,
            "syntactic_role": None,
            "semantic_function": None,
            "morphological_breakdown": {},
            "agreement_patterns": {},
            "phonological_processes": [],
            "explanation": []
        }
        
        # Enhanced ngeli analysis with context
        ngeli_info = self.ngeli_system.identify_ngeli_enhanced(word, context)
        if ngeli_info:
            token["ngeli_analysis"] = {
                "ngeli": ngeli_info.ngeli_class,
                "number": ngeli_info.number,
                "semantic_function": ngeli_info.semantic_function.value,
                "confidence": ngeli_info.confidence,
                "morphological_analysis": ngeli_info.morphological_analysis
            }
            token["semantic_function"] = ngeli_info.semantic_function.value
            token["morphological_breakdown"] = ngeli_info.morphological_analysis
            
            # Extract phonological processes
            if "phonological_changes" in ngeli_info.morphological_analysis:
                token["phonological_processes"] = ngeli_info.morphological_analysis["phonological_changes"]
            
            # Determine syntactic role based on position and ngeli
            if token["in_kiima"]:
                token["syntactic_role"] = SyntacticRole.KIIMA.value
                token["explanation"].append(
                    f"Subject: '{word}' (ngeli {ngeli_info.ngeli_class}, {ngeli_info.number})"
                )
            else:
                token["syntactic_role"] = SyntacticRole.NOMINO.value
                token["explanation"].append(
                    f"Noun: '{word}' (ngeli {ngeli_info.ngeli_class}, {ngeli_info.number})"
                )
        
        # Enhanced verb analysis
        if token["in_kiarifu"]:
            verb_analysis = self.ngeli_system.analyze_verb_structure_enhanced(word, context)
            if verb_analysis["tense"]:
                token["verb_analysis"] = verb_analysis
                token["syntactic_role"] = SyntacticRole.KITENZI.value
                token["explanation"].append(
                    f"Verb: '{word}' ({verb_analysis['tense']} tense)"
                )
                
                # Extract morphological breakdown from verb analysis
                token["morphological_breakdown"].update(verb_analysis["structure"])
        
        # Default role assignment
        if not token["syntactic_role"]:
            token["syntactic_role"] = SyntacticRole.NOMINO.value
        
        return token
    
    def _check_sentence_agreement_enhanced(self, tokens: List[Dict], sentence: str) -> AgreementAnalysis:
        """
        Enhanced agreement checking across the sentence.
        
        Args:
            tokens: List of analyzed tokens
            sentence: Original sentence
            
        Returns:
            AgreementAnalysis object with comprehensive results
        """
        agreement = AgreementAnalysis()
        
        # Find subject and main verb
        subject_token = next((t for t in tokens if t["in_kiima"] and t["ngeli_analysis"]), None)
        verb_token = next((t for t in tokens if t["in_kiarifu"] and t["verb_analysis"]), None)
        
        if subject_token and verb_token:
            # Check subject-verb agreement using enhanced system
            agreement_check = self.ngeli_system.check_enhanced_agreement(
                subject_token["word"], 
                verb_token["word"], 
                context={"sentence": sentence}
            )
            
            agreement.subject_verb_agreement = agreement_check["verb_agreement"]
            agreement.detailed_analysis.extend(agreement_check["explanation"])
            
            if not agreement_check["verb_agreement"]:
                agreement.issues.append("Subject-verb agreement violation")
            
            # Add special cases information
            if agreement_check.get("special_cases"):
                agreement.detailed_analysis.extend(agreement_check["special_cases"])
        
        # Check for ngeli consistency across sentence
        ngeli_usage = {}
        for token in tokens:
            if token["ngeli_analysis"]:
                ngeli = token["ngeli_analysis"]["ngeli"]
                if ngeli not in ngeli_usage:
                    ngeli_usage[ngeli] = []
                ngeli_usage[ngeli].append(token["word"])
        
        agreement.ngeli_consistency = ngeli_usage
        
        # Overall coherence assessment
        if agreement.issues:
            agreement.overall_coherence = False
        
        return agreement
    
    def _generate_semantic_summary(self, tokens: List[Dict]) -> Dict[str, Any]:
        """
        Generate semantic analysis summary.
        
        Args:
            tokens: List of analyzed tokens
            
        Returns:
            Semantic analysis summary
        """
        semantic_functions = {}
        ngeli_distribution = {}
        morphological_processes = []
        
        for token in tokens:
            # Collect semantic functions
            if token["semantic_function"] and token["semantic_function"] != "neutral":
                func = token["semantic_function"]
                if func not in semantic_functions:
                    semantic_functions[func] = []
                semantic_functions[func].append(token["word"])
            
            # Collect ngeli distribution
            if token["ngeli_analysis"]:
                ngeli = token["ngeli_analysis"]["ngeli"]
                if ngeli not in ngeli_distribution:
                    ngeli_distribution[ngeli] = 0
                ngeli_distribution[ngeli] += 1
            
            # Collect morphological processes
            if token["phonological_processes"]:
                morphological_processes.extend(token["phonological_processes"])
        
        return {
            "semantic_functions": semantic_functions,
            "ngeli_distribution": ngeli_distribution,
            "morphological_processes": list(set(morphological_processes)),
            "complexity_score": len(ngeli_distribution),
            "semantic_diversity": len(semantic_functions)
        }
    
    def _analyze_morphological_complexity(self, tokens: List[Dict]) -> Dict[str, Any]:
        """
        Analyze morphological complexity of the sentence.
        
        Args:
            tokens: List of analyzed tokens
            
        Returns:
            Morphological complexity analysis
        """
        complexity = {
            "total_morphemes": 0,
            "phonological_processes": 0,
            "zero_morphemes": 0,
            "complex_verbs": 0,
            "migrated_ngeli": 0,
            "complexity_score": 0.0
        }
        
        for token in tokens:
            # Count morphemes
            if token["morphological_breakdown"]:
                breakdown = token["morphological_breakdown"]
                if "prefix" in breakdown and breakdown["prefix"]:
                    complexity["total_morphemes"] += 1
                if "root" in breakdown and breakdown["root"]:
                    complexity["total_morphemes"] += 1
                if breakdown.get("prefix") == "Ø":
                    complexity["zero_morphemes"] += 1
            
            # Count phonological processes
            if token["phonological_processes"]:
                complexity["phonological_processes"] += len(token["phonological_processes"])
            
            # Count complex verbs
            if token["verb_analysis"] and token["verb_analysis"].get("structure", {}).get("tense_marker"):
                complexity["complex_verbs"] += 1
            
            # Count migrated ngeli
            if token["semantic_function"] and token["semantic_function"] != "neutral":
                complexity["migrated_ngeli"] += 1
        
        # Calculate overall complexity score
        total_tokens = len(tokens)
        if total_tokens > 0:
            complexity["complexity_score"] = (
                (complexity["phonological_processes"] * 0.3) +
                (complexity["zero_morphemes"] * 0.2) +
                (complexity["complex_verbs"] * 0.3) +
                (complexity["migrated_ngeli"] * 0.2)
            ) / total_tokens
        
        return complexity
    
    def _generate_enhanced_explanation(self, analysis: Dict) -> str:
        """
        Generate comprehensive explanation of the analysis.
        
        Args:
            analysis: Complete sentence analysis
            
        Returns:
            Human-readable explanation string
        """
        explanation = f"Enhanced Analysis of: '{analysis['original']}'\n"
        explanation += "=" * 60 + "\n\n"
        
        # Sentence type and structure
        explanation += f"Sentence Type: {analysis['sentence_type']}\n"
        explanation += f"Structure: {analysis['structure']['explanation'][0]}\n\n"
        
        # Token analysis
        explanation += "Detailed Token Analysis:\n"
        explanation += "-" * 30 + "\n"
        for token in analysis["tokens"]:
            explanation += f"• {token['word']}: {token['syntactic_role']}\n"
            for detail in token["explanation"]:
                explanation += f"  └─ {detail}\n"
            
            if token["ngeli_analysis"]:
                nga = token["ngeli_analysis"]
                explanation += f"  └─ Morphology: {nga['morphological_analysis']}\n"
                if nga["semantic_function"] != "neutral":
                    explanation += f"  └─ Semantic function: {nga['semantic_function']}\n"
            
            if token["phonological_processes"]:
                explanation += f"  └─ Phonological processes: {', '.join(token['phonological_processes'])}\n"
            
            explanation += "\n"
        
        # Agreement analysis
        explanation += "Agreement Analysis:\n"
        explanation += "-" * 20 + "\n"
        if analysis["agreement"].issues:
            explanation += "⚠️ Issues detected:\n"
            for issue in analysis["agreement"].issues:
                explanation += f"  • {issue}\n"
        else:
            explanation += "✅ All elements show proper agreement\n"
        
        for detail in analysis["agreement"].detailed_analysis:
            explanation += f"  • {detail}\n"
        
        explanation += "\n"
        
        # Ngeli migrations
        if analysis["ngeli_migrations"]:
            explanation += "Ngeli Migrations Detected:\n"
            explanation += "-" * 25 + "\n"
            for migration in analysis["ngeli_migrations"]:
                mig = migration["migration"]
                explanation += f"• {migration['word']}: {mig['canonical_ngeli']} → {mig['current_ngeli']}\n"
                explanation += f"  └─ Reason: {mig['reason']}\n"
            explanation += "\n"
        
        # Semantic summary
        sem = analysis["semantic_analysis"]
        if sem["semantic_functions"]:
            explanation += "Semantic Functions:\n"
            explanation += "-" * 18 + "\n"
            for func, words in sem["semantic_functions"].items():
                explanation += f"• {func}: {', '.join(words)}\n"
        
        explanation += f"\nNgeli Distribution: {sem['ngeli_distribution']}\n"
        explanation += f"Complexity Score: {sem['complexity_score']}/18 ngeli classes used\n"
        
        # Morphological complexity
        morph = analysis["morphological_complexity"]
        explanation += f"Morphological Complexity: {morph['complexity_score']:.2f}\n"
        
        # Add semantic processes if available
        sem = analysis["semantic_analysis"]
        if sem.get("morphological_processes"):
            explanation += f"Processes: {', '.join(set(sem['morphological_processes']))}\n"
        
        return explanation
    
    def analyze_word(self, word: str, context: Dict = None) -> Dict[str, Any]:
        """
        Analyze a single word in isolation or with context.
        
        Args:
            word: Word to analyze
            context: Optional context information
            
        Returns:
            Complete word analysis
        """
        ngeli_info = self.ngeli_system.identify_ngeli_enhanced(word, context or {})
        migration = self.ngeli_system.detect_ngeli_migration(word, context or {})
        
        return {
            "word": word,
            "ngeli_analysis": ngeli_info,
            "migration_analysis": migration,
            "morphological_breakdown": ngeli_info.morphological_analysis if ngeli_info else {},
            "semantic_function": ngeli_info.semantic_function.value if ngeli_info else "unknown"
        }
    
    def check_agreement(self, subject: str, verb: str, adjective: str = None) -> Dict[str, Any]:
        """
        Check agreement between sentence elements.
        
        Args:
            subject: Subject noun
            verb: Main verb
            adjective: Optional adjective
            
        Returns:
            Agreement analysis results
        """
        return self.ngeli_system.check_enhanced_agreement(subject, verb, adjective)