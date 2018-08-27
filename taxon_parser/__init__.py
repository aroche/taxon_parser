import regex as re
import html
import os
from pkg_resources import resource_string
from enum import Enum, auto

from .name_parser_api.parsedname import ParsedName, State, NamePart
from .name_parser_api.util import rankutils
from .name_parser_api.rank import Rank, NomCode
from .name_parser_api.authorship import Authorship


def stripToNone(s):
    """ strips and return None if string is empty """
    if s is None:
        return
    s = s.strip()
    if s == '':
        return None
    return s


class UnparsableNameException(Exception):
    def __init__(self, type_, name):
        super().__init__("Unparsable {} name: {}".format(type_, name))
        self.type = type_
        self.name = name


class NameType(Enum):
    """
        A short classification of scientific name strings used in Checklist Bank.
    """

    # A scientific latin name that might contain authorship but is not any of the other name types below (virus, hybrid, cultivar, etc).
    SCIENTIFIC = auto()

    # a virus name
    VIRUS = auto()

    # A hybrid <b>formula</b> (not a hybrid name).
    HYBRID_FORMULA = auto()

    """
        A variation of a scientific name that either adds additional notes or has some shortcomings to be classified as
         regular scientific names. Frequent reasons are:
         - informal addition like "cf."
         - indetermined like "Abies spec."
         - abbreviated genus "A. alba Mill
    """
    INFORMAL = auto()

    """
        Operational Taxonomic Unit.
        An OTU is a pragmatic definition to group individuals by similarity, equivalent to but not necessarily in line
        with classical Linnaean taxonomy or modern Evolutionary taxonomy.

        A OTU usually refers to clusters of organisms, grouped by DNA sequence similarity of a specific taxonomic marker gene.
        In other words, OTUs are pragmatic proxies for "species" at different taxonomic levels.
       
        Sequences can be clustered according to their similarity to one another,
        and operational taxonomic units are defined based on the similarity threshold (usually 97% similarity) set by the researcher.
        Typically, OTU's are based on similar 16S rRNA sequences.
    """
    OTU = auto()

    # A placeholder name like "incertae sedis" or "unknown genus".
    PLACEHOLDER = auto()

    # Surely not a scientific name of any kind.
    NO_NAME = auto()

    def isParsable(self):
        return self == self.SCIENTIFIC or self == self.INFORMAL


class Warnings:
    NULL_EPITHET = "epithet with literal value null"
    UNUSUAL_CHARACTERS = "unusual characters"
    SUBSPECIES_ASSIGNED = "Name was considered species but contains infraspecific epithet"
    LC_MONOMIAL = "lower case monomial match"
    INDETERMINED = "indetermined name missing its terminal epithet"
    HIGHER_RANK_BINOMIAL = "binomial with rank higher than species aggregate"
    QUESTION_MARKS_REMOVED = "question marks removed"
    REPL_ENCLOSING_QUOTE = "removed enclosing quotes"
    MISSING_GENUS = "epithet without genus"
    RANK_MISMATCH = "rank does not fit the parsed name"
    HTML_ENTITIES = "html entities unescaped"
    XML_TAGS = "xml tags removed"


class TaxonParser:
    """
        Core parser class of the name parser that tries to take a clean name into its pieces by using regular expressions.
    
        Fully parse the supplied name also trying to extract authorships, a conceptual sec reference, remarks or notes
        on the nomenclatural status. In some cases the authorship parsing proves impossible and this nameparser will
        return null.
        
        For strings which are no scientific names and scientific names that cannot be expressed by the ParsedName class
        the parser will throw an UnparsableException with a given NameType and the original, unparsed name. This is the
        case for all virus names and proper hybrid formulas, so make sure you catch and process this exception.
    """
    
    class Latin_endings_pattern:
        def __init__(self):
            endings = resource_string(__name__, "resources/latin-endings.txt").decode().split("\n")
            self.pattern = re.compile("(" + "|".join(endings) + ")$")
    

    AUTHORTEAM_DELIMITER = re.compile("[,&]")
    AUTHOR_INITIAL_SWAP = re.compile("^([^,]+) *, *([^,]+)$")
    NORM_EX_HORT = re.compile("\\b(?:hort(?:usa?)?|cv)[. ]ex ", re.I)

    # name parsing
    NAME_LETTERS = "A-ZÏËÖÜÄÉÈČÁÀÆŒ"
    name_letters = "a-zïëöüäåéèčáàæœ"
    AUTHOR_LETTERS = NAME_LETTERS + "\\p{Lu}" # upper case unicode letter, not numerical
    # (\W is alphanum)
    author_letters = name_letters + "\\p{Ll}-?" # lower case unicode letter, not numerical
    # common 3 char or longer name suffices
    AUTHOR_TOKEN_3 = "fil|filius|hort|jun|junior|sen|senior"
    # common name suffices (ms=manuscript, not yet published)
    AUTHOR_TOKEN = (r"(?:\p{Lu}[\p{Lu}\p{Ll}'-]*" 
        + "|" + AUTHOR_TOKEN_3 
        + "|al|f|j|jr|ms|sr|v|v[ao]n|bis|d[aeiou]?|de[nrmls]?|degli|e|l[ae]s?|s|ter|'?t|y" 
        + r")\.?")
    AUTHOR = AUTHOR_TOKEN + "(?:[ '-]?" + AUTHOR_TOKEN + ")*"
    AUTHOR_TEAM = AUTHOR + "(?:[&,;]+" + AUTHOR + ")*"
    AUTHORSHIP = (
        "(?:(" + AUTHOR_TEAM + r") ?\bex[. ])?" 
        + "(" + AUTHOR_TEAM + ")" 
        + r"(?: *: *(Pers\.?|Fr\.?))?"  # 2 well known sanction authors for fungus, see POR-2454
    ) 
    AUTHOR_TEAM_PATTERN = re.compile("^" + AUTHOR_TEAM + "$")
    YEAR = "[12][0-9][0-9][0-9?]"
    YEAR_LOOSE = YEAR + r"[abcdh?]?(?:[/,-][0-9]{1,4})?"

    NOTHO = "notho"
    RANK_MARKER = ("(?:" + NOTHO + ")?(?:(?<!f[ .])sp|"
            + "|".join(rankutils.RANK_MARKER_MAP_INFRASPECIFIC.keys())
            + ")").replace("|hort|", "|hort(?!\\.ex)|") # avoid hort.ex matches

    RANK_MARKER_MICROBIAL = r"(?:bv\.|ct\.|f\.sp\.|" \
           + "|".join(r.name.replace(r"\.", r"\\.")
                for r in rankutils.INFRASUBSPECIFIC_MICROBIAL_RANKS) +  ")"

    UNALLOWED_EPITHET_ENDING = "bacilliform|coliform|coryneform|cytoform|chemoform|biovar|serovar" \
                               + "|genomovar|agamovar|cultivar|genotype|serotype|subtype|ribotype|isolate"
    EPHITHET = ("(?:[0-9]+-?|[a-z]-|[doml]'|(?:van|novae) [a-z])?" 
                + "(?!" + RANK_MARKER + r"\b)"  # avoid matching to rank markers
                + "[" + name_letters + "+-]{1,}(?<! d)[" + name_letters + "]" 
                + r"(?<!(?:\b(?:ex|l[ae]|v[ao]n|" + AUTHOR_TOKEN_3 + ")\\.?|"  # avoid epithets ending with the unallowed endings, e.g. serovar and author suffices like filius
                + UNALLOWED_EPITHET_ENDING + "))(?=\\b)")
    MONOMIAL = "[" + NAME_LETTERS + r"](?:\.|[" + name_letters  \
        + "]+)(?:-[" + NAME_LETTERS + "]?[" + name_letters + "]+)?"
    # a pattern matching typical latin word endings. Helps identify name parts from authors
    LATIN_ENDINGS = Latin_endings_pattern().pattern
    INFRAGENERIC = (r"(?:\(([" + NAME_LETTERS + "][" + name_letters + r"-]+)\)" 
            + "| ((?:" + NOTHO + ")?(?:" 
            + "|".join(rankutils.RANK_MARKER_MAP_INFRAGENERIC.keys())
            + "))[. ]([" + NAME_LETTERS + "][" + name_letters + "-]+)"
        + ")")

    RANK_MARKER_ALL = "(" + NOTHO + ")? *(" \
        + "|".join(rankutils.RANK_MARKER_MAP.keys()) + r")\.?"
    RANK_MARKER_ONLY = re.compile("^" + RANK_MARKER_ALL + "$")

    QUOTES = ('"', '\'', '"', '\'')

    # this is only used to detect whether we have a hybrid formula. If not, all markers are normalised
    HYBRID_MARKER = "×"
    HYBRID_FORMULA_PATTERN = re.compile("[. ]" + HYBRID_MARKER + " ")
    EXTINCT_MARKER = "†"
    EXTINCT_PATTERN = re.compile(EXTINCT_MARKER + r"\s*")

    CULTIVAR = re.compile("(?:([. ])cv[. ])?[\"'] ?((?:[" + NAME_LETTERS + "]?[" + name_letters + "]+[- ]?){1,3}) ?[\"']")
    CULTIVAR_GROUP = re.compile(r"(?<!^)\b[\"']?((?:[" + NAME_LETTERS + "][" + name_letters + r"]{2,}[- ]?){1,3})[\"']? (Group|Hybrids|Sort|[Gg]rex|gx)\b")

    # TODO: replace with more generic manuscript name parsing: https://github.com/gbif/name-parser/issues/8
    INFRASPEC_UPPER = re.compile(r"(?<=forma? )([A-Z])\b")
    STRAIN = re.compile(r"([a-z]\.?) +([A-Z]+[ -]?(?!" + YEAR + ")[0-9]+T?)$")
    # this is only used to detect whether we have a virus name
    IS_VIRUS_PATTERN = re.compile(r"virus(es)?\b|" 
        + r"\b("
          +  "(bacterio|viro)?phage(in|s)?|"
           +  "particles?|" 
            + "prion|" 
            + "replicon|" 
            + "(alpha|beta|circular) ?satellites|" 
            + "[a-z]+satellite|" 
            + "vector|"
            + "viroid|"
            + "ictv$"
        + r")\b", re.I)
    # NPV=Nuclear Polyhedrosis Virus
    # GV=Granulovirus
    IS_VIRUS_PATTERN_CASE_SENSITIVE = re.compile(r"\b(:?[MS]?NP|G)V\b")
    IS_VIRUS_PATTERN_POSTFAIL = re.compile(r"(\b(vector)\b)", re.I)
    # RNA or other gene markers
    IS_GENE = re.compile(r"(RNA|DNA)[0-9]*(?:\b|_)")
    # detect known OTU name formats
    # SH  = SH000003.07FU
    # BIN = BOLD:AAA0003
    OTU_PATTERN = re.compile(r"(BOLD:[0-9A-Z]{7}$|SH[0-9]{6}\.[0-9]{2}FU)", re.I)
    # spots a Candidatus bacterial name
    CANDIDATUS = r"(Candidatus\s|Ca\.)"
    IS_CANDIDATUS_PATTERN = re.compile(CANDIDATUS)
    IS_CANDIDATUS_QUOTE_PATTERN = re.compile("\"" + CANDIDATUS + "(.+)\"", re.I)
    FAMILY_PREFIX = re.compile("^[A-Z][a-z]*(?:aceae|idae) +("
            + "|".join(rankutils.RANK_MARKER_MAP_FAMILY_GROUP.keys())
        + r")\b")
    SUPRA_RANK_PREFIX = re.compile("^(" + "|".join(rankutils.merge_dicts(
            rankutils.RANK_MARKER_MAP_SUPRAGENERIC,
            rankutils.RANK_MARKER_MAP_INFRAGENERIC).keys()) + r")[\. ] *")
    RANK_MARKER_AT_END = re.compile("[ .]"
        + RANK_MARKER_ALL[:RANK_MARKER_ALL.rfind(')')]
        + "|"
        + RANK_MARKER_MICROBIAL[3:]
        + r"[. ]?(?:Ad|Lv)?\.?" # allow for larva/adult life stage indicators: http://dev.gbif.org/issues/browse/POR-3000
        + "$")
    FILIUS_AT_END = re.compile(r"[ .]f\.?$")
    # name normalising
    EXTRACT_SENSU = re.compile(" ?\\b" 
        + "(" 
            + "(?:(?:excl[. ](?:gen|sp|var)|mut.char|p.p)[. ])?" 
            + r"\(?(?:" 
            + "ss?[. ](?:(?:ampl|l|s|str)[. ]|(?:ampl|lat|strict)(?:[uo]|issimo)?)" 
            + "|(?:(?:ss[. ])?auct|emend|fide|non|nec|sec|sensu|according to)[. ].+" 
            + r")\)?" 
        + ")")
    NOV_RANKS = r"((?:[sS]ub)?(?:[fF]am|[gG]en|[sS]s?p(?:ec)?|[vV]ar|[fF](?:orma?)?))"
    NOV_RANK_MARKER = re.compile("(" + NOV_RANKS + ")")
    EXTRACT_NOMSTATUS = re.compile("[;, ]?" 
        + r"\(?" 
        + r"\b(" 
            + "(?:comb|" + NOV_RANKS + r")[. ]nov\b[. ]?(?:ined[. ])?" 
            + "|ined[. ]" 
            + "|nom(?:en)?[. ]" 
            + "(?:utiq(?:ue)?[. ])?" 
            + r"(?:ambig|alter|alt|correct|cons|dubium|dub|herb|illeg|invalid|inval|negatum|neg|novum|nov|nudum|nud|oblitum|obl|praeoccup|prov|prot|transf|superfl|super|rejic|rej)\b[. ]?"
            + r"(?:prop[. ]|proposed\b)?"
        + ")"
        + r"\)?")
    EXTRACT_REMARKS = re.compile(r"\s+(anon\.?)(\s.+)?$")
    COMMA_AFTER_BASYEAR = re.compile("(" + YEAR + r")\s*\)\s*,")
    NORM_APOSTROPHES = re.compile("([\u0060\u00B4\u2018\u2019]+)")
    NORM_QUOTES = re.compile("([\"'`´]+)")
    REPL_GENUS_QUOTE = re.compile("^' *(" + MONOMIAL + ") *'")
    REPL_ENCLOSING_QUOTE = re.compile(r"^[',\s]+|[',\s]+$")
    NORM_UPPERCASE_WORDS = re.compile(r"\b(\p{Lu})(\p{Lu}{2,})\b")
    NORM_LOWERCASE_BINOMIAL = re.compile("^(" + EPHITHET + ") (" + EPHITHET + ")")
    NORM_WHITESPACE = re.compile(r"(?:\\[nr]|\s)+")
    REPL_UNDERSCORE = re.compile("_+")
    NORM_NO_SQUARE_BRACKETS = re.compile(r"\[(.*?)\]")
    NORM_BRACKETS_OPEN = re.compile(r"\s*([{(\[])\s*,?\s*")
    NORM_BRACKETS_CLOSE = re.compile(r"\s*,?\s*([})\]])\s*")
    NORM_BRACKETS_OPEN_STRONG = re.compile(r"( ?[{\[] ?)+")
    NORM_BRACKETS_CLOSE_STRONG = re.compile(r"( ?[}\]] ?)+")
    NORM_AND = re.compile(r"\b *(and|et|und|\+|,&) *\b")
    NORM_SUBGENUS = re.compile("(" + MONOMIAL + ") (" + MONOMIAL + ") (" + EPHITHET+ ")")
    NO_Q_MARKS = re.compile("([" + author_letters + r"])\?+")
    NORM_PUNCTUATIONS = re.compile(r"\s*([.,;:&(){}\[\]-])\s*\1*\s*")
    NORM_YEAR = re.compile(r"[\"'\[]+\s*(" + YEAR_LOOSE + r")\s*[\"'\]]+")
    NORM_IMPRINT_YEAR = re.compile("(" + YEAR_LOOSE + r")\s*"
        + r"([(\[,&]? *(?:not|imprint)? *\"?" + YEAR_LOOSE + r"\"?[)\]]?)")
    # √ó is an utf garbaged version of the hybrid cross found in IPNI. See http://dev.gbif.org/issues/browse/POR-3081
    NORM_HYBRIDS_GENUS = re.compile(r"^\s*(?:[+×xX]|√ó)\s*([" + NAME_LETTERS + "])")
    NORM_HYBRIDS_EPITH = re.compile(r"^\s*(×?" + MONOMIAL + r")\s+(?:×|√ó|[xX]\s)\s*(" + EPHITHET + ")")
    NORM_HYBRIDS_FORM = re.compile(r"\b([×xX]|√ó) ")
    NORM_TF_GENUS = re.compile("^([" + NAME_LETTERS + r"])\(([" + name_letters + r"-]+)\)\.? ")
    REPL_IN_REF = re.compile(r"[, ]?\b(?:in|IN|apud) (" + AUTHOR_TEAM + ")")
    REPL_RANK_PREFIXES = re.compile("^(sub)?(fossil|"
        + "|".join(rankutils.RANK_MARKER_MAP_SUPRAGENERIC.keys()) + r")\.?\s+", re.I)
    MANUSCRIPT_NAMES = re.compile(r"\b(indet|spp?)[. ](?:nov\.)?[A-Z0-9][a-zA-Z0-9-]*(?:\(.+?\))?")
    MANUSCRIPT_SUFFIX = re.compile(r"\bms\\.?$")
    REPL_AFF = re.compile(r"\b(undet|indet|aff|cf)[?.]?\b", re.I)
    NO_LETTERS = re.compile("^[^a-zA-Z]+$")
    REMOVE_PLACEHOLDER_AUTHOR = re.compile(r"\b"
        + r"(?:unknown|unspecified|uncertain|\?)"
        + "[, ] ?(" + YEAR_LOOSE + ")$", re.I
    )
    PLACEHOLDER_GENUS = re.compile(r"^(In|Dummy|Missing|Temp|Unknown|Unplaced|Unspecified) (?=[a-z]+)\b")
    PLACEHOLDER_NAME = "(?:allocation|awaiting|deleted?|dummy|incertae sedis|mixed|not assigned|not stated|place ?holder|temp|tobedeleted|unaccepted|unallocated|unassigned|uncertain|unclassed|unclassified|uncultured|undescribed|undetermined|unknown|unnamed|unplaced|unspecified)"
    REMOVE_PLACEHOLDER_INFRAGENERIC = re.compile(r"\b\( ?" + PLACEHOLDER_NAME + r" ?\) ", re.I)
    PLACEHOLDER = re.compile(r"\b" + PLACEHOLDER_NAME + r"\b", re.I)
    DOUBTFUL = re.compile("^[" + AUTHOR_LETTERS + author_letters + HYBRID_MARKER + r"\":;&*+\s,.()\[\]/'`´0-9-†]+$")
    DOUBTFUL_NULL = re.compile(r"\bnull\b", re.I)
    XML_ENTITY_STRIP = re.compile(r"&\s*([a-z]+)\s*;")
    # matches badly formed amoersands which are important in names / authorships
    AMPERSAND_ENTITY = re.compile("& *amp +")

    XML_TAGS = re.compile("< */? *[a-zA-Z] *>")
    STARTING_EPITHET = re.compile(r"^\s*(" + EPHITHET + r")\b")
    FORM_SPECIALIS = re.compile(r"\bf\. *sp(?:ec)?\b")
    SENSU_LATU = re.compile(r"\bs\.l\.\b")

    # many names still use outdated xxxtype rank marker, e.g. serotype instead of serovar
    TYPE_TO_VAR = re.compile(r"\b(" + "|".join(r.name.lower()[:-2]
        for r in rankutils.INFRASUBSPECIFIC_MICROBIAL_RANKS) \
            + r")type\b")
    POTENTIAL_NAME_PATTERN = re.compile("^×?" + MONOMIAL + r"\b")
    REMOVE_INTER_RANKS = re.compile(r"\b((?:subsp|ssp|var)[ .].+)\b(" + RANK_MARKER + r")\b")
    # allow only short lower case tokens to avoid matching to a real epithet
    SKIP_AUTHORS = r"(?:\b[ \p{Ll}'(-]{0,3}\p{Lu}.*?\b)??";
    NAME_PATTERN = re.compile(
                "^"
                # #1 genus/monomial
                + r"(×?(?:\?|" + MONOMIAL + "))"
                # #2 or #4 subgenus/section with #3 infrageneric rank marker
                + "(?:(?<!ceae)" + INFRAGENERIC + ")?"
                # #5 species
                + r"(?:(?:\b| )(×?" + EPHITHET + ")"
                    + "(?:"
                    # any superfluous intermediate bits before terminal epithets, e.g. species authors
                    + "(?:.*?)"
                    # #6 superfluous subspecies epithet
                    + "( ×?" + EPHITHET + ")?"
                    # #7 infraspecies rank
                    + "[. ]?(" + RANK_MARKER + ")?"
                    # #8 infraspecies epitheton, avoid matching to degli which is part of Italian author names
                    + r"[. ](×?\"?(?!(?:degli|de[rn]?)\b)" + EPHITHET + "\"?)"
                    + ")?"
                + ")?"

                + "(?: "
                # #9 microbial rank
                + "(" + RANK_MARKER_MICROBIAL + ")[ .]"
                # #10 microbial infrasubspecific epithet
                + r"(\S+)"
                + ")?"

                # #11 indet rank marker after epithets
                + "([. ]" + RANK_MARKER + ")?"

                # #12 entire authorship incl basionyms and year
                + "([., ]?"
                + r"(?:\("
                    # #13/14/15 basionym authorship (ex/auth/sanct)
                    + "(?:" + AUTHORSHIP + ")?"
                    # #16 basionym year
                    + "[, ]?(" + YEAR_LOOSE + ")?"
                + r"\))?"

                # #17/18/19 authorship (ex/auth/sanct)
                + "(?:" + AUTHORSHIP + ")?"
                # #20 year with or without brackets
                + r"(?: ?\(?,?(" + YEAR_LOOSE + r")\)?)?"
                + ")"

                # #21 any remainder
                + r"(\b.*?)??$"
            )


    def __init__(self, scientificName=None, rank=None):
        """ 
            :param scientificName: the full scientific name to parse
            :param rank: the rank of the name if it is known externally. Helps identifying infrageneric names vs bracket authors
        """
        self.rank = rank
        self.scientificName = scientificName
        self.pn = ParsedName()
        self.pn.rank = rank
        self.ignoreAuthorship = None

    def unparsable(self, type_):
        raise UnparsableNameException(type_, self.scientificName)

    def parse(self, name=None):
        """
            Fully parse the supplied name also trying to extract authorships, a conceptual sec reference, remarks or notes
            on the nomenclatural status. In some cases the authorship parsing proves impossible and this nameparser will
            return null.

            For strings which are no scientific names and scientific names that cannot be expressed by the ParsedName class
            the parser will throw an UnparsableException with a given NameType and the original, unparsed name. This is the
            case for all virus names and proper hybrid formulas, so make sure you catch and process this exception.
            
            :throws UnparsableNameException
        """
        
        if name is not None:
            self.scientificName = name
        
        if not isinstance(self.scientificName, str):
            self.unparsable(NameType.NO_NAME)

        # clean name, removing seriously wrong things
        name = self.preClean(self.scientificName)

        # before further cleaning/parsing try if we have known OTU formats, i.e. BIN or SH numbers
        m = self.OTU_PATTERN.search(name)
        if m:
            self.pn.uninomial = m.group(1).upper()
            self.pn.type = NameType.OTU
            self.setRankIfNotContradicting(Rank.SPECIES)
            self.pn.setState(self.ParsedName.State.COMPLETE)
        else:
            # do the main incremental parsing
            self.parse_name(name)

        # build canonical name
        return self.pn

    def parse_name(self, name):
        # remove extinct markers
        name = self.EXTINCT_PATTERN.sub("", name, 1)

        # before any cleaning test for properly quoted candidate names
        m = self.IS_CANDIDATUS_QUOTE_PATTERN.search(self.scientificName)
        if m:
            self.pn.candidatus = True
            name = m.re.sub(m.group(2), m.string, 1)

        # normalize bacterial rank markers
        name = self.TYPE_TO_VAR.sub(r"\1var", name)

        # TODO: parse manuscript names properly
        m = self.INFRASPEC_UPPER.search(name)
        infraspecEpithet = None
        if m:
            # we will replace is later again with infraspecific we memorized here!!!
            name = m.re.sub("vulgaris", m.string, 1)
            infraspecEpithet = m.group(1)
            self.pn.type = NameType.INFORMAL

        # remove placeholders from infragenerics and authors and set type
        name, n = self.REMOVE_PLACEHOLDER_AUTHOR.subn(r" \1", name, 1)
        if n > 0:
            self.pn.type = NameType.PLACEHOLDER
        
        name, n = self.REMOVE_PLACEHOLDER_INFRAGENERIC.subn("", name, 1)
        if n > 0:
            self.pn.type = NameType.PLACEHOLDER

        # resolve parsable names with a placeholder genus only
        name, n = self.PLACEHOLDER_GENUS.subn("? ", name, 1)
        if n:
            self.pn.type = NameType.PLACEHOLDER

        # detect further unparsable names
        if self.PLACEHOLDER.search(name):
            self.unparsable(NameType.PLACEHOLDER)

        if self.IS_VIRUS_PATTERN.search(name) or  \
            self.IS_VIRUS_PATTERN_CASE_SENSITIVE.search(name):
            self.unparsable(NameType.VIRUS)

        # detect RNA/DNA gene/strain names and flag as informal
        if self.IS_GENE.search(name):
            self.pn.type = NameType.INFORMAL

        # normalise name
        name = self.normalize(name)

        if name is None or name == '':
            self.unparsable(NameType.NO_NAME)

        # remove family in front of subfamily ranks
        name = self.FAMILY_PREFIX.sub(r"\1", name, 1)
        
        # check for supraspecific ranks at the beginning of the name
        m = self.SUPRA_RANK_PREFIX.search(name)
        if m:
            self.pn.rank = rankutils.RANK_MARKER_MAP.get(m.group(1).replace(".", ""))
            name = m.re.sub("", name, 1)

        # parse cultivar names first BEFORE we strongly normalize
        # this will potentially remove quotes needed to find cultivar names
        # this will potentially remove quotes needed to find cultivar group names
        m = self.CULTIVAR_GROUP.search(name)
        if m:
            self.pn.cultivarEpithet = m.group(1)
            name = m.re.sub(" ", name, 1)
            cgroup = m.group(2)
            if cgroup.lower() == "grex" or cgroup.lower() == "gx":
                self.pn.rank = Rank.GREX
            else:
                self.pn.rank = Rank.CULTIVAR_GROUP

        m = self.CULTIVAR.search(name)
        if m:
            self.pn.cultivarEpithet = m.group(2)
            name = m.re.sub(r"\1", name, 1)
            self.pn.rank = Rank.CULTIVAR

        # name without any latin char letter at all?
        if self.NO_LETTERS.search(name):
            self.unparsable(NameType.NO_NAME)

        if self.HYBRID_FORMULA_PATTERN.search(name):
            self.unparsable(NameType.HYBRID_FORMULA)

        name, n = self.IS_CANDIDATUS_PATTERN.subn("", name, 1)
        if n > 0:
            self.pn.candidatus = True

        # extract nom.illeg. and other nomen status notes
        notes = ''
        for m in self.EXTRACT_NOMSTATUS.finditer(name):
            if len(notes) > 0:
                notes += " "
            note = m.group(1).strip()
            notes += note
            # if there was a rank given in the nom status populate the rank marker field
            rm = self.NOV_RANK_MARKER.search(note)
            if rm:
                self.setRank(rm.group(1), True)

        name = self.EXTRACT_NOMSTATUS.sub("", name)  # check if this works as intended
        self.pn.nomenclaturalNotes = stripToNone(notes)

        # manuscript names (unpublished names)
        # http://splink.cria.org.br/docs/appendix_j.pdf
        m = self.MANUSCRIPT_NAMES.search(name)
        if m:
            self.pn.type = NameType.INFORMAL
            self.pn.addRemark(m.group(0))
            self.setRank(m.group(1).replace("indet", "sp"))
            name = m.re.sub("", name, 1)
            
        name, n = self.MANUSCRIPT_SUFFIX.subn("", name, 1)
        if n:
            self.pn.type = NameType.INFORMAL

        # parse out species/strain names with numbers found in Genebank/EBI names, e.g. Advenella kashmirensis W13003
        m = self.STRAIN.search(name)
        if m:
            name = m.re.sub(m.group(1), name, 1)
            self.pn.type = NameType.INFORMAL
            self.pn.strain = m.group(2)

        # extract sec reference
        m = self.EXTRACT_SENSU.search(name)
        if m:
            self.pn.taxonomicNote = self.normNote(m.group(1))
            name = m.re.sub("", name, 1)

        # extract other remarks
        m = self.EXTRACT_REMARKS.search(name)
        if m:
            self.pn.remarks = stripToNone(m.group(1))
            name = m.re.sub("", name, 1)

        # check for indets
        m = self.RANK_MARKER_AT_END.search(name)
        # f. is a marker for forms, but more often also found in authorships as "filius" - son of.
        # so ignore those
        if m and not self.FILIUS_AT_END.search(name):
            # use as rank unless we already have a cultivar
            self.ignoreAuthorship = True
            if self.pn.cultivarEpithet is None:
                self.setRank(m.group(2))
            
            name = m.re.sub("", name)

        # remove informal identification notes
        m = self.REPL_AFF.search(name)
        if m:
            self.pn.type = NameType.INFORMAL
            self.pn.addRemark(m.group(0))
            name = m.re.sub("", name)

        # replace bibliographic in references
        m = self.REPL_IN_REF.search(name)
        if m:
            self.pn.addRemark(self.normNote(m.group(0)))
            name = m.re.sub("", name, 1)

        # remove superflous epithets with rank markers
        m = self.REMOVE_INTER_RANKS.search(name)
        if m:
            self.pn.addWarning("Intermediate classification removed: " + m.group(1))
            name = m.re.sub(r"\2", name, 1)

        # remember current rank for later reuse
        preparsingRank = self.pn.rank

        nameStrongly = self.normalizeStrong(name)

        if nameStrongly is None or nameStrongly == '':
            # we might have parsed out remarks already which we treat as a placeholder
            if self.pn.hasName():
                # stop here!
                self.pn.state = State.COMPLETE
                self.pn.type = NameType.PLACEHOLDER
                return
            else:
                self.unparsable(NameType.NO_NAME)

        # try regular parsing
        parsed = self.parseNormalisedName(nameStrongly)
        if not parsed:
            # try to spot a virus name once we know its not a scientific name
            m = self.IS_VIRUS_PATTERN_POSTFAIL.search(nameStrongly)
            if m:
                self.unparsable(NameType.VIRUS)

            # cant parse it, fail!
            # Does it appear to be a genuine name starting with a monomial?
            if self.POTENTIAL_NAME_PATTERN.search(name):
                self.unparsable(NameType.SCIENTIFIC)
            else:
                self.unparsable(NameType.NO_NAME)

        # did we parse a infraspecic manuscript name?
        if infraspecEpithet is not None:
            self.pn.infraspecificEpithet = infraspecEpithet

        # if we established a rank during preparsing make sure we use this not the parsed one
        if preparsingRank is not None and preparsingRank != Rank.UNRANKED and self.rank != preparsingRank:
            self.pn.rank = preparsingRank
        
        # determine name type
        self.determineNameType(name)

        # flag names that match doubtful patterns
        self.applyDoubtfulFlag(self.scientificName)

        # determine rank if not yet assigned
        if self.pn.rank.otherOrUnranked():
            self.pn.rank = rankutils.inferRankFromParsedName(self.pn)

        # determine code if not yet assigned
        self.determineCode()
        
    def normNote(self, note):
        if note.startswith("(") and note.endswith(")"):
            note = note[1:-1]
        note = note.strip()
        # punctuation followed by a space, dots are special because of author initials
        note = re.sub( "([,;)])(?!= )", r"\1 ", note)
        # opening brackets with space
        note = re.sub("(?<! )([(])", r" \1", note)
        # dots before years and after lower case words should have a space
        note = re.sub("(?:\\.(?=" + self.YEAR + ")|(?<=\\b[a-z]{2,})\\.(?! ))", ". ", note)
        # ands with space
        note = note.replace("&", "& ")
        return note
    
    def normalize(self, name):
        """
            Carefully normalizes a scientific name trying to maintain the original as close as possible.
            In particular the string is normalized by:
                - adding commas in front of years
                - trims whitespace around hyphens
                - pads whitespace around &
                - adds whitespace after dots following a genus abbreviation, rank marker or author name
                - keeps whitespace before opening and after closing brackets
                - removes whitespace inside brackets
                - removes whitespace before commas
                - normalized hybrid marker to be the ascii multiplication sign
                - removes whitespace between hybrid marker and following name part in case it is NOT a hybrid formula
                - trims the string and replaces multi whitespace with single space
                - capitalizes all only uppercase words (authors are often found in upper case only)

            :param name: name To normalize

            :return The normalized name
        """
        if (name is None):
            return

        # translate some very similar characters that sometimes get misused instead of real letters
        name = name.replace("¡", "i")

        # normalise usage of rank marker with 2 dots, i.e. forma specialis and sensu latu
        name = self.FORM_SPECIALIS.sub("fsp", name)
        name = self.SENSU_LATU.sub("sl", name)

        # cleanup years
        name = self.NORM_YEAR.sub(r"\1", name)

        # remove imprint years. See ICZN §22A.2.3 http://www.iczn.org/iczn/index.jsp?nfv=&article=22
        m = self.NORM_IMPRINT_YEAR.search(name)
        if m:
            name = m.re.sub(r"\1", name)

        # replace underscores
        name = self.REPL_UNDERSCORE.sub(" ", name)

        # normalise punctuations removing any adjacent space
        name = self.NORM_PUNCTUATIONS.sub(r"\1", name)

        # normalise different usages of ampersand, and, et &amp; to always use &
        name = self.NORM_AND.sub("&", name)

        # remove commans after basionym brackets
        name = self.COMMA_AFTER_BASYEAR.sub("$1)", name, 1)

        # no whitespace before and after brackets, keeping the bracket style
        name = self.NORM_BRACKETS_OPEN.sub(r"\1", name)
        name = self.NORM_BRACKETS_CLOSE.sub(r"\1", name)
     
        # normalize hybrid markers
        name = self.NORM_HYBRIDS_GENUS.sub(r"×\1", name, 1)
        name = self.NORM_HYBRIDS_EPITH.sub(r"\1 ×\2", name, 1)
        name = self.NORM_HYBRIDS_FORM.sub(" × ", name)
        # capitalize all entire upper case words
        for m in self.NORM_UPPERCASE_WORDS.finditer(name):
            name = name.replace(m.group(1)+m.group(2), m.group(1)+m.group(2).lower(), 1)

        # Capitalize potential owercase genus in binomials
        m = self.NORM_LOWERCASE_BINOMIAL.search(name)
        if m:
            name = m.re.sub(m.group(1).capitalize() + " " + m.group(2), name, 1)

        # finally whitespace and trimming
        name = self.NORM_WHITESPACE.sub(" ", name)
        return name.strip()

    
    def normalizeStrong(self, name):
        """
            Does the same as a normalize and additionally removes all ( ) and "und" etc
            Checks if a name starts with a blacklisted name part like "Undetermined" or "Uncertain" and only returns the
            blacklisted word in that case
            so its easy to catch names with blacklisted name parts.
            
            :param name: name To normalize
        
            :return The normalized name
        """
        if name is None:
            return
        
        # normalize ex hort. (for gardeners, often used as ex names) spelled in lower case
        name = self.NORM_EX_HORT.sub("hort.ex ", name)

        # normalize all quotes to single "
        name = self.NORM_QUOTES.sub("'", name)
        # remove quotes from genus
        name = self.REPL_GENUS_QUOTE.sub(r"\1 ", name, 1)
        # remove enclosing quotes
        name, n = self.REPL_ENCLOSING_QUOTE.subn("", name)
        if n > 0:
            self.pn.addWarning(Warnings.REPL_ENCLOSING_QUOTE)


        # no question marks after letters (after years they should remain)
        name, n = self.NO_Q_MARKS.subn(r"\1", name)
        if n > 0:
            self.pn.doubtful = True
            self.pn.addWarning(Warnings.QUESTION_MARKS_REMOVED)

        # remove prefixes
        name = self.REPL_RANK_PREFIXES.sub("", name)

        # remove brackets inside the genus, the kind taxon finder produces
        name = self.NORM_TF_GENUS.sub(r"\1\2 ", name)

        # TODO: replace square brackets, keeping content (or better remove all within?)
        #name = NORM_NO_SQUARE_BRACKETS.matcher(name).replaceAll(" $1 ")

        # replace different kind of brackets with ()
        name = self.NORM_BRACKETS_OPEN_STRONG.sub("(", name)
        name = self.NORM_BRACKETS_CLOSE_STRONG.sub(")", name)

        # add ? genus when name starts with an epithet
        name, n = self.STARTING_EPITHET.subn(r"? \1", name, 1)
        if n > 0:
            self.pn.addWarning(Warnings.MISSING_GENUS)


        # add parenthesis around subgenus if missing
        m = self.NORM_SUBGENUS.search(name)
        if m:
            # make sure epithet is not a rank mismatch
            if self.parseRank(m.group(3)) is None:
                name = m.re.sub(r"\1(\2)\3", name)

        # finally NORMALIZE PUNCTUATION AND WHITESPACE again
        name = self.NORM_PUNCTUATIONS.sub(r"\1", name)
        name = self.NORM_WHITESPACE.sub(" ", name)
        return name.strip()

   
    def preClean(self, name):
        """
            basic careful cleaning, trying to preserve all parsable name parts
        """
        
        # remove bad whitespace in html entities
        name = self.XML_ENTITY_STRIP.sub(r"&\1", name)

        # unescape html entities
        length = len(name)
        name = html.unescape(name)
        if length > len(name):
            self.pn.addWarning(Warnings.HTML_ENTITIES)

        # finally remove still existing bad ampersands missing the closing ;
        name, n = self.AMPERSAND_ENTITY.subn("&", name)
        if n > 0:
            self.pn.addWarning(Warnings.HTML_ENTITIES)

        # replace xml tags
        name, n = self.XML_TAGS.subn("", name)
        if n > 0:
            self.pn.addWarning(Warnings.XML_TAGS)

        # trim
        name = name.strip()
        # remove quotes in beginning and matching ones at the end
        for c in self.QUOTES:
            idx = 0
            while idx < len(name) and (c == name[idx] or name[idx].isspace()):
                idx += 1
            if idx > 0:
                # check if we also find this char at the end
                end = 0
                while c == name[len(name) - 1 - end] and (len(name) - idx - end) > 0:
                    end += 1
                name = name[idx:len(name) - end + 1]
    
        name = self.NORM_WHITESPACE.sub(" ", name)
        # replace various single quote apostrophes with always '
        name = self.NORM_APOSTROPHES.sub("'", name)

        return name.strip()

    def setTypeIfNull(self, pn, type_):
        if pn.type is None:
            pn.type = type_

    def determineNameType(self, normedName):
        """
            Identifies a name type, defaulting to SCIENTIFIC_NAME so that type is never null
        """
        
        # all rules below do not apply to unparsable names
        if self.pn.type is None or self.pn.type.isParsable():
            # if we only match a monomial in the 3rd pass its suspicious
            if self.pn.uninomial is not None and normedName[0].islower():
                self.pn.addWarning(Warnings.LC_MONOMIAL)
                self.pn.doubtful = True
                self.setTypeIfNull(self.pn, NameType.INFORMAL)

            elif self.pn.rank.notOtherOrUnranked():
                if self.pn.isIndetermined():
                    self.pn.type = NameType.INFORMAL
                    self.pn.addWarning(Warnings.INDETERMINED)

                elif self.pn.rank.isSupraspecific() and (self.pn.specificEpithet is not None or
                    self.pn.infraspecificEpithet is not None):
                    self.pn.addWarning(Warnings.RANK_MISMATCH)
                    self.pn.doubtful = True
                    self.pn.type = NameType.INFORMAL

                elif not self.pn.rank.isSpeciesOrBelow() and self.pn.isBinomial():
                    self.pn.addWarning(Warnings.HIGHER_RANK_BINOMIAL)
                    self.pn.doubtful = True

        if self.pn.type is None:
            # an abbreviated name?
            if self.pn.isAbbreviated() or self.pn.isIncomplete():
                self.pn.type = NameType.INFORMAL
            elif "?" == self.pn.uninomial or "?" == self.pn.genus or "?" == self.pn.specificEpithet:
                # a placeholder epithet only
                self.pn.type = NameType.PLACEHOLDER
            else:
                # anything else looks fine!
                self.pn.type = NameType.SCIENTIFIC

    def applyDoubtfulFlag(self, scientificName):
        # all rules below do not apply to unparsable names
        m = self.DOUBTFUL.search(scientificName)
        if not m:
            self.pn.doubtful = True
            self.pn.addWarning(Warnings.UNUSUAL_CHARACTERS)

        elif self.pn.type.isParsable():
            m = self.DOUBTFUL_NULL.search(scientificName)
            if m:
                self.pn.doubtful = True
                self.pn.addWarning(Warnings.NULL_EPITHET)


    def determineCode(self):
        if self.pn.code is None:
            # does the rank tell us sth?
            if self.pn.rank.isRestrictedToCode() is not None:
                self.pn.code = self.pn.rank.isRestrictedToCode()

            elif self.pn.cultivarEpithet is not None:
                self.pn.code = NomCode.CULTIVARS

            elif self.pn.sanctioningAuthor is not None:
                # sanctioning is only for Fungi
                self.pn.code = NomCode.BOTANICAL

            elif self.pn.type == NameType.VIRUS:
                self.pn.code = NomCode.VIRUS

            elif self.pn.isCandidatus() or self.pn.strain is not None:
                self.pn.code = NomCode.BACTERIAL

            # elif self.pn.basionymAuthorship.year is not None or self.pn.combinationAuthorship.year is not None:
                # if years are given its a zoological name
            #   self.pn.code = NomCode.ZOOLOGICAL

            elif not self.pn.basionymAuthorship.isEmpty():
                if self.pn.combinationAuthorship.isEmpty():
                    # if only the basionym authorship is given its a zoological name!
                    self.pn.code = NomCode.ZOOLOGICAL

                else:
                    # if both the basionym and combination authorship is given its a botanical name!
                    self.pn.code = NomCode.BOTANICAL
            elif self.pn.nomenclaturalNotes is not None and "illeg" in self.pn.nomenclaturalNotes:
                self.pn.code = NomCode.BOTANICAL
   
    def parseNormalisedName(self, name):
        """
            Tries to parse a name string with the full regular expression.
            In very few, extreme cases names with very long authorships might cause the regex to never finish or take hours
            we should run this parsing in a separate thread that can be stopped if it runs too long.

            :return true if the name could be parsed, false in case of failure
        """
        
        matcher = self.NAME_PATTERN.search(name)
        if matcher:
            if matcher.group(21) == '' or matcher.group(21) is None:
                self.pn.state = State.COMPLETE
            else:
                self.pn.state = State.PARTIAL
                self.pn.unparsed = stripToNone(matcher.group(21))
            # the match can be the genus part of an infrageneric, bi- or trinomial, the uninomial or even the infrageneric epithet!
            self.setUninomialOrGenus(matcher, self.pn)
            bracketSubrankFound = False
            if matcher.group(2) is not None:
                bracketSubrankFound = True
                self.pn.infragenericEpithet = stripToNone(matcher.group(2))
            elif matcher.group(4) is not None:
                self.setRank(matcher.group(3))
                self.pn.infragenericEpithet = stripToNone(matcher.group(4))
            self.pn.specificEpithet = stripToNone(matcher.group(5))
            if matcher.group(6) is not None and len(matcher.group(6)) > 1 and "null" not in matcher.group(6):
                # 4 parted name, so its below subspecies
                self.pn.rank = Rank.INFRASUBSPECIFIC_NAME
    
            if matcher.group(7) is not None and matcher.group(7) != "":
                self.setRank(matcher.group(7))
                
            self.pn.infraspecificEpithet = stripToNone(matcher.group(8))

            # microbial ranks
            if matcher.group(9) is not None:
                self.setRank(matcher.group(9))
                self.pn.infraspecificEpithet = matcher.group(10)

            # #11 indet rank markers
            if matcher.group(11) is not None:
                self.setRank(matcher.group(11))
                self.ignoreAuthorship = True

            # make sure (infra)specific epithet is not a rank marker!
            self.lookForIrregularRankMarker()

            if self.pn.isIndetermined():
                self.ignoreAuthorship = True

            # #12 is entire authorship, not stored in ParsedName
            if not self.ignoreAuthorship and stripToNone(matcher.group(12)) is not None:
                # #17/18/19/20 authorship (ex/auth/sanct/year)
                self.pn.combinationAuthorship = self.parseAuthorship(matcher.group(17), matcher.group(18), matcher.group(20))
                # sanctioning author
                if matcher.group(19) is not None:
                    self.pn.sanctioningAuthor = matcher.group(19)

                # #13/14/15/16 basionym authorship (ex/auth/sanct/year)
                self.pn.basionymAuthorship = self.parseAuthorship(matcher.group(13), matcher.group(14), matcher.group(16))
                if bracketSubrankFound and self.infragenericIsAuthor(self.pn):
                    # rather an author than a infrageneric rank. Swap in case of monomials
                    self.pn.basionymAuthorship = self.parseAuthorship(None, self.pn.infragenericEpithet, None)
                    self.pn.infragenericEpithet = None
                    # check if we need to move genus to uninomial
                    if self.pn.genus is not None and self.pn.specificEpithet is None and self.pn.infraspecificEpithet is None:
                        self.pn.uninomial = self.pn.genus
                        self.pn.genus = None

            return True

        return False

    @staticmethod
    def cleanYear(matchedYear):
        if matchedYear is not None and len(matchedYear) > 2:
            return matchedYear.strip()

    def setRank(self, rankMarker, force=False):
        """
            Sets the parsed names rank based on a found rank marker
            Potentially also sets the notho field in case the rank marker indicates a hybrid
            if the rankMarker cannot be interpreted or is null nothing will be done.
        """
        
        rank = self.parseRank(rankMarker)
        if rank is not None and rank.notOtherOrUnranked():
            if force:
                self.pn.rank = rank
            else:
                self.setRankIfNotContradicting(rank)
            if rankMarker.startswith(self.NOTHO):
                if rank.isInfraspecific():
                    self.pn.notho = NamePart.INFRASPECIFIC
                elif rank == Rank.SPECIES:
                    self.pn.notho = NamePart.SPECIFIC
                elif rank.isInfrageneric():
                    self.pn.notho = NamePart.INFRAGENERIC
                elif rank == Rank.GENUS:
                    self.pn.notho = NamePart.GENERIC

    
    def setRankIfNotContradicting(self, rank):
        """
            Sets the rank if the current rank of the parsed name is not contradicting
            to the given one. Mostly this is the case to define a Unranked rank.
        """
        
        if self.pn.rank.isUncomparable():
            if (self.pn.rank == Rank.INFRAGENERIC_NAME and not rank.isInfragenericStrictly()) \
                    or (self.pn.rank == Rank.INFRASPECIFIC_NAME and not rank.isInfraspecific()) \
                    or (self.pn.rank == Rank.INFRASUBSPECIFIC_NAME and not rank.isInfrasubspecific()):
                return
            self.pn.rank = rank

    @staticmethod
    def parseRank(rankMarker):
        return rankutils.inferRankFromMarker(stripToNone(rankMarker))

    @classmethod
    def infragenericIsAuthor(cls, pn):
        return pn.basionymAuthorship.isEmpty() \
            and pn.specificEpithet is None \
            and pn.infraspecificEpithet is None \
            and not pn.rank.isInfragenericStrictly() \
            and not cls.LATIN_ENDINGS.search(pn.infragenericEpithet)

    @staticmethod
    def setUninomialOrGenus(matcher, pn):
        """
            The first Capitalized word can be stored in 3 different places in ParsedName.
            Figure out where to best keep it:
                a) as the genus part of an infrageneric, bi- or trinomial
                b) the uninomial for names of rank genus or higher
                c) the infrageneric epithet in case its a standalone infrageneric name (which is hard to detect)
        """
        
        # the match can be the genus part of a bi/trinomial or a uninomial
        monomial = stripToNone(matcher.group(1))
        if matcher.group(2) is not None \
            or matcher.group(4) is not None \
            or matcher.group(5) is not None \
            or matcher.group(8) is not None \
            or pn.rank.isSpeciesOrBelow(): #  and self.pn.getRank().isRestrictedToCode() != NomCode.CULTIVARS
            pn.genus = monomial

        elif pn.rank.isInfragenericStrictly():
            pn.setInfragenericEpithet(monomial)

        else:
            pn.uninomial = monomial

    def lookForIrregularRankMarker(self):
        """
            if no rank marker is set, inspect epitheta for wrongly placed rank markers and modify parsed name accordingly.
            This is sometimes the case for informal names like: Coccyzus americanus ssp.
        """
        
        if self.pn.rank.otherOrUnranked():
            if self.pn.infraspecificEpithet is not None:
                m = self.RANK_MARKER_ONLY.search(self.pn.infraspecificEpithet)
                if m:
                    # we found a rank marker, make it one
                    self.setRank(self.pn.infraspecificEpithet)
                    self.pn.infraspecificEpithet = None
            if self.pn.specificEpithet is not None:
                m = self.RANK_MARKER_ONLY.search(self.pn.specificEpithet)
                if m:
                    # we found a rank marker, make it one
                    self.setRank(self.pn.specificEpithet)
                    self.pn.specificEpithet = None
        elif self.pn.rank == Rank.SPECIES and self.pn.infraspecificEpithet is not None:
            # sometimes sp. is wrongly used as a subspecies rankmarker
            self.pn.rank = Rank.SUBSPECIES
            self.pn.addWarning(Warnings.SUBSPECIES_ASSIGNED)

    @classmethod
    def parseAuthorship(cls, ex, authors, year):
        a = Authorship()
        if authors is not None:
            a.authors = cls.splitTeam(authors)
        if ex is not None:
            a.exAuthors = cls.splitTeam(ex)
        a.year = cls.cleanYear(year)
        return a

    @classmethod
    def splitTeam(cls, team):
        """
            Splits an author team by either ; or ,
        """
        # treat semicolon differently. Single author name can contain a comma now!
        if ";" in team:
            authors = []
            for a in team.split(";"):
                m = cls.AUTHOR_INITIAL_SWAP.search(a)
                if m:
                    authors.append(cls.normAuthor(m.group(2) + " " + m.group(1), True))
                else:
                    authors.append(cls.normAuthor(a, False))
            return authors

        m = cls.AUTHORTEAM_DELIMITER.search(team)
        if m:
            return cls.AUTHORTEAM_DELIMITER.split(cls.normAuthor(team, False))

        else:
            # we sometimes see space delimited authorteams with the initials consistently at the end of a single author:
            # Balsamo M Fregni E Tongiorgi MA
            SPACE_AUTHOR = "(\\p{Lu}\\p{Ll}+ \\p{Lu}+)"
            AUTHORTEAM_SPACED = re.compile("^" + SPACE_AUTHOR + "(?: " + SPACE_AUTHOR + ")*$")
            AUTHOR_SPACED = re.compile("(\\p{Lu}\\p{Ll}+) (\\p{Lu}+)")
            ms = AUTHORTEAM_SPACED.findall(team)
            if ms:
                # We should be able to extract the authors from the first match instead of doing it again
                authors = []
                for g in ms:
                    sb = ""
                    for initial in g[1]:
                        sb += initial + '.'
                    sb += g[0]
                    authors.append(sb)
                return authors
            else:
                # no delimiters found, treat as one author
                return [cls.normAuthor(team, False)]

    @classmethod
    def normAuthor(cls, authors, normPunctuation):
        """
            Author strings are normalized by removing any whitespace following a dot.
            See IPNI author standard form recommendations: http://www.ipni.org/standard_forms_author.html
        """
        if normPunctuation:
            authors = cls.NORM_PUNCTUATIONS.sub(r"\1", authors)
        return stripToNone(authors)
 
