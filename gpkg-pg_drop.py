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
#   This script drops a PostgreSQL-GeoPackage from a database reversing the
#   loading by the gpkg-pg_loadpkg.py script.
#
#------------------------------------------------------------------------------

import sys
import psycopg2


def drop_gpkg(pg_connection_string, gpkg_name):

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

            cursor_in.execute(
                "SELECT tgname FROM pg_trigger WHERE tgrelid = "
                "'\"%s\"'::regclass;" % gpkg_name
            )
            triggers = cursor_in.fetchall()
            for trigger in triggers:
                trigger_name = trigger[0]
                cursor_in.execute(
                    "DROP FUNCTION \"%s\"() CASCADE;" % trigger_name
                )
            cursor_in.execute("DROP TABLE \"%s\";" % gpkg_name)
            cursor_in.execute(
                "SELECT md_file_id FROM gpkg_metadata_reference WHERE "
                "table_name = '%s';" % gpkg_name
            )
            md_ids = cursor_in.fetchall()
            cursor_in.execute(
                "DELETE FROM gpkg_metadata_reference WHERE table_name = '%s';"
                % gpkg_name
            )
            for md_id in md_ids:
                cursor_in.execute(
                    "DELETE FROM gpkg_metadata WHERE id = '%s';" % md_id
                )
            cursor_in.execute(
                "DELETE FROM gpkg_tile_matrix WHERE table_name = '%s';"
                % gpkg_name
            )
            cursor_in.execute(
                "DELETE FROM gpkg_tile_matrix_set WHERE table_name = '%s';"
                % gpkg_name
            )
            cursor_in.execute(
                "DELETE FROM gpkg_contents WHERE table_name = '%s';"
                % gpkg_name
            )


if __name__ == "__main__":
    if len(sys.argv) <= 2:
        sys.stderr.write(
            "ERROR: Please provide the connection string for PostgreSQL as "
            "well as the GeoPackage name to drop.\n"
        )
        sys.exit(1)

    pg_connection_string = sys.argv[1]
    gpkg_name = sys.argv[2]

    drop_gpkg(pg_connection_string, gpkg_name)

    sys.stdout.write(
        "GeoPackage '%s' successfully deleted\n" % gpkg_name
    )
    sys.exit(0)
