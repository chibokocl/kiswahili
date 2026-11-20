"""
Enhanced ngeli system implementation for Ki-Micheweni dialect.

This module implements the comprehensive 18-ngeli system with semantic functions,
phonological rules, and migration detection as documented in the research by
Hamad Khamis Juma (2015).
"""

from typing import Dict, List, Optional, Tuple, Any
import re

from .types import NgeliInfo, SemanticFunction
from .phonology import PhonologicalRules, MorphemeSegmenter
from .verb_morphology import VerbParser, VERB_THRESHOLD
from .noun_lexicon import NounLexicon
from ..data.ngeli_data import NGELI_CLASSES, TENSE_MARKERS
from ..data.semantic_domains import (
    SEMANTIC_DOMAINS, SEMANTIC_CONTEXT_PATTERNS, COMMON_MIGRATIONS,
    DIMINUTIVE_TRIGGERS, AUGMENTATIVE_TRIGGERS, CONTEMPT_TRIGGERS,
    POSITIVE_TRIGGERS, HUMOR_TRIGGERS, HATRED_TRIGGERS
)


class EnhancedNgeliSystem:
    """
    Enhanced Ki-Micheweni noun class system with full 18-ngeli support.
    
    Features:
    - All 18 ngeli classes from Ki-Micheweni research
    - Phonological rule application (nasal mutation, vowel coalescence)
    - Semantic function detection (ukuzaji, udogoshaji, dharau, etc.)
    - Ngeli migration detection and explanation
    - Context-aware analysis
    """
    
    def __init__(self, verb_parser: Optional[VerbParser] = None,
                 noun_lexicon: Optional[NounLexicon] = None, use_noun_lexicon: bool = True):
        """
        Args:
            verb_parser: Verb parser (default: ``VerbParser.from_kamusi()``).
            noun_lexicon: Noun lexicon; defaults to the packaged dictionary-derived one.
            use_noun_lexicon: ``False`` forces prefix heuristics only (useful for baselines).
        """
        self.verb_parser = verb_parser or VerbParser.from_kamusi()
        self.noun_lexicon = (noun_lexicon or NounLexicon.load()) if use_noun_lexicon else None
        self.ngeli_classes = NGELI_CLASSES
        self.tense_markers = TENSE_MARKERS
        self.phonological_rules = PhonologicalRules()
        self.segmenter = MorphemeSegmenter()
        
        # Build reverse mapping for prefix identification
        self.prefix_to_ngeli = self._build_prefix_mapping()
        
        # Compile semantic patterns for efficiency
        self._compile_semantic_patterns()
    
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
    
    def _compile_semantic_patterns(self):
        """Compile regex patterns for semantic function detection"""
        self.compiled_patterns = {}
        for func, data in SEMANTIC_CONTEXT_PATTERNS.items():
            compiled_patterns = []
            for pattern in data["patterns"]:
                compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
            self.compiled_patterns[func] = compiled_patterns
    
    def identify_ngeli_enhanced(self, word: str, context: Dict = None) -> Optional[NgeliInfo]:
        """
        Enhanced ngeli identification with semantic and phonological analysis.
        
        Args:
            word: The word to analyze
            context: Optional context including sentence, position, etc.
            
        Returns:
            NgeliInfo object with complete analysis or None if unidentifiable
        """
        word = word.lower().strip()
        context = context or {}

        # Dictionary lookup beats prefix heuristics (mtoto is 1/2, chakula is 7/8)
        lexical = self._identify_from_lexicon(word, context)
        if lexical:
            return lexical

        candidates = []
        
        # Try morphological analysis for each ngeli class
        for ngeli, data in self.ngeli_classes.items():
            # Collect all possible prefixes for this ngeli
            all_prefixes = []
            all_prefixes.extend(data.get("singular_prefixes", []))
            all_prefixes.extend(data.get("plural_prefixes", []))
            
            # Try morpheme segmentation
            segmentation = self.segmenter.segment_word(word, all_prefixes)
            if segmentation:
                prefix, root, processes = segmentation
                
                # Determine number based on prefix
                number = self._determine_number(prefix, ngeli, data)
                confidence = self._calculate_confidence(word, prefix, root, processes, data)
                
                morphological_analysis = {
                    "prefix": prefix,
                    "root": root,
                    "phonological_changes": processes,
                    "segmentation_method": "morphological"
                }
                
                candidates.append((ngeli, number, confidence, morphological_analysis))
        
        # Also try semantic domain matching for words without clear morphology
        semantic_candidates = self._identify_by_semantic_domain(word, context)
        candidates.extend(semantic_candidates)
        
        if not candidates:
            return None
        
        # Sort by confidence and select best
        candidates.sort(key=lambda x: x[2], reverse=True)
        best_ngeli, best_number, best_confidence, best_analysis = candidates[0]
        
        # Determine semantic function
        semantic_func = self._determine_semantic_function(word, best_ngeli, context)
        
        return NgeliInfo(
            ngeli_class=best_ngeli,
            number=best_number,
            semantic_function=semantic_func,
            confidence=best_confidence,
            morphological_analysis=best_analysis
        )
    
    def _identify_from_lexicon(self, word: str, context: Dict) -> Optional[NgeliInfo]:
        if not self.noun_lexicon:
            return None
        entries = self.noun_lexicon.lookup(word)
        if not entries:
            return None
        best = entries[0]
        return NgeliInfo(
            ngeli_class=best.ngeli,
            number=best.number,
            semantic_function=self._determine_semantic_function(word, best.ngeli, context),
            confidence=best.confidence,
            morphological_analysis={
                "segmentation_method": "lexicon",
                "lemma": best.lemma,
                "source": best.source,
                "alternatives": [
                    {"ngeli": e.ngeli, "number": e.number, "lemma": e.lemma, "source": e.source}
                    for e in entries[1:]
                ],
            },
        )

    def _determine_number(self, prefix: str, ngeli: str, ngeli_data: Dict) -> str:
        """Determine if prefix indicates singular or plural"""
        if prefix in [p.rstrip('-') for p in ngeli_data.get("singular_prefixes", [])]:
            return "singular"
        elif prefix in [p.rstrip('-') for p in ngeli_data.get("plural_prefixes", [])]:
            return "plural"
        else:
            # Default to singular for ambiguous cases
            return "singular"
    
    def _calculate_confidence(self, word: str, prefix: str, root: str, 
                            processes: List[str], ngeli_data: Dict) -> float:
        """Calculate confidence score for ngeli assignment"""
        confidence = 0.5  # Base confidence
        
        # Boost for longer roots (more substantial words)
        if len(root) >= 3:
            confidence += 0.2
        elif len(root) >= 2:
            confidence += 0.1
        
        # Boost for matching known examples
        examples = ngeli_data.get("examples", [])
        if word in examples:
            confidence += 0.3
        elif any(example in word or word in example for example in examples):
            confidence += 0.1
        
        # Slight penalty for complex phonological processes
        confidence -= len(processes) * 0.05
        
        # Boost for zero prefix in appropriate ngeli classes
        if prefix == "Ø" and "Ø-" in ngeli_data.get("singular_prefixes", []):
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _identify_by_semantic_domain(self, word: str, context: Dict) -> List[Tuple[str, str, float, Dict]]:
        """Identify ngeli by semantic domain matching"""
        candidates = []
        
        for domain, domain_data in SEMANTIC_DOMAINS.items():
            # Check keywords
            if any(keyword in word for keyword in domain_data["keywords"]):
                for canonical_ngeli in domain_data["canonical_ngeli"]:
                    morphological_analysis = {
                        "prefix": "semantic",
                        "root": word,
                        "phonological_changes": [],
                        "segmentation_method": "semantic_domain",
                        "domain": domain
                    }
                    candidates.append((canonical_ngeli, "singular", 0.6, morphological_analysis))
        
        return candidates
    
    def _determine_semantic_function(self, word: str, ngeli: str, context: Dict) -> SemanticFunction:
        """Determine semantic function based on context and patterns"""
        
        # Check for explicit semantic function in context
        if "semantic_function" in context:
            return SemanticFunction(context["semantic_function"])
        
        sentence = context.get("sentence", "").lower()
        
        # Check compiled patterns
        for func_name, patterns in self.compiled_patterns.items():
            if any(pattern.search(sentence) for pattern in patterns):
                target_ngeli = SEMANTIC_CONTEXT_PATTERNS[func_name]["target_ngeli"]
                if ngeli in target_ngeli:
                    return SemanticFunction(func_name)
        
        # Check trigger words in sentence
        if any(trigger in sentence for trigger in DIMINUTIVE_TRIGGERS) and ngeli == "7/8":
            return SemanticFunction.UDOGOSHAJI
        
        if any(trigger in sentence for trigger in AUGMENTATIVE_TRIGGERS) and ngeli in ["5/6", "5/4"]:
            return SemanticFunction.UKUZAJI
        
        if any(trigger in sentence for trigger in CONTEMPT_TRIGGERS) and ngeli == "7/8":
            return SemanticFunction.DHARAU
        
        if any(trigger in sentence for trigger in POSITIVE_TRIGGERS):
            return SemanticFunction.SIFA_NZURI
        
        if any(trigger in sentence for trigger in HUMOR_TRIGGERS):
            return SemanticFunction.MZAHA
        
        if any(trigger in sentence for trigger in HATRED_TRIGGERS):
            return SemanticFunction.CHUKI
        
        return SemanticFunction.NEUTRAL
    
    def get_agreement_prefix(self, ngeli: str, number: str, role: str) -> Optional[str]:
        """
        Get agreement prefix for KK, KY, KV roles.
        
        Args:
            ngeli: The ngeli class (e.g., "1/2")
            number: "singular" or "plural"
            role: "kk" (kiwakilishi kitenzi), "ky" (kiwakilishi nomino), "kv" (kivumishi)
            
        Returns:
            Agreement prefix string or None if not found
        """
        if ngeli not in self.ngeli_classes:
            return None
        
        ngeli_data = self.ngeli_classes[ngeli]
        if role not in ngeli_data:
            return None
            
        return ngeli_data[role].get(number)
    
    def check_enhanced_agreement(self, subject: str, verb: str, adjective: Optional[str] = None, 
                                context: Dict = None) -> Dict[str, Any]:
        """
        Enhanced agreement checking with semantic analysis.
        
        Args:
            subject: Subject noun
            verb: Main verb
            adjective: Optional adjective
            context: Additional context
            
        Returns:
            Comprehensive agreement analysis
        """
        context = context or {}
        result = {
            "subject_analysis": None,
            "verb_agreement": False,
            "adjective_agreement": False if adjective else None,
            "semantic_analysis": {},
            "special_cases": [],
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

        # Check for special agreement cases (e.g., disability terms)
        special_agreement_ngeli = self._check_special_agreement(subject, ngeli)
        agreement_ngeli = special_agreement_ngeli or ngeli

        if special_agreement_ngeli:
            result["special_cases"].append(
                f"Using {special_agreement_ngeli} agreement for {ngeli} morphology"
            )

        # Parse the verb independently of the subject, then compare its subject
        # marker with the classes the subject can control.
        verb_analysis = self.analyze_verb_structure_enhanced(
            verb, {"subject_ngeli": agreement_ngeli, "subject_number": number}
        )
        verb_sm = verb_analysis["structure"]["subject_prefix"]
        candidates = [tuple(c) for c in verb_analysis["subject_candidates"]]

        # A noun can have several lexicon readings (mtoto: 1/2 child, 3/4 shoot);
        # if the primary reading disagrees but another one agrees, use that one.
        if verb_sm and (agreement_ngeli, number) not in candidates and self.noun_lexicon:
            for alt_ngeli, alt_number in self.noun_lexicon.candidates(subject):
                if (alt_ngeli, alt_number) in candidates:
                    agreement_ngeli, ngeli, number = alt_ngeli, alt_ngeli, alt_number
                    result["special_cases"].append(
                        f"Subject '{subject}' read as ngeli {alt_ngeli} ({alt_number}) "
                        f"to match the verb"
                    )
                    break
        expected_kk = self.get_agreement_prefix(agreement_ngeli, number, "kk")

        if verb_sm and (agreement_ngeli, number) in candidates:
            result["verb_agreement"] = True
            result["explanation"].append(
                f"✓ Verb '{verb}' agrees with subject '{subject}' (ngeli {ngeli}, {number})"
            )
        else:
            result["explanation"].append(
                f"✗ Verb '{verb}' disagrees with subject '{subject}' - "
                f"expected {expected_kk or '?'}, got {verb_sm or 'none'}"
            )

        # Check adjective agreement
        if adjective:
            expected_kv = self.get_agreement_prefix(agreement_ngeli, number, "kv")
            if expected_kv:
                if adjective.startswith(expected_kv.rstrip('-')):
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
            "morphological_details": subject_info.morphological_analysis,
            "migration_detected": subject_info.is_migrated()
        }
        
        return result
    
    def _check_special_agreement(self, word: str, ngeli: str) -> Optional[str]:
        """Check for special agreement patterns (e.g., disability terms using human agreement)"""
        
        # Disability terms in 7/8 use 1/2 agreement
        if ngeli == "7/8":
            disability_markers = ["pofu", "bubu", "ziwi", "lema", "chaa"]
            if any(marker in word.lower() for marker in disability_markers):
                return "1/2"
        
        return None
    
    def analyze_verb_structure_enhanced(self, verb: str, context: Dict = None) -> Dict[str, Any]:
        """
        Analyze verb morphology with :class:`VerbParser`.

        Args:
            verb: The verb to analyze
            context: Optional ``subject_ngeli`` / ``subject_number`` used to prefer
                an analysis whose subject marker agrees with the subject.

        Returns:
            Dict with ``structure`` (subject_prefix, tense_marker, object_prefix,
            root, extensions, final_vowel, ...), ``tense``, ``subject_candidates``
            (ngeli/number pairs the subject marker allows) and ranked ``alternatives``.
            Low-confidence parses (bare imperatives, noun-like words) yield no tense.
        """
        context = context or {}
        analysis = {
            "word": verb,
            "structure": {
                "subject_prefix": None, "object_prefix": None, "tense_marker": None,
                "root": None, "extensions": [], "final_vowel": None,
                "polarity": None, "relative_marker": None,
            },
            "ngeli": None, "number": None, "tense": None,
            "form": None, "confidence": 0.0,
            "subject_candidates": [], "alternatives": [], "explanation": [],
        }

        subject = None
        if context.get("subject_ngeli") and context.get("subject_number"):
            subject = (context["subject_ngeli"], context["subject_number"])

        parse = self.verb_parser.best(verb, subject)
        if parse is None or parse.score < VERB_THRESHOLD:
            analysis["explanation"].append("No confident verb analysis")
            return analysis

        st = analysis["structure"]
        st["subject_prefix"] = parse.negative_prefix or parse.subject_marker
        st["tense_marker"] = parse.tam
        st["object_prefix"] = parse.object_marker
        st["root"] = parse.root
        st["extensions"] = [surface for _, surface in parse.extensions]
        st["extension_labels"] = [label for label, _ in parse.extensions]
        st["final_vowel"] = parse.final_vowel or None
        st["polarity"] = parse.polarity
        st["relative_marker"] = parse.relative or parse.relative_suffix

        analysis["tense"] = parse.tam_name
        analysis["form"] = parse.form
        analysis["confidence"] = round(parse.score, 3)
        analysis["subject_candidates"] = [list(c) for c in parse.subject_ngeli()]
        if subject and subject in parse.subject_ngeli():
            analysis["ngeli"], analysis["number"] = subject
        analysis["alternatives"] = [
            {"segmentation": p.segmentation(), "form": p.form, "score": round(p.score, 3)}
            for p in self.verb_parser.parse(verb)[1:4] if p.score >= VERB_THRESHOLD
        ]
        gloss = " ".join(f"{s}({g})" for s, g in parse.morphemes())
        analysis["explanation"].append(f"Verb structure: {parse.segmentation()}  [{gloss}]")
        return analysis

    def detect_ngeli_migration(self, word: str, context: Dict = None) -> Dict[str, Any]:
        """
        Detect if word has migrated from its canonical ngeli class.
        
        Args:
            word: Word to analyze
            context: Optional context
            
        Returns:
            Migration analysis results
        """
        context = context or {}
        
        # Check for known common migrations first
        if word in COMMON_MIGRATIONS:
            migration_data = COMMON_MIGRATIONS[word]
            return {
                "migration_detected": True,
                "canonical_ngeli": migration_data["from"],
                "current_ngeli": migration_data["to"],
                "reason": migration_data["reason"],
                "confidence": 0.9
            }
        
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
                "reason": self._explain_migration(canonical_ngeli, current_ngeli, current_analysis.semantic_function),
                "confidence": current_analysis.confidence
            }
        
        return {
            "migration_detected": False, 
            "canonical_ngeli": canonical_ngeli,
            "current_ngeli": current_ngeli
        }
    
    def _get_canonical_ngeli(self, word: str) -> Optional[str]:
        """Determine canonical ngeli class based on semantic content"""
        word_lower = word.lower()
        
        # Check semantic domains
        for domain, domain_data in SEMANTIC_DOMAINS.items():
            # Check keywords
            if any(keyword in word_lower for keyword in domain_data["keywords"]):
                return domain_data["canonical_ngeli"][0]  # Return first canonical option
            
            # Check patterns
            for pattern in domain_data.get("patterns", []):
                if pattern.lower() in word_lower or word_lower in pattern.lower():
                    return domain_data["canonical_ngeli"][0]
        
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
        elif semantic_func == SemanticFunction.MZAHA:
            return f"Moved from {canonical} to {current} for humorous effect"
        elif semantic_func == SemanticFunction.CHUKI:
            return f"Moved from {canonical} to {current} to express hatred or disgust"
        else:
            return f"Dialectal variation: {canonical} -> {current}"