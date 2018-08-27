from . import unicodeutils
from ..namepart import NamePart
from ..rank import Rank, NomCode


HYBRID_MARKER = '×'
NOTHO_PREFIX = "notho"
AUTHORSHIP_JOINER = ", "

     
def canonical(n):
    """
        A full scientific name with authorship from the individual properties in its canonical form.
        Autonyms are rendered without authorship and subspecies are using the subsp rank marker
        unless a name is assigned to the zoological code.
    """
    # TODO: show authorship for zoological autonyms?
    # TODO: how can we best remove subsp from zoological names?
    # https://github.com/gbif/portal-feedback/issues/640
    return buildName(n, True, True, True, True, False, True, False, True, False, False, False, True, True)


def canonicalWithoutAuthorship(n):
    """
    A full scientific name just as canonicalName, but without any authorship.
    """
    return buildName(n, True, True, False, True, False, True, False, True, False, False, False, True, True)



def canonicalMinimal(n):
    """
        A minimal canonical name with nothing else but the 3 main name parts (genus, species, infraspecific).
        No rank or hybrid markers and no authorship, cultivar or strain information is rendered.
        Infrageneric names are represented without a leading genus.
        Unicode characters will be replaced by their matching ASCII characters.

        For example:
            Abies alba
            Abies alba alpina
            Bracteata
    """
    return buildName(n, False, False, False, False, False, True, True, False, False, False, False, False, False)



def canonicalComplete(n):
    """
        Assembles a full name with all details including non code compliant, informal remarks.
    """
    return buildName(n, True, True, True, True, True, True, False, True, True, True, True, True, True)


def authorshipComplete(n):
    """
        The full concatenated authorship for parsed names including the sanctioning author.
    """
    sb = appendAuthorshipFromParsedName(n)
    if len(sb) == 0:
        return None
    return sb


def authorString(authors, inclYear):
    """
        Renders the authors of an authorship including ex authors, optionally with the year included.
    """
    sb = appendAuthorshipFromAuthor(authors, inclYear)
    if len(sb) == 0:
        return
    return sb


def buildName(n, hybridMarker, rankMarker, authorship, genusForinfrageneric, infrageneric, decomposition, asciiOnly,
    showIndet, nomNote, remarks, showSensu, showCultivar, showStrain):
    """
        build a name controlling all available flags for name parts to be included in the resulting name.
        
        :param hybridMarker    include the hybrid marker with the name if existing
        :param rankMarker      include the infraspecific or infrageneric rank marker with the name if existing
        :param authorship      include the names authorship (authorteam and year)
        :param genusForinfrageneric show the genus for infrageneric names
        :param infrageneric    include the infrageneric name in brackets for species or infraspecies
        :param decomposition   decompose unicode ligatures into their corresponding ascii ones, e.g. æ beomes ae
        :param asciiOnly       transform unicode letters into their corresponding ascii ones, e.g. ø beomes o and ü u
        :param showIndet       if True include the rank marker for incomplete determinations, for example Puma spec.
        :param nomNote         include nomenclatural notes
        :param remarks         include informal remarks
    """
    sb = ''

    if n.isCandidatus():
        sb += "\"Candidatus "
    

    if n.uninomial is not None:
        # higher rank names being just a uninomial!
        if hybridMarker and NamePart.GENERIC == n.notho:
            sb += HYBRID_MARKER + " "
    
        sb += n.uninomial

    else:
        # bi- or trinomials or infrageneric names
        if n.infragenericEpithet is not None:
            if (isUnknown(n.rank) and n.specificEpithet is None) or (n.rank is not None and n.rank.isInfragenericStrictly()):
                showInfraGen = True
                # the infrageneric is the terminal rank. Always show it and wrap it with its genus if requested
                if n.genus is not None and genusForinfrageneric:
                    sb += appendGenus(n, hybridMarker) + " "
                    # we show zoological infragenerics in brackets,
                    # but use rank markers for botanical names (unless its no defined rank)
                    if NomCode.ZOOLOGICAL == n.code:
                        sb += "("
                        if hybridMarker and NamePart.INFRAGENERIC == n.notho:
                            sb += HYBRID_MARKER + ' '
                            
                        sb += n.infragenericEpithet + ")"
                        showInfraGen = False
            
                if showInfraGen:
                    if rankMarker:
                        # If we know the rank we use explicit rank markers
                        # this is how botanical infrageneric names are formed, see http://www.iapt-taxon.org/nomen/main.php?page=art21
                        s = appendRankMarker(n.rank, hybridMarker and NamePart.INFRAGENERIC == n.notho)
                        if s:
                            sb += s + ' '
                    
                    sb += n.infragenericEpithet

            else:
                if n.genus is not None:
                    sb += appendGenus(n, hybridMarker)
                
                if infrageneric:
                    # additional subgenus shown for binomial. Always shown in brackets
                    sb += " (" + n.infragenericEpithet + ")"  
        
        elif n.genus is not None:
            sb += appendGenus(n, hybridMarker)
    
        if n.specificEpithet is None:
            if showIndet and n.genus is not None and n.cultivarEpithet is None:
                if Rank.SPECIES == n.rank:
                    # no species epithet given, but rank=species. Indetermined species!
                    sb += " spec."
                    authorship = False

                elif n.rank is not None and n.rank.isInfraspecific():
                    # no species epithet given, but rank below species. Indetermined!
                    sb += appendInfraspecific(n, hybridMarker, rankMarker, True)
                    authorship = False
        
        else:
            # species part
            sb += ' '
            if hybridMarker and NamePart.SPECIFIC == n.notho:
                sb += HYBRID_MARKER + " "
            
            sb += n.specificEpithet

            if n.infraspecificEpithet is None:
                # Indetermined infraspecies? Only show indet cultivar marker if no cultivar epithet exists
                if showIndet \
                    and n.rank is not None \
                    and n.rank.isInfraspecific() \
                    and (NomCode.CULTIVARS != n.rank.isRestrictedToCode() or n.cultivarEpithet is None):
                    # no infraspecific epitheton given, but rank below species. Indetermined!
                    sb += ' ' + n.rank.value
                    authorship = False
        

            else:
                # infraspecific part
                sb += appendInfraspecific(n, hybridMarker, rankMarker, False)
                # non autonym authorship ?
                if n.isAutonym():
                    authorship = False

    # closing quotes for Candidatus names
    if n.isCandidatus():
        sb += "\""

    # uninomial, genus, infragen, species or infraspecies authorship
    if authorship and n.hasAuthorship():
        sb += " " + appendAuthorshipFromParsedName(n)    

    # add strain name
    if showStrain and n.strain is not None:
        sb += " " + n.strain

    # add cultivar name
    if showCultivar and n.cultivarEpithet is not None:
        if Rank.CULTIVAR_GROUP == n.rank:
            sb += " " + n.cultivarEpithet + " Group"

        elif Rank.GREX == n.rank:
            sb += " " + n.cultivarEpithet + " gx"
        
        else:
            sb += " '" + n.cultivarEpithet + "'"    

    # add sensu/sec reference
    if showSensu and n.getTaxonomicNote() is not None:
        if sb != '':
            sb += " "
        sb += n.taxonomicNote   

    # add nom status
    if nomNote and n.nomenclaturalNotes is not None:
        if sb != '':
            sb += ', '
        sb += n.nomenclaturalNotes
    
    # add remarks
    if remarks and n.remarks is not None:
        if sb != '':
            sb += ' '
        sb += "[" + n.remarks + "]"    

    # final char transformations
    name = sb.strip()
    if decomposition:
        name = unicodeutils.decompose(name)
    
    if asciiOnly:
        name = unicodeutils.ascii(name)
    
    if name == '':
        return None
    return name


def appendInfraspecific(n, hybridMarker, rankMarker, forceRankMarker):
    # infraspecific part
    sb = ' '
    if hybridMarker and NamePart.INFRASPECIFIC == n.notho:
        if rankMarker and n.rank is not None and isInfraspecificMarker(n.rank):
            sb += "notho"
        else:
            sb += HYBRID_MARKER
            sb += " "    
    
    # hide subsp. from zoological names
    if forceRankMarker or rankMarker and (not isZoo(n.code) or Rank.SUBSPECIES != n.rank):
        s = appendRankMarker(n.rank, False,  isInfraspecificMarker)
        if s and n.infraspecificEpithet is not None:
            sb += s + ' '
    
    if n.infraspecificEpithet is not None:
        sb += n.infraspecificEpithet
    
    return sb


def isZoo(code):
    return code is not None and code == NomCode.ZOOLOGICAL


def isUnknown(r):
    return r is None or r.otherOrUnranked()


def isInfragenericMarker(r):
    return r is not None and r.isInfrageneric() and not r.isUncomparable()


def isInfraspecificMarker(r):
    return r.isInfraspecific() and not r.isUncomparable()


def appendRankMarker(rank, nothoPrefix, ifRank=None):
    """
        :return True if rank marker was added
    """
    sb = ''
    if rank is not None and (ifRank is None or ifRank(rank)):
        if nothoPrefix:
            sb += NOTHO_PREFIX
    
        sb += rank.value
        return sb
    
    return False


def appendGenus(n, hybridMarker):
    sb = ''
    if hybridMarker and NamePart.GENERIC == n.notho:
        sb += HYBRID_MARKER + " "
    
    sb += n.genus
    return sb


def joinAuthors(authors, useEtAl=True):
    if useEtAl and len(authors) > 2:
        return AUTHORSHIP_JOINER.join(authors[:2]) + " et al."

    elif len(authors) > 1:
        return AUTHORSHIP_JOINER.join(authors[:-1]) + " & " + authors[-1]
    else:
        return AUTHORSHIP_JOINER.join(authors)


def appendAuthorshipFromAuthor(auth, includeYear):
    """
        Renders the authorship with ex authors and year
        :param sb StringBuilder to append to
    """
    sb = ''
    if auth.exists():
        authorsAppended = False
        if len(auth.exAuthors) > 0:
            sb += joinAuthors(auth.exAuthors, False) + " ex "
            authorsAppended = True
    
        if len(auth.authors) > 0:
            sb += joinAuthors(auth.authors, False)
            authorsAppended = True
        
        if auth.year is not None and includeYear:
            if authorsAppended:
                sb += ", "
            sb += auth.year
                    
    return sb    


def appendAuthorshipFromParsedName(n):
    sb = ''
    if n.basionymAuthorship.exists():
        sb += "(" + appendAuthorshipFromAuthor(n.basionymAuthorship, True) + ")"
    
    if n.combinationAuthorship.exists():
        sb += appendAuthorshipFromAuthor(n.combinationAuthorship, True)
        # Render sanctioning author via colon:
        # http://www.iapt-taxon.org/nomen/main.php?page=r50E
        # TODO: remove rendering of sanctioning author according to Paul Kirk!
        if n.sanctioningAuthor is not None:
            sb += " : "
            sb += n.sanctioningAuthor
            
    return sb
