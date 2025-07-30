#!/usr/bin/env python3
"""
KI-MICHEWENI GRAMMAR ENGINE - ENHANCED NGELI IMPLEMENTATION

A comprehensive grammar engine implementing the full 18-ngeli system as documented in
'ngeli za kiswahili.pdf' (Hamad Khamis Juma, 2015). This engine:
- Implements all 18 ngeli classes found in Ki-Micheweni dialect
- Handles complex allomorphic variations and phonological rules
- Supports semantic functions (ukuzaji, udogoshaji, dharau, sifa)
- Manages ngeli migration and dialectal variations
- Processes zero morphemes and complex morphophonological patterns
- Implements proper KK, KY, KV agreement systems
- Follows OFP 008 principles for sentence analysis
"""

import re
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from enum import Enum
from dataclasses import dataclass

class SemanticFunction(Enum):
    """Semantic functions that can trigger ngeli changes"""
    NEUTRAL = "neutral"
    UKUZAJI = "ukuzaji"  # Augmentative - size, fear, respect
    UDOGOSHAJI = "udogoshaji"  # Diminutive - small, endearing
    DHARAU = "dharau"  # Contempt, bad behavior
    SIFA_NZURI = "sifa_nzuri"  # Good qualities, beauty
    MZAHA = "mzaha"  # Humor, joking
    CHUKI = "chuki"  # Hatred, disgust

@dataclass
class NgeliInfo:
    """Complete information about a ngeli classification"""
    ngeli_class: str
    number: str  # singular/plural
    semantic_function: SemanticFunction
    confidence: float
    morphological_analysis: Dict[str, str]
    
class PhonologicalRules:
    """Handles phonological processes in Ki-Micheweni"""
    
    @staticmethod
    def apply_nasal_mutation(prefix: str, root: str) -> str:
        """Apply nasal mutation rules: m- -> n- before certain consonants"""
        if not root:
            return prefix
            
        first_consonant = root[0].lower()
        
        # m- becomes n- except before p, b, f, v
        if prefix.startswith('m') and first_consonant not in ['p', 'b', 'f', 'v']:
            return prefix.replace('m', 'n', 1)
        
        return prefix
    
    @staticmethod
    def handle_vowel_coalescence(prefix: str, root: str) -> Tuple[str, str]:
        """Handle vowel coalescence when prefix ends with vowel and root starts with vowel"""
        if not prefix or not root:
            return prefix, root
            
        if prefix.endswith(('u', 'i', 'a')) and root.startswith(('a', 'e', 'i', 'o', 'u')):
            # Common pattern: mu- + embe -> mwembe
            if prefix.endswith('u'):
                return prefix[:-1] + 'w', root
            elif prefix.endswith('i'):
                return prefix[:-1] + 'y', root
                
        return prefix, root

class EnhancedNgeliSystem:
    """Enhanced Ki-Micheweni noun class system with full 18-ngeli support"""
    
    def __init__(self):
        self.phonological_rules = PhonologicalRules()
        
        # Complete 18-ngeli system based on Ki-Micheweni research
        self.ngeli_classes = {
            "1/2": {
                "singular_prefixes": ["mu-", "m-", "n-", "mw-", "Ø-"],
                "plural_prefixes": ["wa-"],
                "kk": {"singular": "a-", "plural": "wa-"},
                "ky": {"singular": "n-", "plural": "wa-"},
                "kv": {"singular": "n-", "plural": "wa-"},
                "semantic_domains": ["humans", "kinship", "professions", "tribes"],
                "examples": ["mtu", "mwanafunzi", "mwalimu", "mwanamke", "mama", "dada"],
                "can_migrate_to": ["7/8"],  # For semantic functions
                "special_rules": ["Family terms can use Ø- prefix", "Agent nouns from verbs"]
            },
            "1a/2a": {
                "singular_prefixes": ["Ø-"],
                "plural_prefixes": ["Ø-"],
                "kk": {"singular": "a-", "plural": "wa-"},
                "ky": {"singular": "n-", "plural": "wa-"},
                "kv": {"singular": "n-", "plural": "wa-"},
                "semantic_domains": ["family_relations"],
                "examples": ["mame", "dade", "kake", "shangazi"],
                "special_rules": ["Zero prefix family terms"]
            },
            "3/4": {
                "singular_prefixes": ["mu-", "m-", "n-", "mw-"],
                "plural_prefixes": ["mi-"],
                "kk": {"singular": "u-", "plural": "i-"},
                "ky": {"singular": "n-", "plural": "mi-"},
                "kv": {"singular": "n-", "plural": "mi-"},
                "semantic_domains": ["plants", "body_parts", "tools", "natural_objects"],
                "examples": ["mti", "mto", "mchungwa", "mpira", "mkono", "mwili"],
                "special_rules": ["Nasal mutation applies", "Vowel coalescence mu- + V -> mw-"]
            },
            "5/6": {
                "singular_prefixes": ["j-", "Ø-", "i-", "zi-"],
                "plural_prefixes": ["ma-"],
                "kk": {"singular": "li-", "plural": "ya-"},
                "ky": {"singular": "j-", "plural": "ma-"},
                "kv": {"singular": "Ø-", "plural": "ma-"},
                "semantic_domains": ["body_parts", "fruits", "products", "buildings", "natural_features"],
                "examples": ["jicho", "jipu", "jogoo", "goti", "limau", "daraja"],
                "can_accept_from": ["3/4", "1/2"],  # For ukuzaji
                "special_rules": ["Often uses zero prefix in singular", "Ukuzaji function"]
            },
            "7/8": {
                "singular_prefixes": ["ki-", "ky-"],
                "plural_prefixes": ["vi-", "vy-"],
                "kk": {"singular": "ki-", "plural": "vi-"},
                "ky": {"singular": "ki-", "plural": "vi-"},
                "kv": {"singular": "ki-", "plural": "vi-"},
                "semantic_domains": ["tools", "body_parts", "languages", "groups", "disabilities"],
                "examples": ["kisu", "kikombe", "kiti", "kichwa", "Kiswahili", "kichaa"],
                "can_accept_from": ["1/2", "3/4", "9/10"],  # For udogoshaji, sifa
                "special_rules": ["Diminutive function", "Language names", "Disability terms use 1/2 agreement"]
            },
            "9/10": {
                "singular_prefixes": ["n-", "Ø-"],
                "plural_prefixes": ["n-", "Ø-"],
                "kk": {"singular": "i-", "plural": "zi-"},
                "ky": {"singular": "n-", "plural": "n-"},
                "kv": {"singular": "n-", "plural": "n-"},
                "semantic_domains": ["animals", "foods", "objects", "abstract_concepts", "borrowed_words"],
                "examples": ["nyumba", "ndizi", "nchi", "nyani", "nyama", "sabuni"],
                "can_accept_from": ["1/2"],  # Animals from 1/2 for certain contexts
                "special_rules": ["Same prefix for singular and plural", "Many borrowed words"]
            },
            "11/10a": {
                "singular_prefixes": ["u-"],
                "plural_prefixes": ["n-"],
                "kk": {"singular": "u-", "plural": "zi-"},
                "ky": {"singular": "u-", "plural": "n-"},
                "kv": {"singular": "u-", "plural": "n-"},
                "semantic_domains": ["body_parts", "abstract_concepts", "long_thin_objects"],
                "examples": ["ulimi", "umoja", "ukuta", "uso", "uzi"],
                "special_rules": ["Some take plural in 10a (zi-)"]
            },
            "12/13": {
                "singular_prefixes": ["ka-"],
                "plural_prefixes": ["tu-"],
                "kk": {"singular": "ka-", "plural": "tu-"},
                "ky": {"singular": "ka-", "plural": "tu-"},
                "kv": {"singular": "ka-", "plural": "tu-"},
                "semantic_domains": ["diminutives"],
                "examples": [],  # Marked as absent in Ki-Micheweni
                "special_rules": ["Not productive in Ki-Micheweni"]
            },
            "14/6a": {
                "singular_prefixes": ["u-"],
                "plural_prefixes": ["ma-"],
                "kk": {"singular": "u-", "plural": "ya-"},
                "ky": {"singular": "u-", "plural": "ma-"},
                "kv": {"singular": "u-", "plural": "ma-"},
                "semantic_domains": ["abstract_concepts", "diseases", "professions"],
                "examples": ["ugonjwa", "utoto", "umoja", "upendo", "ujamaa"],
                "special_rules": ["Derived from other word classes"]
            },
            "15": {
                "singular_prefixes": ["ku-"],
                "plural_prefixes": ["ku-"],
                "kk": {"singular": "ku-", "plural": "ku-"},
                "ky": {"singular": "ku-", "plural": "ku-"},
                "kv": {"singular": "ku-", "plural": "ku-"},
                "semantic_domains": ["infinitives", "gerunds"],
                "examples": ["kuja", "kula", "kunywa", "kupiga", "kuvyaa"],
                "special_rules": ["Infinitive forms", "No true plural"]
            },
            "16": {
                "singular_prefixes": ["pa-"],
                "plural_prefixes": ["mwa-"],
                "kk": {"singular": "pa-", "plural": "mu-"},
                "ky": {"singular": "pa-", "plural": "mu-"},
                "kv": {"singular": "pa-", "plural": "mu-"},
                "semantic_domains": ["definite_location"],
                "examples": ["pahali", "pangoni", "pembezoni"],
                "special_rules": ["Specific/definite location"]
            },
            "17": {
                "singular_prefixes": ["ku-", "kwa-"],
                "plural_prefixes": ["ku-"],
                "kk": {"singular": "ku-", "plural": "ku-"},
                "ky": {"singular": "ku-", "plural": "mu-"},
                "kv": {"singular": "ku-", "plural": "mu-"},
                "semantic_domains": ["indefinite_location", "distant_location"],
                "examples": ["kule", "kulelewa", "kuwepo", "kwahali"],
                "special_rules": ["Distant/indefinite location"]
            },
            "18": {
                "singular_prefixes": ["mu-"],
                "plural_prefixes": [],
                "kk": {"singular": "mu-", "plural": "mu-"},
                "ky": {"singular": "mu-", "plural": "mu-"},
                "kv": {"singular": "mu-", "plural": "mu-"},
                "semantic_domains": ["interior_location"],
                "examples": ["mahali", "muhali"],
                "special_rules": ["Interior/inside location"]
            }
        }
        
        # Build reverse mapping for prefix identification
        self.prefix_to_ngeli = self._build_prefix_mapping()
        
        # Semantic domains for migration detection
        self.semantic_domains = {
            "animals": ["mbwa", "paka", "ng'ombe", "nyuki", "joka", "tumbili"],
            "people": ["mtu", "msichana", "mvulana", "mzee", "mwanamke"],
            "diminutive_triggers": ["kidogo", "ndogo", "mdogo"],
            "augmentative_triggers": ["kubwa", "mkubwa", "mzito"]
        }
        
        # Tense markers from OFP 008
        self.tense_markers = {
            "-na-": "present",
            "-me-": "perfect", 
            "-ta-": "future",
            "-li-": "past_definite",
            "-ki-": "contingent",
            "-se-": "subjunctive",
            "-ka-": "consecutive",
            "-nge-": "conditional",
            "-ngali-": "past_conditional"
        }

    def _build_prefix_mapping(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build mapping from prefixes to possible ngeli classes"""
        prefix_map = {}
        
        for ngeli, data in self.ngeli_classes.items():
            # Add noun prefixes
            for prefix_type in ["singular_prefixes", "plural_prefixes"]:
                if prefix_type in data:
                    number = "singular" if "singular" in prefix_type else "plural"
                    for prefix in data[prefix_type]:
                        clean_prefix = prefix.rstrip('-')
                        if clean_prefix not in prefix_map:
                            prefix_map[clean_prefix] = []
                        prefix_map[clean_prefix].append((ngeli, number))
            
            # Add agreement prefixes
            for role in ["kk", "ky", "kv"]:
                if role in data:
                    for number, prefix in data[role].items():
                        clean_prefix = prefix.rstrip('-')
                        if clean_prefix not in prefix_map:
                            prefix_map[clean_prefix] = []
                        prefix_map[clean_prefix].append((ngeli, number))
        
        return prefix_map

    def identify_ngeli_enhanced(self, word: str, context: Dict = None) -> Optional[NgeliInfo]:
        """Enhanced ngeli identification with semantic and phonological analysis"""
        word = word.lower().strip()
        context = context or {}
        
        candidates = []
        
        # Try different prefix patterns
        for ngeli, data in self.ngeli_classes.items():
            # Check singular prefixes
            for prefix in data.get("singular_prefixes", []):
                confidence, analysis = self._match_prefix_pattern(word, prefix, ngeli, "singular", data)
                if confidence > 0:
                    candidates.append((ngeli, "singular", confidence, analysis))
            
            # Check plural prefixes  
            for prefix in data.get("plural_prefixes", []):
                confidence, analysis = self._match_prefix_pattern(word, prefix, ngeli, "plural", data)
                if confidence > 0:
                    candidates.append((ngeli, "plural", confidence, analysis))
        
        if not candidates:
            return None
            
        # Sort by confidence and apply semantic analysis
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        best_ngeli, best_number, best_confidence, best_analysis = candidates[0]
        
        # Determine semantic function based on context
        semantic_func = self._determine_semantic_function(word, best_ngeli, context)
        
        return NgeliInfo(
            ngeli_class=best_ngeli,
            number=best_number,
            semantic_function=semantic_func,
            confidence=best_confidence,
            morphological_analysis=best_analysis
        )

    def _match_prefix_pattern(self, word: str, prefix: str, ngeli: str, number: str, ngeli_data: Dict) -> Tuple[float, Dict]:
        """Match word against prefix pattern with phonological rules"""
        if prefix == "Ø-":
            # Zero prefix - check if word fits semantic domain
            semantic_domains = ngeli_data.get("semantic_domains", [])
            if self._word_fits_semantic_domain(word, semantic_domains):
                return 0.8, {"prefix": "Ø-", "root": word, "phonological_changes": []}
            return 0.0, {}
        
        clean_prefix = prefix.rstrip('-')
        if not clean_prefix:
            return 0.0, {}
            
        # Check direct match
        if word.startswith(clean_prefix):
            root = word[len(clean_prefix):]
            if len(root) >= 2:  # Ensure substantial root
                return 0.9, {
                    "prefix": clean_prefix,
                    "root": root,
                    "phonological_changes": []
                }
        
        # Check with phonological rules
        if len(word) > len(clean_prefix):
            root = word[len(clean_prefix):]
            
            # Try nasal mutation
            mutated_prefix = self.phonological_rules.apply_nasal_mutation(clean_prefix, root)
            if word.startswith(mutated_prefix) and mutated_prefix != clean_prefix:
                actual_root = word[len(mutated_prefix):]
                if len(actual_root) >= 2:
                    return 0.85, {
                        "prefix": mutated_prefix,
                        "root": actual_root,
                        "phonological_changes": [f"{clean_prefix} -> {mutated_prefix} (nasal mutation)"]
                    }
            
            # Try vowel coalescence
            coalesced_prefix, modified_root = self.phonological_rules.handle_vowel_coalescence(clean_prefix, root)
            reconstructed = coalesced_prefix + modified_root
            if reconstructed == word:
                return 0.85, {
                    "prefix": coalesced_prefix,
                    "root": modified_root,
                    "phonological_changes": [f"{clean_prefix} + {root} -> {coalesced_prefix} + {modified_root} (coalescence)"]
                }
        
        return 0.0, {}

    def _word_fits_semantic_domain(self, word: str, domains: List[str]) -> bool:
        """Check if word semantically fits the given domains"""
        # Simple keyword matching - could be enhanced with ML/embeddings
        domain_keywords = {
            "humans": ["tu", "na", "mu", "wa"],
            "family_relations": ["mama", "baba", "dada", "kaka", "shangazi"],
            "plants": ["mti", "ua", "mche"],
            "body_parts": ["cho", "guu", "kono", "wi"],
            "tools": ["su", "kombe", "ti"],
            "animals": ["bwa", "paka", "ombe", "uki"],
            "foods": ["zi", "nama", "chakula"],
            "locations": ["hali", "ni", "le"]
        }
        
        for domain in domains:
            if domain in domain_keywords:
                for keyword in domain_keywords[domain]:
                    if keyword in word:
                        return True
        return False

    def _determine_semantic_function(self, word: str, ngeli: str, context: Dict) -> SemanticFunction:
        """Determine semantic function based on context and ngeli migration patterns"""
        
        # Check for explicit semantic markers in context
        if "semantic_function" in context:
            return SemanticFunction(context["semantic_function"])
        
        # Check for ngeli migration patterns
        sentence = context.get("sentence", "")
        
        # Ukuzaji indicators (5/4 for size/fear)
        if ngeli in ["5/6", "5/4"] and any(word in sentence.lower() for word in 
                                          ["kubwa", "mkubwa", "mzito", "mrefu", "ogopa"]):
            return SemanticFunction.UKUZAJI
        
        # Udogoshaji indicators (7/8 for small/cute)
        if ngeli == "7/8" and any(word in sentence.lower() for word in 
                                ["kidogo", "mdogo", "mzuri", "mchumba"]):
            return SemanticFunction.UDOGOSHAJI
        
        # Dharau indicators (7/8 for contempt)
        if ngeli == "7/8" and any(word in sentence.lower() for word in 
                                ["mbaya", "mwizi", "mlevi", "mchafu"]):
            return SemanticFunction.DHARAU
        
        # Sifa nzuri indicators
        if any(word in sentence.lower() for word in 
               ["mzuri", "mrembo", "hodari", "mwema"]):
            return SemanticFunction.SIFA_NZURI
        
        return SemanticFunction.NEUTRAL

    def get_agreement_prefix(self, ngeli: str, number: str, role: str) -> Optional[str]:
        """Get agreement prefix for KK, KY, KV roles"""
        if ngeli not in self.ngeli_classes:
            return None
        
        ngeli_data = self.ngeli_classes[ngeli]
        if role not in ngeli_data:
            return None
            
        return ngeli_data[role].get(number)

    def check_enhanced_agreement(self, subject: str, verb: str, adjective: Optional[str] = None, 
                                context: Dict = None) -> Dict[str, Any]:
        """Enhanced agreement checking with semantic analysis"""
        context = context or {}
        result = {
            "subject_analysis": None,
            "verb_agreement": False,
            "adjective_agreement": False if adjective else None,
            "semantic_analysis": {},
            "explanation": []
        }
        
        # Analyze subject
        subject_info = self.identify_ngeli_enhanced(subject, context)
        if not subject_info:
            result["explanation"].append(f"Could not identify ngeli for subject '{subject}'")
            return result
        
        result["subject_analysis"] = subject_info
        ngeli = subject_info.ngeli_class
        number = subject_info.number
        
        # Enhanced verb analysis
        verb_analysis = self.analyze_verb_structure_enhanced(verb, {"subject_ngeli": ngeli, "subject_number": number})
        
        # Check verb agreement
        expected_kk = self.get_agreement_prefix(ngeli, number, "kk")
        if expected_kk:
            if verb_analysis.get("subject_prefix") == expected_kk.rstrip('-'):
                result["verb_agreement"] = True
                result["explanation"].append(
                    f"✓ Verb '{verb}' agrees with subject '{subject}' (ngeli {ngeli}, {number})"
                )
            else:
                result["explanation"].append(
                    f"✗ Verb '{verb}' disagrees with subject '{subject}' - expected {expected_kk}, got {verb_analysis.get('subject_prefix', 'none')}"
                )
        
        # Check adjective agreement
        if adjective:
            expected_kv = self.get_agreement_prefix(ngeli, number, "kv")
            if expected_kv and adjective.startswith(expected_kv.rstrip('-')):
                result["adjective_agreement"] = True
                result["explanation"].append(
                    f"✓ Adjective '{adjective}' agrees with subject '{subject}'"
                )
            else:
                result["explanation"].append(
                    f"✗ Adjective '{adjective}' disagrees - expected {expected_kv}"
                )
        
        # Semantic analysis
        result["semantic_analysis"] = {
            "function": subject_info.semantic_function.value,
            "confidence": subject_info.confidence,
            "morphological_details": subject_info.morphological_analysis
        }
        
        return result

    def analyze_verb_structure_enhanced(self, verb: str, context: Dict = None) -> Dict[str, Any]:
        """Enhanced verb structure analysis with better morphological parsing"""
        context = context or {}
        analysis = {
            "word": verb,
            "structure": {
                "subject_prefix": None,
                "object_prefix": None,
                "tense_marker": None,
                "root": None,
                "extensions": [],
                "final_vowel": None
            },
            "ngeli": None,
            "number": None,
            "tense": None,
            "explanation": []
        }
        
        working_verb = verb.lower()
        
        # Extract final vowel
        if working_verb and working_verb[-1] in "aeiou":
            analysis["structure"]["final_vowel"] = working_verb[-1]
            working_verb = working_verb[:-1]
        else:
            analysis["explanation"].append("No valid final vowel found")
            return analysis
        
        # Extract tense marker
        tense_found = False
        for tense_marker, tense_name in self.tense_markers.items():
            clean_marker = tense_marker.strip('-')
            if clean_marker in working_verb:
                analysis["structure"]["tense_marker"] = clean_marker
                analysis["tense"] = tense_name
                # Split around tense marker
                parts = working_verb.split(clean_marker, 1)
                if len(parts) == 2:
                    prefix_part, root_part = parts
                    working_verb = prefix_part + root_part
                    tense_found = True
                    break
        
        if not tense_found:
            analysis["explanation"].append("No tense marker identified")
        
        # Extract subject prefix using ngeli system
        subject_ngeli = context.get("subject_ngeli")
        subject_number = context.get("subject_number")
        
        if subject_ngeli and subject_number:
            expected_prefix = self.get_agreement_prefix(subject_ngeli, subject_number, "kk")
            if expected_prefix:
                clean_expected = expected_prefix.rstrip('-')
                if working_verb.startswith(clean_expected):
                    analysis["structure"]["subject_prefix"] = clean_expected
                    analysis["ngeli"] = subject_ngeli
                    analysis["number"] = subject_number
                    working_verb = working_verb[len(clean_expected):]
        
        # What remains should be root + extensions
        if working_verb:
            # Simple root extraction (could be enhanced with extension analysis)
            analysis["structure"]["root"] = working_verb
        
        # Generate explanation
        if analysis["structure"]["subject_prefix"]:
            explanation = f"Verb structure: {analysis['structure']['subject_prefix']}"
            if analysis["structure"]["tense_marker"]:
                explanation += f"-{analysis['structure']['tense_marker']}"
            if analysis["structure"]["root"]:
                explanation += f"-{analysis['structure']['root']}"
            if analysis["structure"]["final_vowel"]:
                explanation += f"-{analysis['structure']['final_vowel']}"
            
            if analysis["ngeli"] and analysis["number"]:
                explanation += f" [ngeli {analysis['ngeli']}, {analysis['number']}]"
            
            analysis["explanation"].insert(0, explanation)
        
        return analysis

    def detect_ngeli_migration(self, word: str, context: Dict = None) -> Dict[str, Any]:
        """Detect if word has migrated from its canonical ngeli class"""
        context = context or {}
        
        # Get current classification
        current_analysis = self.identify_ngeli_enhanced(word, context)
        if not current_analysis:
            return {"migration_detected": False, "reason": "Could not classify word"}
        
        current_ngeli = current_analysis.ngeli_class
        
        # Check semantic domains for canonical class
        canonical_ngeli = self._get_canonical_ngeli(word)
        
        if canonical_ngeli and canonical_ngeli != current_ngeli:
            return {
                "migration_detected": True,
                "canonical_ngeli": canonical_ngeli,
                "current_ngeli": current_ngeli,
                "semantic_function": current_analysis.semantic_function.value,
                "reason": self._explain_migration(canonical_ngeli, current_ngeli, current_analysis.semantic_function)
            }
        
        return {"migration_detected": False, "canonical_ngeli": canonical_ngeli}

    def _get_canonical_ngeli(self, word: str) -> Optional[str]:
        """Determine canonical ngeli class based on semantic content"""
        # This would be enhanced with a proper lexicon
        word_lower = word.lower()
        
        # People words typically go to 1/2
        if any(marker in word_lower for marker in ["mtu", "tu", "mu", "mw"]) and \
           not word_lower.startswith(('ki', 'vi')):  # Exclude diminutives
            return "1/2"
        
        # Animals typically 1/2 or 9/10
        if any(marker in word_lower for marker in ["mbwa", "paka", "ng'ombe"]):
            return "1/2"  # But can migrate to 9/10
        
        # Tools/objects typically 7/8 or 9/10
        if any(marker in word_lower for marker in ["kisu", "kikombe", "kiti"]):
            return "7/8"
        
        return None

    def _explain_migration(self, canonical: str, current: str, semantic_func: SemanticFunction) -> str:
        """Explain why ngeli migration occurred"""
        if semantic_func == SemanticFunction.UKUZAJI:
            return f"Moved from {canonical} to {current} for augmentative effect (size, fear, respect)"
        elif semantic_func == SemanticFunction.UDOGOSHAJI:
            return f"Moved from {canonical} to {current} for diminutive effect (smallness, endearment)"
        elif semantic_func == SemanticFunction.DHARAU:
            return f"Moved from {canonical} to {current} to express contempt or bad behavior"
        elif semantic_func == SemanticFunction.SIFA_NZURI:
            return f"Moved from {canonical} to {current} to express positive qualities"
        else:
            return f"Dialectal variation: {canonical} -> {current}"

class EnhancedKiswahiliGrammarEngine:
    """Enhanced Ki-Micheweni grammar engine with full ngeli support"""
    
    def __init__(self):
        self.ngeli_system = EnhancedNgeliSystem()
    
    def analyze_sentence_enhanced(self, sentence: str) -> Dict[str, Any]:
        """Enhanced sentence analysis with full ngeli awareness"""
        # Clean sentence
        sentence = re.sub(r'\s+', ' ', sentence.strip())
        if not sentence:
            return {"error": "Empty sentence"}
        
        # Tokenize
        words = [w for w in re.findall(r'\b\w+\b', sentence) if w]
        if not words:
            return {"error": "No valid words found"}
        
        # Enhanced analysis
        result = {
            "original": sentence,
            "words": words,
            "sentence_type": self._classify_sentence_type_enhanced(sentence, words),
            "structure": self._analyze_sentence_structure_enhanced(sentence, words),
            "tokens": [],
            "agreement": {},
            "ngeli_migrations": [],
            "semantic_analysis": {},
            "explanation": ""
        }
        
        # Analyze each token with enhanced context
        for i, word in enumerate(words):
            context = {
                "sentence": sentence,
                "position": i,
                "neighboring_words": words[max(0, i-1):i+2]
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
        result["agreement"] = self._check_sentence_agreement_enhanced(result["tokens"])
        
        # Semantic analysis summary
        result["semantic_analysis"] = self._generate_semantic_summary(result["tokens"])
        
        # Generate comprehensive explanation
        result["explanation"] = self._generate_enhanced_explanation(result)
        
        return result

    def _classify_sentence_type_enhanced(self, sentence: str, words: List[str]) -> str:
        """Enhanced sentence type classification"""
        # Basic punctuation check
        if sentence.endswith("?"):
            return "Ulizi (Question)"
        if sentence.endswith("!"):
            return "Amri (Command)"
        
        # Enhanced conditional detection
        conditional_patterns = [
            (["kama", "ikiwa"], ["basi", "ndipo"], "Changamani (Conditional)"),
            (["ingawa", "ijapokuwa"], [], "Changamani (Concessive)"),
            (["hata"], ["bado"], "Changamani (Even if)")
        ]
        
        for initial_words, final_words, sentence_type in conditional_patterns:
            if any(word in words for word in initial_words):
                if not final_words or any(word in words for word in final_words):
                    return sentence_type
        
        # Enhanced conjunction detection
        conjunctions = {
            "na": "Ambatano (Conjunctive)",
            "lakini": "Ambatano (Adversative)", 
            "wala": "Ambatano (Negative)",
            "au": "Ambatano (Disjunctive)",
            "kisha": "Ambatano (Sequential)",
            "tena": "Ambatano (Additive)"
        }
        
        for conjunction, sentence_type in conjunctions.items():
            if conjunction in words:
                return sentence_type
        
        return "Sahili (Statement)"

    def _analyze_sentence_structure_enhanced(self, sentence: str, words: List[str]) -> Dict[str, Any]:
        """Enhanced sentence structure analysis"""
        structure = {
            "kiima": [],
            "kiarifu": [],
            "explanation": [],
            "verb_positions": [],
            "complex_predicates": []
        }
        
        # Find all verbs with enhanced detection
        verb_indices = []
        for i, word in enumerate(words):
            verb_analysis = self.ngeli_system.analyze_verb_structure_enhanced(word)
            if verb_analysis["tense"] or any(marker in word.lower() for marker in ["-na-", "-me-", "-ta-", "-li-"]):
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
                structure["complex_predicates"] = [
                    {"main_verb": words[verb_indices[0]], "auxiliary_verbs": [words[i] for i in verb_indices[1:]]}
                ]
        else:
            # Default fallback
            structure["kiima"] = [words[0]] if words else []
            structure["kiarifu"] = words[1:] if len(words) > 1 else []
        
        structure["explanation"].append(
            f"Kiima: {' '.join(structure['kiima'])} | Kiarifu: {' '.join(structure['kiarifu'])}"
        )
        
        return structure

    def _analyze_token_enhanced(self, word: str, context: Dict, structure: Dict) -> Dict[str, Any]:
        """Enhanced token analysis with full contextual information"""
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
            
            # Determine syntactic role based on position and ngeli
            if token["in_kiima"]:
                token["syntactic_role"] = "kiima (subject)"
                token["explanation"].append(
                    f"Subject: '{word}' (ngeli {ngeli_info.ngeli_class}, {ngeli_info.number})"
                )
            else:
                token["syntactic_role"] = "nomino"
                token["explanation"].append(
                    f"Noun: '{word}' (ngeli {ngeli_info.ngeli_class}, {ngeli_info.number})"
                )
        
        # Enhanced verb analysis
        if token["in_kiarifu"]:
            verb_analysis = self.ngeli_system.analyze_verb_structure_enhanced(word, context)
            if verb_analysis["tense"]:
                token["verb_analysis"] = verb_analysis
                token["syntactic_role"] = "kitenzi (verb)"
                token["explanation"].append(
                    f"Verb: '{word}' ({verb_analysis['tense']} tense)"
                )
        
        # Default role assignment
        if not token["syntactic_role"]:
            token["syntactic_role"] = "nomino (default)"
        
        return token

    def _check_sentence_agreement_enhanced(self, tokens: List[Dict]) -> Dict[str, Any]:
        """Enhanced agreement checking across the sentence"""
        result = {
            "subject_verb_agreement": True,
            "noun_adjective_agreement": True,
            "overall_coherence": True,
            "issues": [],
            "detailed_analysis": [],
            "ngeli_consistency": {}
        }
        
        # Find subject and main verb
        subject_token = next((t for t in tokens if t["in_kiima"] and t["ngeli_analysis"]), None)
        verb_token = next((t for t in tokens if t["in_kiarifu"] and t["verb_analysis"]), None)
        
        if subject_token and verb_token:
            # Check subject-verb agreement using enhanced system
            agreement_check = self.ngeli_system.check_enhanced_agreement(
                subject_token["word"], 
                verb_token["word"], 
                context={"sentence": " ".join([t["word"] for t in tokens])}
            )
            
            result["subject_verb_agreement"] = agreement_check["verb_agreement"]
            result["detailed_analysis"].extend(agreement_check["explanation"])
            
            if not agreement_check["verb_agreement"]:
                result["issues"].append("Subject-verb agreement violation")
        
        # Check for ngeli consistency across sentence
        ngeli_usage = {}
        for token in tokens:
            if token["ngeli_analysis"]:
                ngeli = token["ngeli_analysis"]["ngeli"]
                if ngeli not in ngeli_usage:
                    ngeli_usage[ngeli] = []
                ngeli_usage[ngeli].append(token["word"])
        
        result["ngeli_consistency"] = ngeli_usage
        
        # Overall coherence assessment
        if result["issues"]:
            result["overall_coherence"] = False
        
        return result

    def _generate_semantic_summary(self, tokens: List[Dict]) -> Dict[str, Any]:
        """Generate semantic analysis summary"""
        semantic_functions = {}
        ngeli_distribution = {}
        
        for token in tokens:
            if token["semantic_function"]:
                func = token["semantic_function"]
                if func not in semantic_functions:
                    semantic_functions[func] = []
                semantic_functions[func].append(token["word"])
            
            if token["ngeli_analysis"]:
                ngeli = token["ngeli_analysis"]["ngeli"]
                if ngeli not in ngeli_distribution:
                    ngeli_distribution[ngeli] = 0
                ngeli_distribution[ngeli] += 1
        
        return {
            "semantic_functions": semantic_functions,
            "ngeli_distribution": ngeli_distribution,
            "complexity_score": len(ngeli_distribution)
        }

    def _generate_enhanced_explanation(self, analysis: Dict) -> str:
        """Generate comprehensive explanation of the analysis"""
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
            explanation += "\n"
        
        # Agreement analysis
        explanation += "Agreement Analysis:\n"
        explanation += "-" * 20 + "\n"
        if analysis["agreement"]["issues"]:
            explanation += "⚠️ Issues detected:\n"
            for issue in analysis["agreement"]["issues"]:
                explanation += f"  • {issue}\n"
        else:
            explanation += "✅ All elements show proper agreement\n"
        
        for detail in analysis["agreement"]["detailed_analysis"]:
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
                if func != "neutral":
                    explanation += f"• {func}: {', '.join(words)}\n"
        
        explanation += f"\nNgeli Distribution: {sem['ngeli_distribution']}\n"
        explanation += f"Complexity Score: {sem['complexity_score']}/18 ngeli classes used\n"
        
        return explanation

# Example usage and testing
if __name__ == "__main__":
    engine = EnhancedKiswahiliGrammarEngine()
    
    # Test sentences from the PDF
    test_sentences = [
        "Mwalimu analima shambani kesho.",  # Standard 1/2
        "Joka limmiza kyura.",  # Ukuzaji example from PDF
        "Kipaka kile kinlala.",  # Udogoshaji example
        "Kizee kile kinaiba kuku.",  # Dharau example
        "Macho yamejaa maji.",  # 5/6 example
        "Ng'ombe in'chinjwa.",  # Migration example (1/2 -> 9/10)
    ]
    
    print("=" * 80)
    print("KI-MICHEWENI ENHANCED GRAMMAR ENGINE - COMPREHENSIVE ANALYSIS")
    print("=" * 80)
    
    for sentence in test_sentences:
        print(f"\n🔍 Analyzing: {sentence}")
        print("-" * 60)
        
        analysis = engine.analyze_sentence_enhanced(sentence)
        print(analysis["explanation"])
        print("=" * 80)