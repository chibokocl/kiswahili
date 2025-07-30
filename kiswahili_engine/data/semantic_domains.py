"""
Semantic domain definitions for ngeli classification and migration detection.
"""

# Semantic domains for automatic ngeli classification
SEMANTIC_DOMAINS = {
    "animals": {
        "keywords": ["mbwa", "paka", "ng'ombe", "nyuki", "joka", "tumbili", "tembo", "simba"],
        "patterns": ["nyani", "ndege", "samaki"],
        "canonical_ngeli": ["1/2", "9/10"],
        "migration_targets": {
            "5/4": "ukuzaji",  # Large/fearsome animals
            "7/8": "udogoshaji"  # Small/cute animals
        }
    },
    
    "people": {
        "keywords": ["mtu", "msichana", "mvulana", "mzee", "mwanamke", "mjinga", "hodari"],
        "patterns": ["m+person", "mw+person"],
        "canonical_ngeli": ["1/2"],
        "migration_targets": {
            "7/8": "udogoshaji, sifa_nzuri, dharau"
        }
    },
    
    "plants": {
        "keywords": ["mti", "ua", "mche", "mmea", "mazao"],
        "patterns": ["tree", "flower", "crop"],
        "canonical_ngeli": ["3/4"],
        "migration_targets": {
            "5/4": "ukuzaji"  # Large trees
        }
    },
    
    "body_parts": {
        "keywords": ["cho", "guu", "kono", "wi", "fuwa", "dole"],
        "patterns": ["jicho", "mguu", "mkono"],
        "canonical_ngeli": ["5/6", "3/4"],
        "migration_targets": {}
    },
    
    "tools": {
        "keywords": ["su", "kombe", "ti", "chombo"],
        "patterns": ["kisu", "kikombe", "kiti"],
        "canonical_ngeli": ["7/8"],
        "migration_targets": {
            "5/4": "ukuzaji"  # Large tools
        }
    },
    
    "foods": {
        "keywords": ["zi", "nama", "chakula", "mboga", "matunda"],
        "patterns": ["ndizi", "nyama"],
        "canonical_ngeli": ["9/10", "5/6"],
        "migration_targets": {}
    },
    
    "locations": {
        "keywords": ["hali", "ni", "le", "mahali", "eneo"],
        "patterns": ["pahali", "mahali", "kwahali"],
        "canonical_ngeli": ["16", "17", "18"],
        "migration_targets": {}
    },
    
    "languages": {
        "keywords": ["swahili", "ngereza", "arabia"],
        "patterns": ["Ki+language"],
        "canonical_ngeli": ["7/8"],
        "migration_targets": {}
    },
    
    "abstract_concepts": {
        "keywords": ["pendo", "amani", "haki", "busara"],
        "patterns": ["u+concept"],
        "canonical_ngeli": ["14/6a", "11/10a"],
        "migration_targets": {}
    },
    
    "disabilities": {
        "keywords": ["pofu", "bubu", "ziwi", "lema", "chaa"],
        "patterns": ["ki+disability"],
        "canonical_ngeli": ["7/8"],
        "special_agreement": "1/2",  # Use human agreement despite 7/8 morphology
        "migration_targets": {}
    }
}

# Diminutive triggers (words that suggest udogoshaji)
DIMINUTIVE_TRIGGERS = [
    "kidogo", "ndogo", "mdogo", "dogo",
    "mchumba", "mzuri", "mrembo", "mtoto"
]

# Augmentative triggers (words that suggest ukuzaji)  
AUGMENTATIVE_TRIGGERS = [
    "kubwa", "mkubwa", "mzito", "mrefu", 
    "mkuu", "ogopa", "hofu", "uwoga"
]

# Contempt/dharau triggers
CONTEMPT_TRIGGERS = [
    "mbaya", "mwizi", "mlevi", "mchafu",
    "mjinga", "mpumbavu", "mkorofi"
]

# Positive qualities triggers
POSITIVE_TRIGGERS = [
    "mzuri", "mrembo", "hodari", "mwema",
    "mwerevu", "mkarimu", "mstahimilivu"
]

# Humor/mzaha triggers
HUMOR_TRIGGERS = [
    "kicheshi", "mchezo", "utani", "mzaha"
]

# Hatred/chuki triggers
HATRED_TRIGGERS = [
    "chuki", "uadui", "wivu", "hasira"
]

# Context patterns for semantic function detection
SEMANTIC_CONTEXT_PATTERNS = {
    "ukuzaji": {
        "patterns": [
            r"\b(kubwa|mkubwa|mzito|mrefu)\b",
            r"\b(ogopa|hofu|uwoga)\b",
            r"\b(mkuu|muhimu|maarufu)\b"
        ],
        "target_ngeli": ["5/4", "5/6"]
    },
    
    "udogoshaji": {
        "patterns": [
            r"\b(kidogo|ndogo|mdogo)\b",
            r"\b(mzuri|mrembo|mtoto)\b",
            r"\b(mchumba|mpenzi)\b"
        ],
        "target_ngeli": ["7/8"]
    },
    
    "dharau": {
        "patterns": [
            r"\b(mbaya|mwizi|mlevi)\b",
            r"\b(mchafu|mjinga|mpumbavu)\b",
            r"\b(mkorofi|mshenzi)\b"
        ],
        "target_ngeli": ["7/8"]
    },
    
    "sifa_nzuri": {
        "patterns": [
            r"\b(mzuri|mrembo|hodari)\b",
            r"\b(mwema|mwerevu|mkarimu)\b",
            r"\b(mstahimilivu|mvumilivu)\b"
        ],
        "target_ngeli": ["7/8"]
    }
}

# Word frequency patterns for common migrations
COMMON_MIGRATIONS = {
    # Animals that commonly migrate to 9/10
    "ng'ombe": {"from": "1/2", "to": "9/10", "reason": "dialectal_variation"},
    "nyuki": {"from": "1/2", "to": "9/10", "reason": "dialectal_variation"},
    
    # People terms that can migrate to 7/8
    "msichana": {"from": "1/2", "to": "7/8", "reason": "endearment"},
    "mvulana": {"from": "1/2", "to": "7/8", "reason": "endearment"},
    "mzee": {"from": "1/2", "to": "7/8", "reason": "respect_or_contempt"},
    
    # Tools that can migrate for size
    "kisu": {"from": "7/8", "to": "5/4", "reason": "large_size"},
    "chombo": {"from": "7/8", "to": "5/4", "reason": "large_size"}
}