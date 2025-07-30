"""
Ngeli class definitions and tense markers for Ki-Micheweni.

Data extracted from "Ngeli za Nomino za Ki-Micheweni" by Hamad Khamis Juma (2015)
"""

# Complete 18-ngeli system based on Ki-Micheweni research
NGELI_CLASSES = {
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

# Tense markers from OFP 008 and Ki-Micheweni research
TENSE_MARKERS = {
    "-na-": "present",
    "-me-": "perfect", 
    "-ta-": "future",
    "-li-": "past_definite",
    "-ki-": "contingent",
    "-se-": "subjunctive",
    "-ka-": "consecutive",
    "-nge-": "conditional",
    "-ngali-": "past_conditional",
    "-japo-": "concessive",
    "-sipo-": "negative_conditional"
}

# Common verb extensions
VERB_EXTENSIONS = {
    "-w-": "passive",
    "-an-": "reciprocal", 
    "-i-": "applied",
    "-ish-": "causative",
    "-iz-": "causative_alt",
    "-uk-": "reversive",
    "-ul-": "reversive_alt"
}

# Final vowel meanings
FINAL_VOWELS = {
    "-a": "indicative",
    "-e": "subjunctive", 
    "-i": "applied/past",
    "-o": "relative",
    "-u": "passive"
}