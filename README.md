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
* ParsedName.strain**

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

