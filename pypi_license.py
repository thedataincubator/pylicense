import xmlrpclib

def regularize_license(license):
  if not license:
    return None

  license = license.strip()
  if license == "UNKNOWN":
    return None
  elif "\n" in license:
    return None
  else:
    return license

def get_license(package, version):
  client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
  info = client.release_data(package, version)
  license = regularize_license(info.get('license'))
  if license:
    return license.rstrip()

  classifiers = info.get('classifiers')
  if not classifiers:
    return None

  for classifier in classifiers:
    if classifier.startswith("License"):
      return classifier.rstrip()

  return None

if __name__ == '__main__':
  import sys

  with open(sys.argv[1]) as fh:
    for line in fh:
      dependency = line.split('#')[0].strip()
      if dependency and not dependency.startswith('git+https://github.com'):
        try:
          package, version = dependency.split('==')
          license = get_license(package, version)
          if license:
            print line.rstrip() + "  # " + license
          else:
            print line.rstrip()
        except ValueError:  # cannot split
          print line.rstrip()
      else:
        print line.rstrip()

