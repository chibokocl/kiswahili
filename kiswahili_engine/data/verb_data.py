"""
Verb morphology tables for Standard Kiswahili.

Verb template parsed by ``core/verb_morphology.py``::

    [NEG] SM [NEG2] [TAM] [REL] [OM] ROOT [EXT...] FV [REL-suffix]

All class numbers are Bantu noun-class numbers ("1".."18").  ``CLASS_TO_NGELI``
maps them onto the ngeli keys used in ``ngeli_data.NGELI_CLASSES``.
"""

# ---------------------------------------------------------------- classes
# class number -> [(ngeli key, number), ...]
CLASS_TO_NGELI = {
    "1": [("1/2", "singular"), ("1a/2a", "singular")],
    "2": [("1/2", "plural"), ("1a/2a", "plural")],
    "3": [("3/4", "singular")], "4": [("3/4", "plural")],
    "5": [("5/6", "singular")], "6": [("5/6", "plural"), ("14/6a", "plural")],
    "7": [("7/8", "singular")], "8": [("7/8", "plural")],
    "9": [("9/10", "singular")],
    "10": [("9/10", "plural"), ("11/10a", "plural")],
    "11": [("11/10a", "singular")],
    "12": [("12/13", "singular")], "13": [("12/13", "plural")],
    "14": [("14/6a", "singular")],
    "15": [("15", "singular"), ("15", "plural")],
    "16": [("16", "singular"), ("16", "plural")],
    "17": [("17", "singular"), ("17", "plural")],
    "18": [("18", "singular"), ("18", "plural")],
}

# ---------------------------------------------------------------- subject markers
# Positive subject markers: marker -> list of labels (persons or class numbers)
SUBJECT_MARKERS = {
    "ni": ["1sg"], "u": ["2sg", "3", "11", "14"], "a": ["3sg", "1"],
    "tu": ["1pl", "13"], "m": ["2pl"], "wa": ["3pl", "2"],
    "i": ["4", "9"], "li": ["5"], "ya": ["6"],
    "ki": ["7"], "vi": ["8"], "zi": ["10"],
    "ka": ["12"], "ku": ["15", "17"], "pa": ["16"], "mu": ["18"],
}

# Negative (portmanteau) subject markers: marker -> labels
NEG_SUBJECT_MARKERS = {
    "si": ["1sg"], "hu": ["2sg"], "ha": ["3sg", "1"],
    "hatu": ["1pl", "13"], "ham": ["2pl"], "hawa": ["3pl", "2"],
    "hau": ["3", "11", "14"], "hai": ["4", "9"], "hali": ["5"],
    "haya": ["6"], "haki": ["7"], "havi": ["8"], "hazi": ["10"],
    "haka": ["12"], "haku": ["15", "17"], "hapa": ["16"], "hamu": ["18"],
}

# Person labels (non-class) -> readable description
PERSON_LABELS = {
    "1sg": "1st person singular", "2sg": "2nd person singular",
    "3sg": "3rd person singular", "1pl": "1st person plural",
    "2pl": "2nd person plural", "3pl": "3rd person plural",
}

# ---------------------------------------------------------------- object markers
# marker -> labels.  'mw' is the allomorph of 'm' before a vowel-initial root.
OBJECT_MARKERS = {
    "ni": ["1sg"], "ku": ["2sg"], "m": ["3sg", "1"], "mw": ["3sg", "1"],
    "tu": ["1pl"], "wa": ["3pl", "2", "2pl"],
    "u": ["3", "11", "14"], "i": ["4", "9"], "li": ["5"], "ya": ["6"],
    "ki": ["7"], "vi": ["8"], "zi": ["10"], "ka": ["12"], "pa": ["16"],
    "mu": ["18"], "ji": ["reflexive"],
}

# ---------------------------------------------------------------- TAM
# Affirmative TAM markers: marker -> (name, required final vowel kind)
# FV kinds: "a" indicative, "e" subjunctive
TAM_POSITIVE = {
    "na": ("present", "a"),
    "li": ("past", "a"),
    "me": ("perfect", "a"),
    "ta": ("future", "a"),
    "ka": ("consecutive", "a"),
    "ki": ("conditional/simultaneous", "a"),
    "nge": ("hypothetical", "a"),
    "ngali": ("counterfactual", "a"),
    "japo": ("concessive", "a"),
    "sipo": ("negative conditional", "a"),
    "hu": ("habitual", "a"),      # replaces the subject marker
}

# TAM markers that appear after a negative subject marker
TAM_NEGATIVE = {
    "": ("negative present", "i"),
    "ku": ("negative past", "a"),
    "ta": ("negative future", "a"),
    "ja": ("negative perfect (not yet)", "a"),
    "ki": ("negative conditional", "a"),
}

# TAM allowing a bare 'ku-' before a monosyllabic root (kula -> anakula)
KU_TAMS = {"na", "li", "me", "ta", "ki", "ka", "nge", "ngali", "japo", "sipo", "ku", "ja", "ta", ""}

# ---------------------------------------------------------------- relative markers
# class/person label -> infixed relative marker
RELATIVE_MARKERS = {
    "ye": ["3sg", "1"], "o": ["3pl", "2", "3", "11", "14"],
    "yo": ["4", "6", "9"], "lo": ["5"], "cho": ["7"], "vyo": ["8"],
    "zo": ["10"], "ko": ["15", "17"], "po": ["16"], "mo": ["18"],
}

# ---------------------------------------------------------------- extensions
# Each entry: (label, [(harmony-high form, harmony-mid form)], needs_vowel_final_base)
# 'high' form follows a/i/u in the base, 'mid' form follows e/o.
EXTENSIONS = [
    ("applicative", "i", "e"),
    ("applicative", "li", "le"),     # after vowel-final bases (ingia -> ingilia)
    ("stative", "ik", "ek"),
    ("causative", "ish", "esh"),
    ("causative", "iz", "ez"),
    ("reciprocal", "an", "an"),
    ("passive", "w", "w"),
    ("passive", "iw", "ew"),         # vowel-less (monosyllabic) bases: kula -> kuliwa
]

# ---------------------------------------------------------------- relative suffix (after FV)
# 'asomaye', 'wasomao' : general-present relatives without a TAM marker
RELATIVE_SUFFIXES = {
    "ye": ["3sg", "1"], "o": ["3pl", "2", "3", "11", "14"],
    "yo": ["4", "6", "9"], "lo": ["5"], "cho": ["7"], "vyo": ["8"],
    "zo": ["10"], "ko": ["15", "17"], "po": ["16"], "mo": ["18"],
}
