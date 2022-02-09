import unicodedata

"""
    Utilities for dealing with unicode strings
"""


def ascii(x):
    """ Replaces all diacretics with their ascii counterpart. """
    if x is None:
        return
        
    x = x.translate(str.maketrans("øØðÐ", "oOdD"))
    return ''.join(c for c in unicodedata.normalize('NFD', x)
                  if unicodedata.category(c) != 'Mn')

transtable = str.maketrans({
    "æ": "ae",
    "Æ": "Ae",
    "œ": "oe",
    "Œ": "Oe",
    "Ĳ": "Ij",
    "ĳ": "ij",
    "ǈ": "Lj",
    "ǉ": "lj",
    "ȸ": "db",
    "ȹ": "qp",
    "ß": "ss",
    "ﬆ": "st",
    "ﬅ": "ft",
    "ﬀ": "ff",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "ﬃ": "ffi",
    "ﬄ": "ffl"
})

def decompose(x):
    """ Replaces all digraphs and ligatures with their underlying 2 latin letters. """
    if x is None:
        return
    return x.translate(transtable)
    
