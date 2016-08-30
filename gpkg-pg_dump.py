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
import argparse
import sqlite3
import datetime
import psycopg2
from osgeo import gdal
from osgeo import osr


def create_gpkg(
    gpkg_name, proj_string, size=(1, 1), geotransform=[0, 1, 0, 0, 0, -1],
    creation_options=None
):
    if os.path.exists("%s.gpkg" % gpkg_name):
        sys.stderr.write(
            "ERROR: SQLite GeoPackage '%s.gpkg' already exists.\n" % gpkg_name
        )
        sys.exit(1)

    gdal.AllRegister()
    drv = gdal.GetDriverByName("GPKG")
    try:
        gpkg = drv.Create(
            "%s.gpkg" % gpkg_name, size[0], size[1], 1, gdal.GDT_Byte,
            creation_options
        )

        proj = osr.SpatialReference()
        proj.SetWellKnownGeogCS(proj_string)
        gpkg.SetProjection(proj.ExportToWkt())

        gpkg.SetGeoTransform(geotransform)
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


def dump_gpkg(pg_connection_string, gpkg_name, srcwin=None):
    with psycopg2.connect(pg_connection_string) as conn_in:
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

            #get projection, geotransform, and size
            cursor_in.execute(
                "SELECT srs.organization, srs.srs_id, con.min_x, "
                "ma.pixel_x_size, 0, con.max_y, 0, -ma.pixel_y_size, "
                "(con.max_x-con.min_x)/ma.pixel_x_size, "
                "(con.max_y-con.min_y)/ma.pixel_y_size, con.identifier, "
                "con.description FROM gpkg_contents con, gpkg_spatial_ref_sys "
                "srs, gpkg_tile_matrix ma, (SELECT max(zoom_level) as max "
                "FROM gpkg_tile_matrix) max WHERE con.table_name = '%s' AND "
                "con.srs_id = srs.srs_id AND ma.table_name = con.table_name "
                "AND ma.zoom_level = max.max;" % gpkg_name
            )
            result = cursor_in.fetchone()
            proj_string = "%s:%i" % result[0:2]
            geotransform = result[2:8]
            size = [int(i) for i in result[8:10]]
            creation_options = []
            if result[10] is not None and result[10] != "":
                creation_options.append('RASTER_IDENTIFIER=%s' % result[10])
            if result[11] is not None and result[11] != "":
                creation_options.append('RASTER_DESCRIPTION=%s' % result[11])

            #TODO apply srcwin

            #tables gpkg_contents,gpkg_spatial_ref_sys, gpkg_tile_matrix_set,
            #and gpkg_tile_matrix are handled by GDAL
            create_gpkg(
                gpkg_name, proj_string, size, geotransform, creation_options
            )

        with sqlite3.connect("%s.gpkg" % gpkg_name) as conn_out:
            #dump metadata
            copy_table(conn_in, conn_out, "gpkg_metadata_reference",
                       "table_name = '%s'" % gpkg_name)
            copy_table(conn_in, conn_out, "gpkg_metadata",
                       "id IN (SELECT md_file_id FROM gpkg_metadata_reference "
                       "WHERE table_name = '%s')" % gpkg_name)

            #dump tiles
            copy_table(conn_in, conn_out, gpkg_name, has_blob=True)


def main():
    parser = argparse.ArgumentParser(
        description="This script dumps a PostgreSQL-GeoPackage database into "
        "a SQLite GeoPackage."
    )
    parser.add_argument(
        "pg_connection_string",
        help="Connection string for PostgreSQL e.g. \"dbname='gpkg' "
        "user='gpkg'\"."
    )
    parser.add_argument(
        "gpkg_name",
        help="The GeoPackage name used to determine the table in which the "
        "tile data is stored as well as for the filename of the SQLite "
        "GeoPackage to generate."
    )
    parser.add_argument(
        "-srcwin", nargs=4, type=int,
        help="Selects a subwindow from the source GeoPackage for dumping "
        "based on tile indexes starting from 0 0 at the top left."
    )

    args = parser.parse_args()
    if args.srcwin[2] < args.srcwin[0] or args.srcwin[3] < args.srcwin[1]:
        sys.stderr.write(
            "ERROR: Invalid srcwin %s. Third value cannot be smaller than "
            "first value and forth than second.\n" % args.srcwin
        )
        sys.exit(1)

    dump_gpkg(args.pg_connection_string, args.gpkg_name, args.srcwin)

    sys.stdout.write(
        "GeoPackage '%s' successfully exported\n" % args.gpkg_name
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
