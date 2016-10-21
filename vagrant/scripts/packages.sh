#!/bin/sh -e

echo "Package installation provision step"

aptitude install -y gdal-bin python-gdal postgis python-psycopg2 sqlite3 postgresql postgresql-common postgresql-client-common postgresql-9.5-postgis-2.2 postgresql-9.5-postgis-scripts
