# Taxon parser

This library is a pure Python adaptation of the GBIF Java [name-parser library](https://github.com/gbif/name-parser).

It is used to parse any taxonomic name into its elementary components (genus, species, authors...)

It returns a ParsedName object containing the name parts and the original parsed string.

## Installation
```
pip install taxon_parser
```

## Requirements

This library works for Python version 3.4 or higher

The only external package dependancy is the *regex* package for handling advanced regular expressions.


## Usage

basic usage:

```python
from taxon_parser import TaxonParser, UnparsableNameException

parser = TaxonParser("Abies pectinata mill.")
try:
    parsed_name = parser.parse()
    print(parsed_name)
except UnparsableNameException as e:
    print("this name does not seem to be a valid taxon name: \n" + e )
```

For any name that can not be parsed, an UnparsableNameException is thrown.


### ParsedName objects

Results of the parsing are `ParsedName` objects. These have the following attributes and functions:

* ParsedName.**combinationAuthorship**: Authorship object with years of the name, but excluding any basionym authorship.
For binomials the combination authors.

* ParsedName.**basionymAuthorship**: basionym Authorship object with years of the name

* ParsedName.**sanctioningAuthor**: The sanctioning author for sanctioned fungal names. Fr. or Pers.

* ParsedName.**rank**: Rank of the name from enumeration see the [rank.py](taxon_parser/name_parser_api/api/rank.py) for description of possible ranks

* ParsedName.**uninomial**: Represents the monomial for genus, families or names at higher ranks which do not have further epithets.

* ParsedName.**genus**: The genus part of an infrageneric, bi- or trinomial name. Not used for standalone genus names which are represented as uninomials.

Infrageneric epithets:

* ParsedName.**infragenericEpithet**
* ParsedName.**specificEpithet**
* ParsedName.**infraspecificEpithet**
* ParsedName.**cultivarEpithet**
* ParsedName.**strain**

* ParsedName.**candidatus**: A bacterial candidate name. Candidatus is a provisional status for incompletely described procaryotes
(e.g. that cannot be maintained in a Bacteriology Culture Collection)
which was published in the January 1995.
The category Candidatus is not covered by the Rules of the Bacteriological Code but is a taxonomic assignment.
The names included in the category Candidatus are usually written as follows:
*Candidatus* (in italics), the subsequent name(s) in roman type and the entire name in quotation marks. For example, "*Candidatus* Phytoplasma", "*Candidatus* Phytoplasma allocasuarinae".
See http://www.bacterio.net/-candidatus.html and https://en.wikipedia.org/wiki/Candidatus

* ParsedName.**notho**: The part of the named hybrid which is considered a hybrid

* ParsedName.**taxonomicNotes**: Nomenclatural status remarks of the name.

* ParsedName.**remarks**: Any informal remarks found in the name

* ParsedName.**unparsed**: Any additional unparsed string found at the end of the name. Only ever set when state=PARTIAL

* ParsedName.**type**: The kind of name classified in broad catagories based on their syntactical structure

* ParsedName.**doubtful**: Indicates some doubts that this is a name of the given type.
Usually indicates the existance of unusual characters not normally found in scientific names.

* ParsedName.**state**: Indicates if the full name has been parsed

* ParsedName.**getTerminalEpithet()**: returns the terminal epithet. Infraspecific epithet if existing, the species epithet or null

* ParsedName.**hasName()**: return `True` if the parsed name has non null name properties or a scientific name. Remarks will not count as a name

* ParsedName.**hasAuthorship()**: return `True` if any kind of authorship exists

* ParsedName.**isBinomial()**: return `True` if the name is a bi- or trinomial with at least a genus and species epithet given.

* ParsedName.**isTrinomial()**: return true if the name is a trinomial with at least a genus, species and infraspecific epithet given.

* ParsedName.**isIndetermined()**: Checks if a parsed name is missing final epithets compared to what is indicated by its rank.
Returns `True` if the name is not fully determined.

* ParsedName.**isIncomplete()**: returns `True` if some "higher" epithet of a name is missing, e.g. the genus in case of a species.

* ParsedName.**isAbbreviated()**: returns `True` if the name contains an abbreviated genus or uninomial.

* ParsedName.**canonicalName()**: A full scientific name with authorship from the individual properties in its canonical form.
Autonyms are rendered without authorship and subspecies are using the subsp rank marker
unless a name is assigned to the zoological code.

* ParsedName.**canonicalName()**: A full scientific name just as canonicalName, but without any authorship.

* ParsedName.**canonicalComplete()**: Assembles a full name with all details including non code compliant, informal remarks.

* ParsedName.**nameMinimal()**:  returns a minimal canonical name with nothing else but the 3 main name parts (genus, species, infraspecific).
No rank or hybrid markers and no authorship, cultivar or strain information is rendered.
Infrageneric names are represented without a leading genus.
Unicode characters will be replaced by their matching ASCII characters.
For example:
    * Abies alba
    * Abies alba alpina
    * Bracteata

* ParsedName.**authorshipComplete()**: returns the full concatenated authorship for parsed names including the sanctioning author.


