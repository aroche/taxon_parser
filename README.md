# Taxon parser

This library is a pure Python adaptation of the GBIF Java [name-parser library](https://github.com/gbif/name-parser).

It is used to parse any taxonomic name into its elementary components (genus, species, authors...)

It returns a ParsedName object containing the name parts and the original parsed string.

## Usage
```python
from taxon_parser import TaxonParser, UnparsableNameException

parser = TaxonParser("Abies pectinata mill.")
try:
    parsed_name = parser.parse()
    print(parsed_name)
except UnparsableNameException:
    print("this name does not seem to be a valid taxon name")
```

