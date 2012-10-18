dev-proxy
====================

Inspects incoming HTTP requests adds some HTTP headers and proxies upstream.
Has ability to add extra cookies for HTTP responses being sent back to the
client.

Installation
------------

Installation is pegged to the latest GPL version of Wurfl.

Assuming you're living in a virtualenv::

    $ pip install -r requirements.pip
    $ ./get-wurfl-2.1-db.sh

Running
-------

    $ twistd dev-proxy --config config.yaml

