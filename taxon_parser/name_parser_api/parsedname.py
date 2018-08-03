from enum import Enum, auto
from .authorship import Authorship
from .rank import Rank, NomCode
from .namepart import NamePart
from .util import nameformatter


class State(Enum):
    COMPLETE = auto()
    PARTIAL = auto()
    NONE = auto()


class ParsedName:
    """ Class holding the different parts of the name once it has been parsed """
    
    def __init__(self):
        # Authorship with years of the name, but excluding any basionym authorship.
        # For binomials the combination authors.
        self.combinationAuthorship = Authorship()
        
        # Basionym authorship with years of the name
        self.basionymAuthorship = Authorship()
        
        # The sanctioning author for sanctioned fungal names. Fr. or Pers.
        self.sanctioningAuthor = None
        
        # Rank of the name from enumeration
        self.rank = Rank.UNRANKED
        self.code = None
        
        # Represents the monomial for genus, families or names at higher ranks which do not have further epithets.
        self.uninomial = None
        
        # The genus part of an infrageneric, bi- or trinomial name.
        # Not used for standalone genus names which are represented as uninomials.
        self.genus = None
        
        # The infrageneric epithet.
        self.infragenericEpithet = None
        self.specificEpithet = None
        self.infraspecificEpithet = None
        self.cultivarEpithet = None
        self.strain = None
        
        # A bacterial candidate name.
        # Candidatus is a provisional status for incompletely described procaryotes
        # (e.g. that cannot be maintained in a Bacteriology Culture Collection)
        # which was published in the January 1995.
        # The category Candidatus is not covered by the Rules of the Bacteriological Code but is a taxonomic assignment.
        
        # The names included in the category Candidatus are usually written as follows:
        # Candidatus (in italics), the subsequent name(s) in roman type and the entire name in quotation marks.
        # For example, "Candidatus Phytoplasma", "Candidatus Phytoplasma allocasuarinae".
        
        # See http://www.bacterio.net/-candidatus.html
        # and https://en.wikipedia.org/wiki/Candidatus
        self.candidatus = None
        
        # The part of the named hybrid which is considered a hybrid
        self.notho = None 
        
        # Nomenclatural status remarks of the name.
        self.taxonomicNote = None
        
        # Nomenclatural status remarks of the name.
        self.nomenclaturalNotes = None
        
        # Any informal remarks found in the name
        self.remarks = None
        
        # Any additional unparsed string found at the end of the name.
        # Only ever set when state=PARTIAL
        self.unparsed = None
        
        # The kind of name classified in broad catagories based on their syntactical structure
        self.type = None
        
        # Indicates some doubts that this is a name of the given type.
        # Usually indicates the existance of unusual characters not normally found in scientific names.
        self.doubtful = None
        
        self.state = State.NONE
        
        self.warnings = []
        
    @property    
    def rank(self):
        return self.__rank
    
    @rank.setter
    def rank(self, rank):
        if rank is None:
            self.__rank = Rank.UNRANKED
        else:
            self.__rank = rank
            
    @property
    def uninomial(self):
        return self.__uninomial
    
    @uninomial.setter
    def uninomial(self, uni):
        if uni is not None and uni != '' and uni[0] == nameformatter.HYBRID_MARKER:
            self.__uninomial = uni[1:]
            self.notho = NamePart.GENERIC
        else:
            self.__uninomial = uni
            
    @property
    def genus(self):
        return self.__genus
    
    @genus.setter
    def genus(self, genus):
        if genus is not None and genus != '' and genus[0] == nameformatter.HYBRID_MARKER:
            self.__genus = genus[1:]
            self.notho = NamePart.GENERIC
        else:
            self.__genus = genus    
            
    @property
    def infragenericEpithet(self):
        return self.__infragenericEpithet
    
    @infragenericEpithet.setter
    def infragenericEpithet(self, ige):
        if ige is not None and ige != '' and ige[0] == nameformatter.HYBRID_MARKER:
            self.__infragenericEpithet = ige[1:]
            self.notho = NamePart.INFRAGENERIC
        else:
            self.__infragenericEpithet = ige
            
    @property
    def specificEpithet(self):
        return self.__specificEpithet
    
    @specificEpithet.setter
    def specificEpithet(self, se):
        if se is not None and se != '' and se[0] == nameformatter.HYBRID_MARKER:
            self.__specificEpithet = se[1:]
            self.notho = NamePart.SPECIFIC
        else:
            self.__specificEpithet = se
            
    @property
    def infraspecificEpithet(self):
        return self.__infraspecificEpithet
    
    @infraspecificEpithet.setter
    def infraspecificEpithet(self, ise):
        if ise is not None and ise != '' and ise[0] == nameformatter.HYBRID_MARKER:
            self.__infraspecificEpithet = ise[1:]
            self.notho = NamePart.INFRASPECIFIC
        else:
            self.__infraspecificEpithet = ise
            
    def addRemark(self, remark):
        if remark != '':
            if self.remarks is None:
                self.remarks = remark.strip()
            else:
                self.remarks = self.remarks + '; ' + remark.strip()
                
    def addWarning(self, warnings):
        self.warnings += warnings
        
    def getTerminalEpithet(self):
        """ @return the terminal epithet. Infraspecific epithet if existing, the species epithet or null """
        if self.infraspecificEpithet is None:
            return self.specificEpithet
        return self.infraspecificEpithet
    
    def hasName(self):
        """ @return true if the parsed name has non null name properties or a scientific name. Remarks will not count as a name """
        for prop in (self.uninomial, self.genus, self.infragenericEpithet, self.specificEpithet, self.infraspecificEpithet, 
                 self.strain, self.cultivarEpithet):
            if prop is not None:
                return True
        return False
    
    def hasAuthorship(self):
        """ @return true if any kind of authorship exists """
        return self.combinationAuthorship.exists() or self.basionymAuthorship.exists()

    def isAutonym(self):
        return self.specificEpithet is not None and self.infraspecificEpithet is not None \
            and self.specificEpithet == self.infraspecificEpithet

    def isBinomial(self):
        """ @return true if the name is a bi- or trinomial with at least a genus and species epithet given. """
        return self.genus is not None and self.specificEpithet is not None

    def isTrinomial(self):
        """ return true if the name is a trinomial with at least a genus, species and infraspecific epithet given. """
        return self.isBinomial() and self.infraspecificEpithet is not None

    def isIndetermined(self):
        """ 
            Checks if a parsed name is missing final epithets compared to what is indicated by its rank.
    
            return true if the name is not fully determined 
        """
        
        return self.rank.isInfragenericStrictly() and self.uninomial is None and self.infragenericEpithet is None and self.specificEpithet is None \
            or self.rank.isSpeciesOrBelow() and not self.rank.isCultivarRank() and self.specificEpithet is None \
            or self.rank.isInfraspecific() and not self.rank.isCultivarRank() and self.infraspecificEpithet is None \
            or self.rank.isCultivarRank() and self.cultivarEpithet is None
    
    def isIncomplete(self):
        """ return true if some "higher" epithet of a name is missing, e.g. the genus in case of a species. """
        return (self.specificEpithet is not None or self.cultivarEpithet is not None) and self.genus is None \
            or self.infraspecificEpithet is not None and self.specificEpithet is None

    def isAbbreviated(self):
        """ return true if the name contains an abbreviated genus or uninomial """
        return self.uninomial is not None and self.uninomial[-1] == "." \
            or self.genus is not None and self.genus[-1] == "." \
            or self.specificEpithet is not None and self.specificEpithet[-1] == "."

    def canonicalName(self):
        """ See NameFormatter.canonical() """
        return nameformatter.canonical(self)

    def canonicalNameWithoutAuthorship(self):
        """ See NameFormatter.canonicalNameWithoutAuthorship() """
        return nameformatter.canonicalWithoutAuthorship(self)

    def canonicalNameMinimal(self):
        """ See NameFormatter.canonicalMinimal() """
        return nameformatter.canonicalMinimal(self)

    def canonicalNameComplete(self):
        """ See NameFormatter.canonicalComplete() """
        return nameformatter.canonicalComplete(self)

    def authorshipComplete(self):
        """ See NameFormatter.authorshipComplete() """
        return nameformatter.authorshipComplete(self)

    def isCandidatus(self):
        return self.candidatus

    def __eq__(self, o):
        if self == o:
            return True
        if o is None or self.__class__ != o.__class__:
            return False
        return self.candidatus == o.candidatus and \
            self.doubtful == o.doubtful and \
            self.state == o.state and \
            self.combinationAuthorship == o.combinationAuthorship and \
            self.basionymAuthorship == o.basionymAuthorship and \
            self.sanctioningAuthor == o.sanctioningAuthor and \
            self.rank == o.rank and \
            self.code == o.code and \
            self.uninomial == o.uninomial and \
            self.genus == o.genus and \
            self.infragenericEpithet == o.infragenericEpithet and \
            self.specificEpithet == o.specificEpithet and \
            self.infraspecificEpithet == o.infraspecificEpithet and \
            self.cultivarEpithet == o.cultivarEpithet and \
            self.strain == o.strain and \
            self.notho == o.notho and \
            self.taxonomicNote == o.taxonomicNote and \
            self.nomenclaturalNotes == o.nomenclaturalNotes and \
            self.remarks == o.remarks and \
            self.unparsed == o.unparsed and \
            self.type == o.type and \
            self.warnings == o.warnings
        
    def __repr__(self):
        sb = ''
        if self.type is not None:
            sb += "[" + str(self.type) + "]"
        if self.uninomial is not None:
            sb += " U:" + self.uninomial
        if self.genus is not None:
            sb += " G:" + self.genus
        if self.infragenericEpithet is not None:
            sb += " IG:" + self.infragenericEpithet
        if self.specificEpithet is not None:
            sb += " S:" + self.specificEpithet
        if self.rank is not None:
            sb += " R:" + str(self.rank)
        if self.infraspecificEpithet is not None:
            sb += " IS:" + self.infraspecificEpithet
        if self.cultivarEpithet is not None:
            sb += " CV:" + self.cultivarEpithet
        if self.strain is not None:
            sb += " STR:" + self.strain
        if self.combinationAuthorship is not None:
            sb += " A:" + str(self.combinationAuthorship)
        if self.basionymAuthorship is not None:
            sb += " BA:" + str(self.basionymAuthorship)
        return sb               
