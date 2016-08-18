#!/usr/bin/env python
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
#
# Description:
#
#   This script dumps a PostgreSQL-GeoPackage database into a SQLite
#   GeoPackage.
#
#   This script should also get a switch to make a spatial selection as
#   bounding box of the data to be dumped.
#
#------------------------------------------------------------------------------

import sys
import os
import sqlite3
import datetime
import psycopg2
from osgeo import gdal


def create_empyt_gpkg(gpkg_name):
    if os.path.exists("%s.gpkg" % gpkg_name):
        sys.stderr.write(
            "ERROR: SQLite GeoPackage '%s.gpkg' already exists.\n" % gpkg_name
        )
        sys.exit(1)

    gdal.AllRegister()
    drv = gdal.GetDriverByName("GPKG")
    try:
        gpkg = drv.Create("%s.gpkg" % gpkg_name, 0, 0, 1, gdal.GDT_Byte)
        gpkg = None
    except Exception as e:
        sys.stderr.write(
            "ERROR: Cannot create SQLite GeoPackage '%s.gpkg'. "
            "Error message was: '%s'.\n" % (gpkg_name, e.message)
        )
        sys.exit(1)


def record_to_string(record):
    type_str = type('str')
    type_datetime = type(datetime.datetime.now())
    type_buffer = type(buffer(""))
    type_None = type(None)

    values = []
    for item in record:
        if type(item) == type_None:
            values.append('NULL')
        elif type(item) == type_str:
            values.append("'" + item.replace("'", "''") + "'")
        elif type(item) == type_datetime:
            utc = (item - item.utcoffset()).replace(tzinfo=None)
            values.append(
                '"' + utc.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z"'
            )
        #Binary data is handled separately
        elif type(item) == type_buffer:
            values.append("''")
        else:
            values.append(str(item))
    return ','.join(values)


def copy_table(conn_in, conn_out, table_name, constraint=None, has_blob=False):
    with conn_in.cursor() as cursor_in:
        #Check that table exists
        cursor_in.execute(
            "SELECT to_regclass('\"%s\"');"
            % table_name
        )
        if cursor_in.fetchone()[0] is not None:
            cursor_in.execute(
                "SELECT * FROM \"%s\"%s;" % (table_name, "" if constraint is
                                             None else " WHERE " + constraint)
            )
            records = cursor_in.fetchall()

            cursor_out = conn_out.cursor()
            for record in records:
                values = record_to_string(record)
                try:
                    cursor_out.execute(
                        "INSERT INTO \"%s\" VALUES (%s);" %
                        (table_name, values)
                    )
                    #If binary data present:
                    if has_blob:
                        cursor_out.execute(
                            "UPDATE \"%s\" SET tile_data = ? WHERE id = %s;" %
                            (table_name, record[0]),
                            (sqlite3.Binary(str(record[4])),)
                        )
                except Exception as e:
                    conn_out.rollback()
                    sys.stderr.write(
                        "ERROR: Input doesn't seem to be a valid GeoPackage. "
                        "Error message was: '%s'.\n" % e.message
                    )
                    sys.exit(1)


def dump_gpkg(pg_connection_string, gpkg_name):
    with psycopg2.connect(pg_connection_string) as conn_in:
        with sqlite3.connect("%s.gpkg" % gpkg_name) as conn_out:
            #Check that GeoPackage exists
            with conn_in.cursor() as cursor_in:
                cursor_in.execute(
                    "SELECT to_regclass('\"%s\"');"
                    % gpkg_name
                )
                if cursor_in.fetchone()[0] is None:
                    sys.stderr.write(
                        "ERROR: GeoPackage '%s' not found in PostgreSQL.\n" %
                        gpkg_name
                    )
                    sys.exit(1)

            copy_table(conn_in, conn_out, "gpkg_spatial_ref_sys",
                       "srs_id NOT IN ('-1','0','4326')")
            copy_table(conn_in, conn_out, "gpkg_contents",
                       "table_name = '%s'" % gpkg_name)
            copy_table(conn_in, conn_out, "gpkg_tile_matrix_set",
                       "table_name = '%s'" % gpkg_name)
            copy_table(conn_in, conn_out, "gpkg_tile_matrix",
                       "table_name = '%s'" % gpkg_name)
            copy_table(conn_in, conn_out, "gpkg_metadata_reference",
                       "table_name = '%s'" % gpkg_name)
            copy_table(conn_in, conn_out, "gpkg_metadata",
                       "id IN (SELECT md_file_id FROM gpkg_metadata_reference "
                       "WHERE table_name = '%s')" % gpkg_name)
            copy_table(conn_in, conn_out, gpkg_name, has_blob=True)


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        sys.stderr.write(
            "ERROR: Please provide the connection string for PostgreSQL as "
            "well as the GeoPackage name. The GeoPackage name is used to "
            "determine the table in which the tile data is stored as well as "
            "for the filename of the SQLite GeoPackage to generate.\n"
        )
        sys.exit(1)

    pg_connection_string = sys.argv[1]
    gpkg_name = sys.argv[2]

    create_empyt_gpkg(gpkg_name)
    dump_gpkg(pg_connection_string, gpkg_name)

    sys.stdout.write(
        "GeoPackage '%s' successfully exported\n" % gpkg_name
    )
    sys.exit(0)
