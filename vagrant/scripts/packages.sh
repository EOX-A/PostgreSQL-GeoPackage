#!/bin/sh -e

echo "Package installation provision step"

aptitude install -y gdal-bin python-gdal postgis python-psycopg2 sqlite3
