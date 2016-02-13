import xmlrpclib

class PyLicense(object):
  @classmethod
  def parse_conda_licenses(cls):
    # make these imports local so we do not need to install libraries if this function is not run
    from bs4 import BeautifulSoup
    import requests

    page = requests.get("http://docs.continuum.io/anaconda/pkg-docs")
    soup = BeautifulSoup(page.text)
    rows = soup.select("table.docutils tr")
    table = [row.select('td') for row in rows]
    return { row[0].select('a')[0].text: row[2].text.split('/')[-1].strip()
                for row in table if row and len(row) == 4 }

  def __init__(self, environment):
    self.environment = environment
    if environment:
      self.conda_licenses = self.parse_conda_licenses()

  @classmethod
  def regularize_license(cls, license):
    if not license:
      return None

    license = license.strip()
    if license == "UNKNOWN":
      return None
    elif "\n" in license:
      return None
    else:
      return license

  @classmethod
  def _get_license(cls, package, version):
    client = xmlrpclib.ServerProxy('http://pypi.python.org/pypi')
    info = client.release_data(package, version)
    if not info:
      info = client.release_data(package.title(), version)
    license = cls.regularize_license(info.get('license'))
    if license:
      return license.rstrip()

    classifiers = info.get('classifiers')
    if not classifiers:
      return None

    for classifier in classifiers:
      if classifier.startswith("License"):
        return classifier.rstrip()

    return None

  @classmethod
  def _maybe_license_comment(cls, line, license):
    if not license:
      return ""

    if line.endswith(license):
      return ""

    if license.startswith("  # "):
      return license

    return "  # " + license

  @classmethod
  def _get_dependency_license(cls, line, dep_sep, num_positions):
    dependency = line.split('#')[0].strip()
    if not dependency or dependency.startswith('git+https://github.com'):
      return ""

    dep_array = dependency.split(dep_sep)
    if len(dep_array) != num_positions:
      return ""

    package, version = dep_array[:2]
    license = cls._get_license(package, version)

    return cls._maybe_license_comment(line, license)

  @classmethod
  def _get_pip_license(cls, line):
    return cls._get_dependency_license(line, '==', 2)

  def _get_conda_license(self, line):
    license = self._get_dependency_license(line, '=', 3)

    if not license:
      license = self.conda_licenses.get(line.split("=")[0], '')

    return self._maybe_license_comment(line, license)

  _CONDA_PREFIX = '- '
  _PIP_PREFIX = '  - '
  _PIP_LINE = ' - pip:'

  def process_environment_line(self, line):
    line = line.rstrip()
    if line.startswith(self._CONDA_PREFIX):
      if line == self._PIP_LINE:
        return self._PIP_LINE
      return line + self._get_conda_license(line[len(self._CONDA_PREFIX):])
    elif line.startswith(self._PIP_PREFIX):
      return line + self._get_pip_license(line[len(self._PIP_PREFIX):])
    else:
      return line

  @classmethod
  def process_pip_line(cls, line):
    return line.rstrip() + cls._get_pip_license(line)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Adds dependencies to dependency file (i.e. requirements.txt or environment.yml)')
  parser.add_argument('-e', '--environment', action='store_true', default=False, help='use environment.yml (requirements.txt is default)')
  parser.add_argument('-s', '--stdout', action='store_true', default=False, help='write output to stdout (default rewrites input file)')
  parser.add_argument('file', help='dependency file')
  args = parser.parse_args()

  output = []

  with open(args.file) as fh:
    pylicense = PyLicense(environment=args.environment)
    for line in fh:
      if args.environment:
        output += [pylicense.process_environment_line(line)]
      else:
        output += [pylicense.process_pip_line(line)]

  if args.stdout:
    print "\n".join(output)
  else:
    # must open file twice to rewrite it
    with open(sys.argv[1], "w") as fh:
      fh.write("\n".join(output))

