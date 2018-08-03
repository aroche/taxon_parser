import regex as re
from collections import OrderedDict
from ..api.rank import Rank, NomCode



# Matches all dots ("."), underscores ("_") and dashes ("-").
NORMALIZE_RANK_MARKER = re.compile(r"(?:[._ -]+|\bnotho)")


def buildRankMarkerMap(ranks, additions=None):
    map_ = {}
    for r in ranks:
        map_[r.name.replace(".", "")] = r
    if additions is not None:
        for k, v in additions.items():
            map_[k] = v
    return map_


INFRASUBSPECIFIC_MICROBIAL_RANKS = [r for r in Rank
        if r.isRestrictedToCode() == NomCode.BACTERIAL and r.isInfraspecific()]

# Map of only suprageneric rank markers to their respective rank enum.
RANK_MARKER_MAP_FAMILY_GROUP = buildRankMarkerMap([r for r in Rank if r.isFamilyGroup()])

# Map of only suprageneric rank markers to their respective rank enum.
RANK_MARKER_MAP_SUPRAGENERIC = buildRankMarkerMap([r for r in Rank
    if r.isSuprageneric()], {
      "ib": Rank.SUPRAGENERIC_NAME,
      "supersubtrib": Rank.SUPRAGENERIC_NAME,
      "trib": Rank.TRIBE
      })

# Map of only infrageneric rank markers to their respective rank enum.
RANK_MARKER_MAP_INFRAGENERIC = buildRankMarkerMap([r for r in Rank
    if r.isGenusGroup() and r != Rank.GENUS], {
      "suprasect": Rank.SUPERSECTION,
      "supraser": Rank.SUPERSERIES,
      "sect": Rank.SECTION,
      "section": Rank.SECTION,
      "ser": Rank.SERIES,
      "series": Rank.SERIES,
      "subg": Rank.SUBGENUS,
      "subgen": Rank.SUBGENUS,
      "subgenus": Rank.SUBGENUS,
      "subsect": Rank.SUBSECTION,
      "subsection": Rank.SUBSECTION,
      "subser": Rank.SUBSERIES,
      "subseries": Rank.SUBSERIES
      })



#Map of species rank markers.
RANK_MARKER_MAP_SPECIFIC = {
      "sl": Rank.SPECIES_AGGREGATE, # sensu lat
      "agg": Rank.SPECIES_AGGREGATE,
      "aggr": Rank.SPECIES_AGGREGATE,
      "sp": Rank.SPECIES,
      "spec": Rank.SPECIES,
      "species": Rank.SPECIES,
      "spp": Rank.SPECIES
      }

# Map of only infraspecific rank markers to their respective rank enum.
RANK_MARKER_MAP_INFRASPECIFIC = buildRankMarkerMap([r for r in Rank if r.isInfraspecific()], {
      "aberration": Rank.ABERRATION,
      "bv": Rank.BIOVAR,
      "conv": Rank.CONVARIETY,
      "ct": Rank.CHEMOFORM,
      "cv": Rank.CULTIVAR,
      "f": Rank.FORM,
      "fo": Rank.FORM,
      "form": Rank.FORM,
      "forma": Rank.FORM,
      "fsp": Rank.FORMA_SPECIALIS,
      "fspec": Rank.FORMA_SPECIALIS,
      "gx": Rank.GREX,
      "hort": Rank.CULTIVAR,
      "m": Rank.MORPH,
      "morpha": Rank.MORPH,
      "nat": Rank.NATIO,
      "proles": Rank.PROLES,
      "pv": Rank.PATHOVAR,
      "sf": Rank.SUBFORM,
      "ssp": Rank.SUBSPECIES,
      "st": Rank.STRAIN,
      "subf": Rank.SUBFORM,
      "subform": Rank.SUBFORM,
      "subsp": Rank.SUBSPECIES,
      "subv": Rank.SUBVARIETY,
      "subvar": Rank.SUBVARIETY,
      "sv": Rank.SUBVARIETY,
      "v": Rank.VARIETY,
      "var": Rank.VARIETY,
      "\\*+": Rank.INFRASPECIFIC_NAME
      })

    
def merge_dicts(*dicts):
    """
        Given any number of dicts, shallow copy and merge into a new dict,
        precedence goes to key value pairs in latter dicts.
    """
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


# Map of rank markers to their respective rank enum.
RANK_MARKER_MAP = merge_dicts(buildRankMarkerMap(Rank, {"subser": Rank.SUBSERIES}), \
        RANK_MARKER_MAP_SUPRAGENERIC,
        RANK_MARKER_MAP_INFRAGENERIC,
        RANK_MARKER_MAP_SPECIFIC,
        RANK_MARKER_MAP_INFRASPECIFIC)

# An immutable map of name suffices to corresponding ranks across all kingdoms.
# To minimize wrong matches this map is sorted by suffix length with the first suffices being the longest and
# therefore most accurate matches.
# See http://www.nhm.ac.uk/hosted-sites/iczn/code/index.jsp?nfv=true&article=29
SUFFICES_RANK_MAP = OrderedDict([
          ("mycetidae", Rank.SUBCLASS),
          ("phycidae", Rank.SUBCLASS),
          ("mycotina", Rank.SUBPHYLUM),
          ("phytina", Rank.SUBPHYLUM),
          ("phyceae", Rank.CLASS),
          ("mycetes", Rank.CLASS),
          ("mycota", Rank.PHYLUM),
          ("opsida", Rank.CLASS),
          ("oideae", Rank.SUBFAMILY),
          ("aceae", Rank.FAMILY),
          ("phyta", Rank.PHYLUM),
          ("oidea", Rank.SUPERFAMILY),
          ("ineae", Rank.SUBORDER),
          ("anae", Rank.SUPERORDER),
          ("ales", Rank.ORDER),
          ("acea", Rank.SUPERFAMILY),
          ("idae", Rank.FAMILY),
          ("inae", Rank.SUBFAMILY),
          ("eae", Rank.TRIBE),
          ("ini", Rank.TRIBE),
          ("ina", Rank.SUBTRIBE)
          ])




def inferRankFromMarker(rankMarker):
    """
        Tries its best to infer a rank from a given rank marker such as subsp.
        :return the inferred rank or null
    """
    if rankMarker is not None:
        return RANK_MARKER_MAP.get(NORMALIZE_RANK_MARKER.sub("", rankMarker.lower()))


def inferRankFromParsedName(pn):
    """
        Tries its best to infer a rank from an atomised name by just looking at the name parts ignoring any existing rank on the instance.
        As a final resort for higher monomials the suffices are inspected, but no attempt is made to disambiguate
        the 2 known homonym suffices -idae and -inae, but instead the far more widespread zoological versions are
        interpreted.
        :return the inferred rank or UNRANKED if it cant be found.
    """
   
    # default if we cant find anything else
    rank = Rank.UNRANKED
    # detect rank based on parsed name
    if pn.infraspecificEpithet is not None:
      # some infraspecific name
      rank = Rank.INFRASPECIFIC_NAME
    elif pn.specificEpithet is not None:
      # a species
      rank = Rank.SPECIES
    elif pn.infragenericEpithet is not None:
      # some infrageneric name
      rank = Rank.INFRAGENERIC_NAME
    elif pn.uninomial is not None:
      # a suprageneric name, check suffices
      for suffix, r in SUFFICES_RANK_MAP.items():
        if pn.uninomial.endswith(suffix):
          rank = r
          break
    return rank
