from enum import Enum, auto


class NamePart(Enum):
    """ Enumeration to indicate a part of a canonical scientific name. """
    
    GENERIC = auto()
    INFRAGENERIC = auto()
    SPECIFIC = auto()
    INFRASPECIFIC = auto()
