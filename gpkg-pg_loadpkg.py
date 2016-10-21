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
#   This script loads a SQLite GeoPackage into a PostgreSQL-GeoPackage
#   database.
#
#   gpkg-pg_loadpkg.py takes a provided SQLite GeoPackage containing raster
#   tile data only and loads it into the given PostgreSQL-GeoPackage database.
#   This script might get a switch to make a selection of the data to be
#   loaded, for example based on a spatial bounding box.
#
# Ideas for future:
#
#   * Add a progress indicator
#
#------------------------------------------------------------------------------

import sys
import os
import sqlite3
import datetime
import psycopg2


def record_to_string(record):
    type_str = type(u'str')
    type_datetime = type(datetime.datetime.now())
    type_buffer = type(buffer(""))
    type_None = type(None)
    type_float = type(0.0)

    values = []
    for item in record:
        if type(item) == type_None:
            values.append('NULL')
        elif type(item) == type_str:
            values.append("'" + item.replace("'", "''") + "'")
        elif type(item) == type_datetime:
            values.append('"' + str(item) + '"')
        elif type(item) == type_buffer:
            values.append(psycopg2.Binary(item).getquoted())
        elif type(item) == type_float:
            values.append("%.19f" % item)
        else:
            values.append(str(item))
    return ','.join(values)


def copy_table(conn_in, conn_out, table_name, constraint=None):
    cursor_in = conn_in.cursor()
    #Check that table exists
    cursor_in.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='%s';"
        % table_name
    )
    if cursor_in.fetchone():
        cursor_in.execute(
            "SELECT * FROM \"%s\"%s;" % (table_name, "" if constraint is None
                                         else " WHERE " + constraint)
        )

        with conn_out.cursor() as cursor_out:
            for record in cursor_in:
                values = record_to_string(record)
                try:
                    cursor_out.execute(
                        "INSERT INTO \"%s\" VALUES (%s);" %
                        (table_name, values)
                    )
                except psycopg2.IntegrityError as e:
                    conn_out.rollback()
                    if e.pgcode == '23505':
                        sys.stderr.write(
                            "ERROR: GeoPackage seems to be already imported. "
                            "Error message was: '%s'.\n" % e.message
                        )
                        sys.exit(1)
                except Exception as e:
                    conn_out.rollback()
                    sys.stderr.write(
                        "ERROR: Input doesn't seem to be a valid GeoPackage. "
                        "Error message was: '%s'.\n" % e.message
                    )
                    sys.exit(1)


def create_tiles_table(conn_in, conn_out, cursor_out, table_name):
   #Create GeoPackage tiles table
    cursor_out.execute(
        "CREATE TABLE \"%s\" ("
        "    id BIGSERIAL PRIMARY KEY,"
        "    zoom_level BIGINT NOT NULL,"
        "    tile_column BIGINT NOT NULL,"
        "    tile_row BIGINT NOT NULL,"
        "    tile_data BYTEA NOT NULL,"
        "    UNIQUE (zoom_level, tile_column, tile_row)"
        ");" % table_name
    )

    #Create triggers for new table
    cursor_out.execute(
        "CREATE FUNCTION \"%s_tile_column_insert\"() RETURNS trigger AS $$"
        "    BEGIN"
        "        IF NEW.tile_column < 0 THEN"
        "            RAISE EXCEPTION 'insert on table ''%s'' violates "
        "constraint: tile_column cannot be < 0';"
        "        END IF;"
        "        IF NOT (NEW.tile_column < (SELECT matrix_width FROM "
        "gpkg_tile_matrix WHERE table_name = '%s' AND zoom_level = "
        "NEW.zoom_level)) THEN"
        "            RAISE EXCEPTION 'insert on table ''%s'' violates "
        "constraint: tile_column must by < matrix_width specified for table "
        "and zoom level in gpkg_tile_matrix';"
        "        END IF;"
        "        RETURN NEW;"
        "    END;"
        "$$ LANGUAGE plpgsql;"
        "CREATE TRIGGER \"%s_tile_column_insert\""
        "BEFORE INSERT ON \"%s\""
        "FOR EACH ROW EXECUTE PROCEDURE \"%s_tile_column_insert\"();"
        % ((table_name,)*7)
    )
    cursor_out.execute(
        "CREATE FUNCTION \"%s_tile_column_update\"() RETURNS trigger AS $$"
        "    BEGIN"
        "        IF NEW.tile_column < 0 THEN"
        "            RAISE EXCEPTION 'update on table ''%s'' violates "
        "constraint: tile_column cannot be < 0';"
        "        END IF;"
        "        IF NOT (NEW.tile_column < (SELECT matrix_width FROM "
        "gpkg_tile_matrix WHERE table_name = '%s' AND zoom_level = "
        "NEW.zoom_level)) THEN"
        "            RAISE EXCEPTION 'update on table ''%s'' violates "
        "constraint: tile_column must by < matrix_width specified for table "
        "and zoom level in gpkg_tile_matrix';"
        "        END IF;"
        "        RETURN NEW;"
        "    END;"
        "$$ LANGUAGE plpgsql;"
        "CREATE TRIGGER \"%s_tile_column_update\""
        "BEFORE UPDATE ON \"%s\""
        "FOR EACH ROW EXECUTE PROCEDURE \"%s_tile_column_update\"();"
        % ((table_name,)*7)
    )
    cursor_out.execute(
        "CREATE FUNCTION \"%s_tile_row_insert\"() RETURNS trigger AS $$"
        "    BEGIN"
        "        IF NEW.tile_row < 0 THEN"
        "            RAISE EXCEPTION 'insert on table ''%s'' violates "
        "constraint: tile_row cannot be < 0';"
        "        END IF;"
        "        IF NOT (NEW.tile_row < (SELECT matrix_height FROM "
        "gpkg_tile_matrix WHERE table_name = '%s' AND zoom_level = "
        "NEW.zoom_level)) THEN"
        "            RAISE EXCEPTION 'insert on table ''%s'' violates "
        "constraint: tile_row must by < matrix_height specified for table and "
        "zoom level in gpkg_tile_matrix';"
        "        END IF;"
        "        RETURN NEW;"
        "    END;"
        "$$ LANGUAGE plpgsql;"
        "CREATE TRIGGER \"%s_tile_row_insert\""
        "BEFORE INSERT ON \"%s\""
        "FOR EACH ROW EXECUTE PROCEDURE \"%s_tile_row_insert\"();"
        % ((table_name,)*7)
    )
    cursor_out.execute(
        "CREATE FUNCTION \"%s_tile_row_update\"() RETURNS trigger AS $$"
        "    BEGIN"
        "        IF NEW.tile_row < 0 THEN"
        "            RAISE EXCEPTION 'update on table ''%s'' violates "
        "constraint: tile_row cannot be < 0';"
        "        END IF;"
        "        IF NOT (NEW.tile_row < (SELECT matrix_height FROM "
        "gpkg_tile_matrix WHERE table_name = '%s' AND zoom_level = "
        "NEW.zoom_level)) THEN"
        "            RAISE EXCEPTION 'update on table ''%s'' violates "
        "constraint: tile_row must by < matrix_height specified for table and "
        "zoom level in gpkg_tile_matrix';"
        "        END IF;"
        "        RETURN NEW;"
        "    END;"
        "$$ LANGUAGE plpgsql;"
        "CREATE TRIGGER \"%s_tile_row_update\""
        "BEFORE UPDATE ON \"%s\""
        "FOR EACH ROW EXECUTE PROCEDURE \"%s_tile_row_update\"();"
        % ((table_name,)*7)
    )
    cursor_out.execute(
        "CREATE FUNCTION \"%s_zoom_insert\"() RETURNS trigger AS $$"
        "    BEGIN"
        "        IF NOT (NEW.zoom_level IN (SELECT zoom_level FROM "
        "gpkg_tile_matrix WHERE table_name = '%s')) THEN"
        "            RAISE EXCEPTION 'insert on table ''%s'' violates "
        "constraint: zoom_level not specified for table in gpkg_tile_matrix';"
        "        END IF;"
        "        RETURN NEW;"
        "    END;"
        "$$ LANGUAGE plpgsql;"
        "CREATE TRIGGER \"%s_zoom_insert\""
        "BEFORE INSERT ON \"%s\""
        "FOR EACH ROW EXECUTE PROCEDURE \"%s_zoom_insert\"();"
        % ((table_name,)*6)
    )
    cursor_out.execute(
        "CREATE FUNCTION \"%s_zoom_update\"() RETURNS trigger AS $$"
        "    BEGIN"
        "        IF NOT (NEW.zoom_level IN (SELECT zoom_level FROM "
        "gpkg_tile_matrix WHERE table_name = '%s')) THEN"
        "            RAISE EXCEPTION 'update on table ''%s'' violates "
        "constraint: zoom_level not specified for table in gpkg_tile_matrix';"
        "        END IF;"
        "        RETURN NEW;"
        "    END;"
        "$$ LANGUAGE plpgsql;"
        "CREATE TRIGGER \"%s_zoom_update\""
        "BEFORE UPDATE ON \"%s\""
        "FOR EACH ROW EXECUTE PROCEDURE \"%s_zoom_update\"();"
        % ((table_name,)*6)
    )

    #Copy content of new table
    copy_table(conn_in, conn_out, table_name)

    #Adjust serial fro future inserts
    cursor_out.execute(
        "SELECT setval(pg_get_serial_sequence('\"%s\"', 'id'), "
        "coalesce(max(id),0) + 1, false) FROM \"%s\";" % ((table_name,)*2)
    )


def read_gpkg(gpkg_filename, pg_connection_string):
    if not os.path.exists(gpkg_filename):
        sys.stderr.write("ERROR: GeoPackage '%s' not found\n" % gpkg_filename)
        sys.exit(1)

    with sqlite3.connect(gpkg_filename) as conn_in:
        with psycopg2.connect(pg_connection_string) as conn_out:
            copy_table(conn_in, conn_out, "gpkg_spatial_ref_sys",
                       "srs_id NOT IN ('-1','0','4326')")
            copy_table(conn_in, conn_out, "gpkg_contents",
                       "data_type = 'tiles'")
            copy_table(conn_in, conn_out, "gpkg_tile_matrix_set")
            copy_table(conn_in, conn_out, "gpkg_tile_matrix")
            copy_table(conn_in, conn_out, "gpkg_metadata")
            copy_table(conn_in, conn_out, "gpkg_metadata_reference")

            cursor_in = conn_in.cursor()
            cursor_in.execute(
                "SELECT table_name FROM gpkg_contents "
                "WHERE data_type = 'tiles';"
            )
            with conn_out.cursor() as cursor_out:
                for table_name in cursor_in:
                    try:
                        create_tiles_table(
                            conn_in, conn_out, cursor_out, table_name[0]
                        )
                    except psycopg2.IntegrityError as e:
                        conn_out.rollback()
                        if e.pgcode == '23505':
                            sys.stderr.write(
                                "ERROR: GeoPackage seems to be already "
                                "imported. Error message was: '%s'.\n"
                                % e.message
                            )
                            sys.exit(1)
                    except Exception as e:
                        sys.stderr.write(
                            "ERROR: Input doesn't seem to be a valid "
                            "GeoPackage. Error message was: '%s'.\n"
                            % e.message
                        )
                        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        sys.stderr.write(
            "ERROR: Please provide filename of GeoPackage as well as "
            "connection string for PostgreSQL.\n"
        )
        sys.exit(1)

    gpkg_filename = sys.argv[1]
    pg_connection_string = sys.argv[2]

    read_gpkg(gpkg_filename, pg_connection_string)

    sys.stdout.write(
        "GeoPackage '%s' successfully imported\n" % gpkg_filename
    )
    sys.exit(0)
