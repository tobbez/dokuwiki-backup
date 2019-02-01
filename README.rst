dokuwiki_backup
===============

Purpose: produce backups that can be publicly redistributed as-is.

This is achieved by not including user accounts in the dump, and by filtering
all IP addresses.

Output from a run is a single xz-compressed tar archives.

The file name is constructed by joining the following components by dashes (-):

* Custom prefix (optional)
* Basename of the dokuwiki root
* UTC timestamp: %Y-%m-%d_%H-%M-%SZ (e.g. 2019-01-13_01-23-45Z)

and appending '.tar.xz'.

Usage
-----

.. code::

  usage: dokuwiki_backup.py [-h] --output-dir OUTPUT_DIR
                            [--name-prefix NAME_PREFIX] [--keep-users]
                            [--keep-ips]
                            dokuwiki_root

  positional arguments:
    dokuwiki_root         Path to the dokuwiki directory that should be backed
                          up.

  optional arguments:
    -h, --help            show this help message and exit
    --output-dir OUTPUT_DIR, -o OUTPUT_DIR
                          Directory where the backup archive should be stored.
                          It is passed through strftime before it is used.
                          Created if it does not exist.
    --name-prefix NAME_PREFIX, -p NAME_PREFIX
                          Optional prefix to prepend to the output archive name.
    --keep-users          Include the user file in the backup. The default is to
                          exclude it.
    --keep-ips            Keep IP addresses in the backup. The default is to
                          strip them.

Dependencies
------------

* Python 3
* `phpserialize <https://github.com/mitsuhiko/phpserialize>`_ (`PyPI <https://pypi.org/project/phpserialize/>`_) for Python

License
-------

ISC. See the header in dokuwiki_backup.py for the full license text.
