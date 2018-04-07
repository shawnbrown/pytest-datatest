
===============
pytest-datatest
===============

..
    Project badges for quick reference:

|TravisCI_status| |mit_license|


The development version of `datatest`_'s pytest integration.

**WARNING:**

* This is the ``pytest-datatest`` development package. Typically,
  developers should only install this package if they are working
  on the ``pytest-datatest`` plugin itself.

* Users are encouraged to use the automatically provided version
  of this plugin that ships with the main ``datatest`` package
  itself---not this development version.


Features
--------

This simple plugin strips the leading "E   " prefix from lists of
datatest differences when they appear in reported pytest errors. This
lets users copy specific *differences* from the output and paste them
into an *allowance* definition with minimal formatting.


Requirements
------------

* `pytest`_ (3.1.1 or newer)
* `datatest`_ (0.8.3 or newer)


Installation
------------

**For Developers:** Clone the git repository and use pip to perform
an editable install from the cloned project directory::

    git clone git@github.com:shawnbrown/pytest-datatest.git
    pip install --no-deps --editable ./pytest-datatest

**For Users:** Don't install this package---you don't need it.
This plugin is already bundled with `datatest`_ itself.

**For Users With Special Requirements:** If you aren't a datatest or
plugin developer but instead need bug-fixes or features that are not
yet available from the main datatest project, you can install
"pytest-datatest" via `pip`_ from `PyPI`_::

    pip install pytest-datatest

And if the version is PyPI isn't new enough for your needs, you can
install the plugin directly from the live GitHub repository (make
sure to check that the build is "passing" before doing this)::

    pip install --upgrade https://github.com/shawnbrown/pytest-datatest/archive/master.zip


Usage
-----

When installed, this development version automatically overrides
datatest's bundled pytest integration. If you want to revert back
to the bundled plugin, simply uninstall this version.

You can disable this plugin with::

    pytest -p no:datatest_devel


License
-------

Distributed under the terms of the `MIT`_ license, "pytest-datatest" is
free and open source software


Issues
------

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
