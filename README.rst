
===============
pytest-datatest
===============

..
    Project badges for quick reference:

|TravisCI_status| |mit_license|


The development version of `datatest`_'s pytest integration.

Typically, only developers working on datatest's pytest plugin
should install this package. Other users are encouraged to install
just ``datatest``—this plugin comes bundled with it.


Requirements
============

* `pytest`_ (3.3 or newer)
* `datatest`_ (0.9.0 or newer)


Installation
============

For Developers
--------------

Clone the git repositories and use `pip`_ to perform an
editable install from the cloned project directory::

    git clone git@github.com:shawnbrown/datatest.git
    git clone git@github.com:shawnbrown/pytest-datatest.git
    pip install --editable ./datatest
    pip install --no-deps --editable ./pytest-datatest


For Users
---------

Don't install this package—install `datatest`_ instead::

    pip install datatest


For Users With Special Requirements
-----------------------------------

If you aren't a datatest or plugin developer but instead need
bug-fixes or features that are not yet available from the main
datatest project, you can install "pytest-datatest" via pip
from `PyPI`_::

    pip install datatest
    pip install pytest-datatest

And if the version is PyPI isn't new enough for your needs, you can
install the plugin directly from the live GitHub repository (make
sure to check that the build is "passing" before doing this)::

    pip install datatest
    pip install --upgrade https://github.com/shawnbrown/pytest-datatest/archive/master.zip


Usage
=====

When installed, this development version automatically overrides
datatest's bundled pytest integration. If you want to revert back
to the bundled plugin, simply uninstall this version.

To disable the development version (and temporarily enable the
bundled version) use::

    pytest -p no:datatest_devel


To disable both the development *and* bundled versions use::

    pytest -p no:datatest_devel -p no:datatest


Features
========

* Provides a 'mandatory' marker to support incremental testing.
* Provides an '--ignore-mandatory' command line option to override
  the default 'mandatory' behavior.
* Strips the leading "E   " prefix from ``ValidationError`` *differences*
  to help users more easily repurpose parts of the error  message for
  ``allowed.specific(...)`` definitions.


License
=======

Distributed under the terms of the `MIT`_ license, "pytest-datatest" is
free and open source software


Issues
======

If you encounter any problems, please `file an issue`_ along with a
detailed description.


.. |TravisCI_status| image:: https://travis-ci.org/shawnbrown/pytest-datatest.svg?branch=master
    :target: https://travis-ci.org/shawnbrown/pytest-datatest
    :alt: Travis CI Build Status
.. |AppVeyor_status| image:: https://ci.appveyor.com/api/projects/status/github/shawnbrown/pytest-datatest?branch=master
    :target: https://ci.appveyor.com/project/shawnbrown/pytest-datatest/branch/master
    :alt: AppVeyor Build Status
.. |devstatus| image:: https://img.shields.io/pypi/status/pytest-datatest.svg
    :target: https://pypi.python.org/pypi/pytest-datatest
    :alt: Development Status
.. |mit_license| image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: http://opensource.org/licenses/MIT
    :alt: MIT License
.. |pyversions| image:: https://img.shields.io/pypi/pyversions/pytest-datatest.svg
    :target: https://pypi.python.org/pypi/pytest-datatest#supported-versions
    :alt: Supported Python Versions
.. _`datatest`: https://pypi.python.org/pypi/datatest
.. _`file an issue`: https://github.com/shawnbrown/pytest-datatest/issues
.. _`MIT`: http://opensource.org/licenses/MIT
.. _`pip`: https://pypi.python.org/pypi/pip/
.. _`PyPI`: https://pypi.python.org/pypi
.. _`pytest`: https://pypi.python.org/pypi/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
