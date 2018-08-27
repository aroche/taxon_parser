from .util import nameformatter


"""
    Authorship of the name (recombination) or basionym
    including authors, ex authors and the year
    but no in authors which are regarded as part of the publishedIn citation.

    The parsed authorship for basionyms does not include brackets.
    Note that the sanctioning author for fungi is part of the ParsedName class.
"""


class Authorship:
    def __init__(self):
        # list of authors
        self.__authors = []
        
        # list of authors excluding ex-authors
        self.__exAuthors = []
        
        # The year the combination or basionym was first published, usually the same as the publishedIn reference.
        # It is used for sorting names and ought to be populated even for botanical names which do not use it in the complete authorship string.
        self.__year = None     
        
    @property
    def authors(self):
        return self.__authors
    
    @authors.setter
    def authors(self, authors):
        self.__authors = authors
        
    @property
    def exAuthors(self):
        return self.__exAuthors
    
    @exAuthors.setter
    def exAuthors(self, exAuthors):
        self.__exAuthors = exAuthors
        
    @property
    def year(self):
        return self.__year
    
    @year.setter
    def year(self, year):
        self.__year = year
        
    def isEmpty(self):
        return len(self.authors) == 0 and self.year is None
    
    def exists(self):
        return (len(self.authors) > 0) or (self.year is not None)
    
    def __eq__(self, obj):
        if obj is None or self.__class__ != obj.__class__:
            return False
        return self.authors == obj.authors and self.exAuthors == obj.exAuthors and self.year == obj.year
    
    def __repr__(self):
        if self.exists():
            return nameformatter.appendAuthorshipFromAuthor(self, True)
        else:
            return '<unknown>'

