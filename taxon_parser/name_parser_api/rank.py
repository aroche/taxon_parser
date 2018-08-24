from enum import Enum


class NomCode:
    """
    Enumeration representing the different nomenclatoral codes found in biology for scientific names.
    
    Nomenclature codes or codes of nomenclature are the various rulebooks that govern biological taxonomic
    nomenclature, each in their own broad field of organisms.
    To an end-user who only deals with names of species, with some awareness that species are assignable to
    families, it may not be noticeable that there is more than one code, but beyond this basic level these are rather
    different in the way they work.

    @see <a href="http://en.wikipedia.org/wiki/Nomenclature_codes">Nomenclature codes (Wikipedia)</a>
    """

    BACTERIAL = ("ICNB",
        "International Code of Nomenclature of Bacteria",
        "http://www.ncbi.nlm.nih.gov/books/NBK8808/")
    BOTANICAL = ("ICNafp",
        "International Code of Nomenclature for algae, fungi, and plants",
        "http://ibot.sav.sk/icbn/main.htm")
    CULTIVARS = ("ICNCP",
        "International Code of Nomenclature for Cultivated Plants",
        "")
    VIRUS = ("ICVCN",
        "International Code of Virus Classifications and Nomenclature",
        "http://talk.ICTVonline.org/")
    ZOOLOGICAL = ("ICZN",
        "International Code of Zoological Nomenclature",
        "http://www.nhm.ac.uk/hosted-sites/iczn/code/index.jsp")
    
    def __init__(self, acronym, title, link):
        self.title = title
        self.acronym = acronym
        self.link = link


class Rank(Enum):
    """
    An ordered taxonomic rank enumeration with the most frequently used values.
    Several static methods, lists, sets and maps are provided to help with ordering and lookup from strings.
    
    @see <a href="http://rs.gbif.org/vocabulary/gbif/rank.xml">rs.gbif.org vocabulary</a>
    """

    DOMAIN = "dom."
    SUPERKINGDOM = "superreg."
    KINGDOM = "reg."
    SUBKINGDOM = "subreg."
    INFRAKINGDOM = "infrareg."
    SUPERPHYLUM = "superphyl."
    PHYLUM = "phyl."
    SUBPHYLUM = "subphyl."
    INFRAPHYLUM = "infraphyl."
    SUPERCLASS = "supercl."
    CLASS = "cl."
    SUBCLASS = "subcl."
    INFRACLASS = "infracl."
    PARVCLASS = "parvcl."
    SUPERLEGION = "superleg."

    # Sometimes used in zoology, e.g. for birds and mammals
    LEGION = "leg."
    SUBLEGION = "subleg."
    INFRALEGION = "infraleg."
    SUPERCOHORT = "supercohort"

    # Sometimes used in zoology, e.g. for birds and mammals
    COHORT = "cohort"
    SUBCOHORT = "subcohort"
    INFRACOHORT = "infracohort"
    MAGNORDER = "magnord."
    SUPERORDER = "superord."
    GRANDORDER = "grandord."
    ORDER = "ord."
    SUBORDER = "subord."
    INFRAORDER = "infraord."
    PARVORDER = "parvord."
    SUPERFAMILY = "superfam."
    FAMILY = "fam."
    SUBFAMILY = "subfam."
    INFRAFAMILY = "infrafam."
    SUPERTRIBE = "supertrib."
    TRIBE = "trib."
    SUBTRIBE = "subtrib."
    INFRATRIBE = "infratrib."

    # Used for any other unspecific rank above genera.
    SUPRAGENERIC_NAME = "supragen."
    GENUS = "gen."
    SUBGENUS = "subgen."
    INFRAGENUS = "infrag."
    SUPERSECTION = "supersect."
    SECTION = "sect."
    SUBSECTION = "subsect."
    SUPERSERIES = "superser."
    SERIES = "ser."
    SUBSERIES = "subser."

    # used for any other unspecific rank below genera and above species aggregates.
    INFRAGENERIC_NAME = "infragen."

    # A loosely defined group of species.
    # Zoology: Aggregate - a group of species, other than a subgenus, within a genus. An aggregate may be denoted by a group name interpolated in parentheses.
    # The Berlin/MoreTax model notes: [these] aren't taxonomic ranks but cirumscriptions because on the one hand they are necessary for the concatenation
    # of the fullname and on the other hand they are necessary for distinguishing the aggregate or species group from the microspecies.
    SPECIES_AGGREGATE = "agg."
    SPECIES = "sp."

    # used for any other unspecific rank below species.
    INFRASPECIFIC_NAME = "infrasp."

    # The term grex has been coined to expand botanical nomenclature to describe hybrids of orchids.
    # Grex names are one of the three categories of plant names governed by the International Code of Nomenclature for Cultivated Plants
    # Within a grex the Groups category can be used to refer to plants by their shared characteristics  = rather than by their parentage
    # and individual orchid plants can be selected  = and propagated) and named as cultivars
    # https://en.wikipedia.org/wiki/Grex_ = horticulture)
    GREX = "gx"

    SUBSPECIES = "subsp."
    
    # Rank in use from the code for cultivated plants.
    # It does not use a classic rank marker but indicated the Group rank after the actual groups name
    # For example Rhododendron boothii Mishmiense Group
    # or Primula Border Auricula Group
    # <p>
    # Sometimes authors also used the words "sort", "type", "selections" or "hybrids" instead of Group which is not legal according to the code.
    CULTIVAR_GROUP = "cvg"

    # A group of cultivars. These can be roughly comparable to cultivar groups, but convarieties, unlike cultivar groups,
    # do not necessarily contain named varieties, and convarieties are members of traditional "Linnaean" ranks.
    # The ICNCP replaced this term with the term cultivar-group, and convarieties should not be used in modern cultivated plant taxonomy.
    # <p>
    # From Spooner et al., Horticultural Reviews 28 (2003): 1-60
    CONVARIETY = "convar."

    # used also for any other unspecific rank below subspecies.
    INFRASUBSPECIFIC_NAME = "infrasubsp."

    # Botanical legacy rank for a race, recommended in botanical code from 1868
    PROLES = "prol."

    # Zoological legacy rank
    NATIO = "natio"

    
    # Zoological legacy rank
    ABERRATION = "ab."

    
    # Zoological legacy rank
    MORPH = "morph"
    VARIETY = "var."
    SUBVARIETY = "subvar."
    FORM = "f."
    SUBFORM = "subf."

    # Microbial rank based on pathogenic reactions in one or more hosts.
    # For recommendations on designating pathovars and use of designations when reviving names see
    # Dye et al. (1980) Standards for naming pathovars of phytopathogenic bacteria and a list of pathovar names and pathotype strains.
    # Rev. Plant Pathol. 59:153–168.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # See <a href="http://www.isppweb.org/about_tppb_naming.asp">International Standards for Naming Pathovars of Phytopathogenic Bacteria</a>
    # See <a href="http://sipav.org/main/jpp/index.php/jpp/article/view/682">Demystifying the nomenclature of bacterial plant pathogens</a>
    # See <a href="http://link.springer.com/chapter/10.1007/978-94-009-3555-6_171">Problems with the Pathovar Concept</a>
    # For example Pseudomonas syringae pv. lachrymans
    PATHOVAR = "pv."

    # Microbial rank based on biochemical or physiological properties.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Francisella tularensis biovar tularensis
    BIOVAR = "biovar"
    
    # Microbial rank based on production or amount of production of a particular chemical.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Vibrio alginolyticus chemovar iophagus
    CHEMOVAR = "chemovar"

    # Microbial rank based on morphological characterislics.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Acinetobacter junii morphovar I
    MORPHOVAR = "morphovar"

    # Microbial infrasubspecific rank based on reactions to bacteriophage.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Staphyloccocus aureus phagovar 42D
    PHAGOVAR = "phagovar"
    
    # Microbial infrasubspecific rank based on antigenic characteristics.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Salmonella enterica serovar Dublin
    SEROVAR = "serovar"

    # Microbial infrasubspecific rank based on chemical constitution.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Thymus vulgaris ct. geraniol
    CHEMOFORM = "chemoform"
    
    # Microbial infrasubspecific rank.
    # A parasitic, symbiotic, or commensal microorganism distinguished primarily by adaptation to a particular host or habitat.
    # Named preferably by the scientific name of the host in the genitive.
    # See <a href="http://www.ncbi.nlm.nih.gov/books/NBK8812/table/A844/?report=objectonly">Bacteriological Code</a>
    # For example Puccinia graminis f. sp. avenae
    FORMA_SPECIALIS = "f.sp."
    CULTIVAR = "cv."
    
    # A microbial strain.
    STRAIN = "strain"

    # Any other rank we cannot map to this enumeration
    OTHER = 0

    # Rank used for unknown or explicitly not assigned rank.
    # The default if not given instead of null.
    UNRANKED = 1

    # All main Linnean ranks ordered.
    LINNEAN_RANKS = (
        KINGDOM,
        PHYLUM,
        CLASS,
        ORDER,
        FAMILY,
        GENUS,
        SPECIES
    )

    
    # An ordered list of all ranks that appear in Darwin Core with their own term.
    DWC_RANKS = (
        KINGDOM,
        PHYLUM,
        CLASS,
        ORDER,
        FAMILY,
        GENUS,
        SUBGENUS,
        SPECIES
    )

    
    # A set of ranks which cannot clearly be compared to any other rank as they represent rank "ranges".
    # For example a subgeneric rank is anything below genus,
    # so one cannot say if its higher or lower than a species for example.
    UNCOMPARABLE_RANKS = {
        SUPRAGENERIC_NAME,
        INFRAGENERIC_NAME,
        INFRASPECIFIC_NAME,
        INFRASUBSPECIFIC_NAME,
        OTHER,
        UNRANKED
    }

    LEGACY_RANKS = {
        MORPH,
        ABERRATION,
        NATIO,
        PROLES,
        CONVARIETY
    }

    RANK2CODE = {
        'PARVCLASS': NomCode.ZOOLOGICAL,
        'MAGNORDER': NomCode.ZOOLOGICAL,
        'GRANDORDER': NomCode.ZOOLOGICAL,
        'PARVORDER': NomCode.ZOOLOGICAL,
        'SUPERLEGION': NomCode.ZOOLOGICAL,
        'LEGION': NomCode.ZOOLOGICAL,
        'SUBLEGION': NomCode.ZOOLOGICAL,
        'INFRALEGION': NomCode.ZOOLOGICAL,
        'SUPERCOHORT': NomCode.ZOOLOGICAL,
        'COHORT': NomCode.ZOOLOGICAL,
        'SUBCOHORT': NomCode.ZOOLOGICAL,
        'INFRACOHORT': NomCode.ZOOLOGICAL,
        'MORPH': NomCode.ZOOLOGICAL,
        'ABERRATION': NomCode.ZOOLOGICAL,
        'NATIO': NomCode.ZOOLOGICAL,
        
        'PROLES': NomCode.BOTANICAL,
        'SUPERSECTION': NomCode.BOTANICAL,
        'SECTION': NomCode.BOTANICAL,
        'SUBSECTION': NomCode.BOTANICAL,
        'SUPERSERIES': NomCode.BOTANICAL,
        'SERIES': NomCode.BOTANICAL,
        'SUBSERIES': NomCode.BOTANICAL,

        'CULTIVAR': NomCode.CULTIVARS,
        'CULTIVAR_GROUP': NomCode.CULTIVARS,
        'CONVARIETY': NomCode.CULTIVARS,
        'GREX': NomCode.CULTIVARS,

        'PATHOVAR': NomCode.BACTERIAL,
        'BIOVAR': NomCode.BACTERIAL,
        'CHEMOVAR': NomCode.BACTERIAL,
        'MORPHOVAR': NomCode.BACTERIAL,
        'PHAGOVAR': NomCode.BACTERIAL,
        'SEROVAR': NomCode.BACTERIAL,
        'CHEMOFORM': NomCode.BACTERIAL,
        'FORMA_SPECIALIS': NomCode.BACTERIAL,
        }

    def __init__(self, *args, marker=None):
        super().__init__()
        self.marker = marker
        
    def ordinal(self):
        " Convenient method to get the order of the member "
        return list(self.__class__.__members__.keys()).index(self.name)
    
    # @return true for infraspecific ranks excluding species.
    def isInfraspecific(self):
        return self.ordinal() > self.SPECIES.ordinal() and self.notOtherOrUnranked()

    # @return true for infra subspecific ranks.
    def isInfrasubspecific(self):
        return self.ordinal() > self.SUBSPECIES.ordinal() and self.notOtherOrUnranked()

    # @return true for rank is below genus. Also includes species and infraspecific ranks
    def isInfrageneric(self):
        return self.ordinal() > Rank.GENUS.ordinal() and self.notOtherOrUnranked()

    # @return true for real infrageneric ranks with an infragenericEpithet below genus and above species aggregate.
    def isInfragenericStrictly(self):
        return self.isInfrageneric() and self.ordinal() < self.SPECIES_AGGREGATE.ordinal()
    
    # True for all mayor Linnéan ranks, ie kingdom,phylum,class,order,family,genus and species.
    def isLinnean(self):
        return self in self.LINNEAN_RANKS

    def isSpeciesOrBelow(self):
        return self.ordinal() >= self.SPECIES_AGGREGATE.ordinal() and self.notOtherOrUnranked()

    def notOtherOrUnranked(self):
        return self != self.OTHER and self != self.UNRANKED

    def otherOrUnranked(self):
        return self == self.OTHER or self == self.UNRANKED
    
    # @return true if the rank is for family group names, i.e. between family (inclusive) and genus (exclusive).
    def isFamilyGroup(self):
        return self.FAMILY.ordinal() <= self.ordinal() and self.ordinal() < self.GENUS.ordinal()

    # @return true if the rank is for genus group names, i.e. between genus (inclusive) and species aggregate (exclusive).
    def isGenusGroup(self):
        return self.GENUS.ordinal() <= self.ordinal() and self.ordinal() < self.SPECIES_AGGREGATE.ordinal()
    
    # @return true if the rank is above genus.
    def isSuprageneric(self):
        return self.ordinal() < self.GENUS.ordinal()
    
    # @return true if the rank is above genus.
    def isGenusOrSuprageneric(self):
        return self.ordinal() <= self.GENUS.ordinal()
    
    # @return true if the rank is above the rank species aggregate.
    def isSupraspecific(self):
        return self.ordinal() < self.SPECIES_AGGREGATE.ordinal()
    
    # True for names of informal ranks that represent a range of ranks really and therefore cannot safely be compared to
    # other ranks in all cases.
    # Example ranks are INFRASPECIFIC_NAME or INFRAGENERIC_NAME
    # @return true if uncomparable
    def isUncomparable(self):
        return self in self.UNCOMPARABLE_RANKS.value
    
    # @return true if the rank is considered a legacy rank not used anymore in current nomenclature.
    def isLegacy(self):
        return self in self.LEGACY_RANKS
   
    # @return the nomenclatural code if the rank is restricted to just one code or null otherwise
    def isRestrictedToCode(self):
        return self.RANK2CODE.value.get(self.name)
    
    # @return true if the rank is restricted to Cultivated Plants
    def isCultivarRank(self):
        return NomCode.CULTIVARS == self.isRestrictedToCode()
    
    # @return true if this rank is higher than the given other
    def higherThan(self, other):
        return self.ordinal() < other.ordinal()
