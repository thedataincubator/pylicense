from mock import MagicMock, patch
import unittest
from pylicense import PyLicense

class Test(unittest.TestCase):
  def setUp(self):
    self.pylicense = PyLicense(False)

  def test_simple_pip_license(self):
    self.pylicense.client.release_data = MagicMock(return_value={ "license": "Apache" })
    self.assertEqual(
      self.pylicense.process_requirements_line("Flask==1.1.1"),
      "Flask==1.1.1  # Apache"
    )

  def test_simple_complex_license(self):
    self.pylicense.client.release_data = MagicMock(
      return_value={ "classifiers": ["Some Junk", "License :: OSI Approved :: BSD License"] }
    )
    self.assertEqual(
      self.pylicense.process_requirements_line("Flask==1.1.1"),
      "Flask==1.1.1  # License :: OSI Approved :: BSD License"
    )

  def test_git_pip_line(self):
    self.pylicense.client.release_data = MagicMock(side_effect=Exception("This method should not be called"))
    self.assertEqual(
      self.pylicense.process_requirements_line("git+https://github.com/thedataincubator/ds30.git"),
      "git+https://github.com/thedataincubator/ds30.git"
    )

  def test_environment_pip_line(self):
    self.pylicense.client.release_data = MagicMock(return_value={ "license": "Apache" })
    self.assertEqual(
      self.pylicense.process_environment_line("  - Flask==1.1.1"),
      "  - Flask==1.1.1  # Apache"
    )

  def test_environment_name_declaration(self):
    self.pylicense.client.release_data = MagicMock(side_effect=Exception("This method should not be called"))
    self.assertEqual(
      self.pylicense.process_environment_line("name: datacourse"),
      "name: datacourse"
    )

  def test_environment_pip_declaration(self):
    self.pylicense.client.release_data = MagicMock(side_effect=Exception("This method should not be called"))
    self.assertEqual(
      self.pylicense.process_environment_line("  - pip:"),
      "  - pip:"
    )

  def test_environment_conda_line(self):
    self.pylicense.client.release_data = MagicMock(return_value={ "license": "Apache" })
    self.assertEqual(
      self.pylicense.process_environment_line("- Flask=1.1.1=py27"),
      "- Flask=1.1.1=py27  # Apache"
    )


if __name__ == "__main__":
  unittest.main()
