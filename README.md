<!--
#------------------------------------------------------------------------------
#
# Project: PostgreSQL-GeoPackage
# Authors: Stephan Meissl <stephan.meissl@eox.at>
#
#------------------------------------------------------------------------------
# Copyright (c) 2016 EOX IT Services GmbH
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#------------------------------------------------------------------------------
-->

# PostgreSQL-GeoPackage

This repository holds scripts used to evaluated the suitability of PostgreSQL
to serve as alternative to SQLite for a container of raster tiles as specified
in the [GeoPackage standard [OGC 12-128r11]](http://www.geopackage.org).

## Usage

Follow the [Vagrant instructions](/tree/master/vagrant) for a clean environment
and connect to it:

```sh
vagrant ssh
cd PostgreSQL-GeoPackage/
```

Create a PostgreSQL database and load the GeoPackage schema into the
PostgreSQL-GeoPackage:

```sh
createdb -E UTF8 -U gpkg gpkg
psql -U gpkg gpkg -f gpkg-pg_init.sql
```

Load a SQLite GeoPackage into the PostgreSQL-GeoPackage, dump it again, and
validate the result of the round-trip:

```sh
./gpkg-pg_loadpkg.py Sample-GeoPackage_Sentinel-2_Vienna_Austria.gpkg "dbname='gpkg' user='gpkg'"
sqlite3 Sample-GeoPackage_Sentinel-2_Vienna_Austria.gpkg .dump > before
rm Sample-GeoPackage_Sentinel-2_Vienna_Austria.gpkg
./gpkg-pg_dump.py "dbname='gpkg' user='gpkg'" Sample-GeoPackage_Sentinel-2_Vienna_Austria
sqlite3 Sample-GeoPackage_Sentinel-2_Vienna_Austria.gpkg .dump > after
diff before after
```

Finally, drop the PostgreSQL-GeoPackage:

```sh
./gpkg-pg_drop.py "dbname='gpkg' user='gpkg'" Sample-GeoPackage_Sentinel-2_Vienna_Austria
```

## Acknowledgment

The sample SQLite GeoPackage was created from
[Sentinel-2](https://sentinel.esa.int/web/sentinel/missions/sentinel-2) data
using [GDAL](http://gdal.org).

Legal notice: [Contains modified Copernicus Sentinel data [2016]](https://scihub.copernicus.eu/twiki/pub/SciHubWebPortal/TermsConditions/Sentinel_Data_Legal_Notice.pdf)
