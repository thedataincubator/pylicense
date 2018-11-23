import os
import xmlrpclib


class CondaLicenseDownloader(object):
  """
  License data is available on anaconda.com for all packages.
  """
  LICENSE_URLS = {
    "py2": "https://docs.anaconda.com/anaconda/packages/old-pkg-lists/4.3.1/py27/",
    "py3": "https://docs.anaconda.com/anaconda/packages/old-pkg-lists/4.3.1/py35/"
  }

  @classmethod
  def get_conda_licenses(cls, environment):
    """
    Download and parse continuum webpage with license data
    """

    # make these imports local so we do not need to install libraries if this function is not run
    from bs4 import BeautifulSoup
    import requests

    url = cls.LICENSE_URLS.get(environment)
    page = requests.get(url)
    soup = BeautifulSoup(page.text, "lxml")
    rows = soup.select("table.docutils tr")
    table = [row.select('td') for row in rows]
    return {row[0].select('a')[0].text: row[2].text.split('/')[-1].strip()
            for row in table if row and len(row) == 4}

class PyLicense(object):
  def __init__(self, environment):
    self.environment = environment
    self.client = xmlrpclib.ServerProxy('https://pypi.python.org/pypi')
    if environment:
      self.conda_licenses = CondaLicenseDownloader.get_conda_licenses(environment)

  @classmethod
  def _regularize_license(cls, license):
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
  def _maybe_license_comment(cls, line, license):
    if not license:
      return ""

    if line.endswith(license):
      return ""

    if license.startswith("  # "):
      return license

    return "  # " + license

  def _get_license(self, package, version):
    info = self.client.release_data(package, version)
    if not info:
      info = self.client.release_data(package.title(), version)
    license = self._regularize_license(info.get('license'))
    if license:
      return license.rstrip()

    classifiers = info.get('classifiers')
    if not classifiers:
      return None

    for classifier in classifiers:
      if classifier.startswith("License"):
        return classifier.rstrip()

    return None

  def _get_dependency_license(self, line, dep_sep, num_positions):
    dependency = line.split('#')[0].strip()
    if not dependency or dependency.startswith('git+https://github.com'):
      return ""

    dep_array = dependency.split(dep_sep)
    if len(dep_array) != num_positions:
      return ""

    package, version = dep_array[:2]
    license = self._get_license(package, version)

    return self._maybe_license_comment(line, license)

  def _get_pip_license(self, line):
    return self._get_dependency_license(line, '==', 2)

  def _get_conda_license(self, line):
    license = self._get_dependency_license(line, '=', 3)

    if not license:
      license = self.conda_licenses.get(line.split("=")[0], '')

    return self._maybe_license_comment(line, license)

  _CONDA_PREFIX = '- '
  _PIP_PREFIX = '  - '
  _PIP_LINE = ' - pip:'

  def process_environment_line(self, line):
    """
    Processes a line from environment.yml
    """
    line = line.rstrip()
    if line.startswith(self._CONDA_PREFIX):
      if line == self._PIP_LINE:
        return self._PIP_LINE
      return line + self._get_conda_license(line[len(self._CONDA_PREFIX):])
    elif line.startswith(self._PIP_PREFIX):
      return line + self._get_pip_license(line[len(self._PIP_PREFIX):])
    else:
      return line

  def process_requirements_line(self, line):
    """
    Processes a line from requirements.txt
    """
    return line.rstrip() + self._get_pip_license(line)

  def process_stream(self, stream):
    """
    Processes lines from stream
    """
    for line in stream:
      if args.environment:
        yield self.process_environment_line(line)
      else:
        yield self.process_requirements_line(line)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser(description='Adds license information to dependency file (i.e. requirements.txt or environment.yml) as comment')
  parser.add_argument('-e', '--environment', default=False, choices=("py2", "py3"), help="specify value for environment.yml, (requirements.txt is default)")
  parser.add_argument('-s', '--stdout', action='store_true', default=False, help='print new dependency file to stdout (default rewrites input file)')
  parser.add_argument('file', help='dependency file')
  args = parser.parse_args()

  with open(os.path.expanduser(args.file)) as stream:
    pylicense = PyLicense(environment=args.environment)
    output = [o for o in pylicense.process_stream(stream)]

  # must open file to rewrite it
  if args.stdout:
    print "\n".join(output)
  else:
    with open(args.file, "w") as fh:
      fh.write("\n".join(output))

