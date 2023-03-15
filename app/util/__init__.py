
import pkgutil, warnings

def get_processors(package):
  keyword = "processors"
  Processors = {}
  for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
      mod = __import__("{}.{}".format(package.__name__, modname), fromlist=[keyword])
      ps = getattr(mod, keyword)
      for p in ps: #go through all processors from the module
        link = p.link
        if link in Processors:
            warnings.warn("Warning: duplicate links")
        else:
            Processors[link] = p
  return Processors