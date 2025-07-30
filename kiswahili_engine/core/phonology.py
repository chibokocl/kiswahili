"""
Phonological rules and processes for Ki-Micheweni morphology.

Implements the sound changes and morphophonological processes documented
in the Ki-Micheweni dialect research.
"""

from typing import Tuple, List, Optional
import re


class PhonologicalRules:
    """
    Handles phonological processes in Ki-Micheweni morphology.
    
    Based on the morphophonological patterns documented in:
    "Ngeli za Nomino za Ki-Micheweni" by Hamad Khamis Juma (2015)
    """
    
    # Consonant clusters that trigger nasal mutation
    NASAL_MUTATION_TRIGGERS = {
        't', 'd', 'c', 'j', 'k', 'g', 's', 'z', 'l', 'r', 'n', 'm', 'y', 'w'
    }
    
    # Consonants that block nasal mutation (bilabials and labiodentals)
    NASAL_MUTATION_BLOCKERS = {'p', 'b', 'f', 'v'}
    
    @staticmethod
    def apply_nasal_mutation(prefix: str, root: str) -> str:
        """
        Apply nasal mutation rules: m- -> n- before certain consonants.
        
        Rule: The bilabial nasal /m/ becomes the alveolar nasal /n/ 
        except before bilabial and labiodental consonants (p, b, f, v).
        
        Args:
            prefix: The morphological prefix
            root: The root to which the prefix attaches
            
        Returns:
            The prefix with nasal mutation applied if appropriate
            
        Examples:
            apply_nasal_mutation("m", "tu") -> "n"  (mtu -> ntu)
            apply_nasal_mutation("m", "papa") -> "m"  (mpapa stays mpapa)
        """
        if not root or not prefix.startswith('m'):
            return prefix
            
        first_consonant = root[0].lower()
        
        # Apply mutation unless blocked by bilabials/labiodentals
        if first_consonant not in PhonologicalRules.NASAL_MUTATION_BLOCKERS:
            return prefix.replace('m', 'n', 1)
        
        return prefix
    
    @staticmethod
    def handle_vowel_coalescence(prefix: str, root: str) -> Tuple[str, str]:
        """
        Handle vowel coalescence when prefix ends with vowel and root starts with vowel.
        
        Common patterns:
        - mu- + embe -> mwembe (u + e -> we)
        - ki- + atu -> kyatu (i + a -> ya, simplified to ky-)
        
        Args:
            prefix: The morphological prefix
            root: The root morpheme
            
        Returns:
            Tuple of (modified_prefix, modified_root)
        """
        if not prefix or not root:
            return prefix, root
            
        if prefix.endswith('u') and root.startswith(('a', 'e', 'i', 'o')):
            # mu- + V -> mw- + V
            return prefix[:-1] + 'w', root
        elif prefix.endswith('i') and root.startswith(('a', 'e', 'o', 'u')):
            # ki- + V -> ky- + V (simplified)
            return prefix[:-1] + 'y', root
        elif prefix.endswith('a') and root.startswith(('i', 'u')):
            # Less common, but handle a + high vowel
            return prefix[:-1], root
            
        return prefix, root
    
    @staticmethod
    def apply_consonant_simplification(word: str) -> str:
        """
        Apply consonant cluster simplification rules.
        
        Handles cases like:
        - nk -> k in certain contexts
        - mb -> m in certain contexts
        
        Args:
            word: The complete word form
            
        Returns:
            Word with consonant simplification applied
        """
        # Handle common simplifications
        patterns = [
            (r'^nk([aeiou])', r'k\1'),      # nk- -> k- before vowels
            (r'^nt([aeiou])', r't\1'),      # nt- -> t- before vowels  
            (r'^mp([aeiou])', r'p\1'),      # mp- -> p- before vowels
        ]
        
        result = word
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result)
            
        return result
    
    @staticmethod
    def reconstruct_underlying_form(surface_form: str, prefix: str) -> Tuple[str, str]:
        """
        Attempt to reconstruct the underlying morphological form.
        
        Given a surface form and suspected prefix, try to determine
        the underlying prefix and root before phonological processes.
        
        Args:
            surface_form: The observed word form
            prefix: The suspected prefix
            
        Returns:
            Tuple of (underlying_prefix, underlying_root)
        """
        if not surface_form.startswith(prefix):
            return prefix, surface_form
            
        surface_root = surface_form[len(prefix):]
        
        # Try to reverse vowel coalescence
        if prefix.endswith('w') and len(prefix) > 1:
            # mw- might be from mu- + vowel-initial root
            underlying_prefix = prefix[:-1] + 'u'
            return underlying_prefix, surface_root
        elif prefix.endswith('y') and len(prefix) > 1:
            # ky- might be from ki- + vowel-initial root  
            underlying_prefix = prefix[:-1] + 'i'
            return underlying_prefix, surface_root
        
        # Try to reverse nasal mutation
        if prefix.startswith('n') and surface_root and \
           surface_root[0] not in PhonologicalRules.NASAL_MUTATION_BLOCKERS:
            underlying_prefix = prefix.replace('n', 'm', 1)
            return underlying_prefix, surface_root
            
        return prefix, surface_root
    
    @classmethod
    def analyze_morphophonology(cls, word: str, candidate_prefixes: List[str]) -> List[Tuple[str, str, List[str]]]:
        """
        Comprehensive morphophonological analysis.
        
        Tries different prefix possibilities and returns all viable analyses
        with the phonological processes that would derive the surface form.
        
        Args:
            word: The surface word form
            candidate_prefixes: List of possible prefixes to try
            
        Returns:
            List of (prefix, root, processes) tuples for viable analyses
        """
        analyses = []
        
        for prefix in candidate_prefixes:
            processes = []
            working_prefix = prefix.rstrip('-')
            
            # Direct match
            if word.startswith(working_prefix):
                root = word[len(working_prefix):]
                if len(root) >= 2:  # Ensure substantial root
                    analyses.append((working_prefix, root, []))
                    continue
            
            # Try with nasal mutation
            if working_prefix.startswith('m'):
                mutated = cls.apply_nasal_mutation(working_prefix, word[len(working_prefix):])
                if word.startswith(mutated) and mutated != working_prefix:
                    root = word[len(mutated):]
                    if len(root) >= 2:
                        processes.append(f"nasal_mutation: {working_prefix} -> {mutated}")
                        analyses.append((mutated, root, processes))
                        continue
            
            # Try with vowel coalescence (reverse engineering)
            if len(word) > len(working_prefix):
                # Test if this could be result of coalescence
                if working_prefix.endswith(('w', 'y')):
                    underlying_prefix, root = cls.reconstruct_underlying_form(word, working_prefix)
                    if underlying_prefix != working_prefix:
                        test_coalesced, _ = cls.handle_vowel_coalescence(underlying_prefix, root)
                        if test_coalesced + root == word:
                            processes.append(f"vowel_coalescence: {underlying_prefix} + {root} -> {working_prefix} + {root}")
                            analyses.append((working_prefix, root, processes))
        
        return analyses


class MorphemeSegmenter:
    """
    Handles morpheme segmentation using phonological rules.
    """
    
    def __init__(self):
        self.phonology = PhonologicalRules()
    
    def segment_word(self, word: str, possible_prefixes: List[str]) -> Optional[Tuple[str, str, List[str]]]:
        """
        Segment a word into prefix and root using phonological analysis.
        
        Args:
            word: The word to segment
            possible_prefixes: List of candidate prefixes
            
        Returns:
            Best (prefix, root, processes) tuple or None if no good segmentation
        """
        analyses = self.phonology.analyze_morphophonology(word, possible_prefixes)
        
        if not analyses:
            return None
        
        # Score analyses by root length and process complexity
        def score_analysis(analysis):
            prefix, root, processes = analysis
            root_score = len(root)  # Prefer longer roots
            process_penalty = len(processes) * 0.1  # Slight penalty for complexity
            return root_score - process_penalty
        
        best_analysis = max(analyses, key=score_analysis)
        return best_analysis