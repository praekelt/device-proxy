http-request-bouncer
====================

Inspects incoming HTTP requests adds some HTTP headers and bounces it
back to HAProxy for rerouting. Useful for things like load balancing specific
User-Agents to specific HAProxy backends.

Installation
------------

Installation is pegged to the latest GPL version of Wurfl.

Assuming you're living in a virtualenv::

    $ pip install -r requirements.pip
    $ ./get-wurfl-2.1-db.sh

Running
-------

    $ twistd hrb --config config.yaml

