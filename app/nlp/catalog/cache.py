class CatalogCache:
    def __init__(self):
        self._catalog=None
    
    def set_catalog(self,catalog):
        self._catalog=catalog
    
    def get_catalog(self):
        return self._catalog
    
    def get_triggers(self):
        return self._catalog["triggers"]

catalog_cache = CatalogCache()