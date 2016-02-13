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
  import argparse

  parser = argparse.ArgumentParser(description='Adds dependencies to dependency file (i.e. requirements.txt or environment.yml)')
  parser.add_argument('-e', '--environment', action='store_true', default=False, help='use environment.yml (requirements.txt is default)')
  parser.add_argument('file', help='dependency file')

  output = []

  with open(sys.argv[1]) as fh:
    for line in fh:
      line = line.rstrip()
      dependency = line.split('#')[0].strip()
      if dependency and not dependency.startswith('git+https://github.com'):
        try:
          package, version = dependency.split('==')
          license = get_license(package, version)
          if license:
            license_comment = "  # " + license
            if line.endswith(license_comment):
              output += [line]
            else:
              output += [line.rstrip() + license_comment]
          else:
            output += [line]
        except ValueError:  # cannot split
          output += [line]
      else:
        output += [line]

  with open(sys.argv[1], "w") as fh:
    fh.write("\n".join(output))

