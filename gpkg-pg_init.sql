-------------------------------------------------------------------------------
--
-- Project: PostgreSQL-GeoPackage
-- Authors: Stephan Meissl <stephan.meissl@eox.at>
--
-------------------------------------------------------------------------------
-- Copyright (C) 2016 EOX IT Services GmbH
--
-- Permission is hereby granted, free of charge, to any person obtaining a copy
-- of this software and associated documentation files (the "Software"), to
-- deal in the Software without restriction, including without limitation the
-- rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
-- sell copies of the Software, and to permit persons to whom the Software is
-- furnished to do so, subject to the following conditions:
--
-- The above copyright notice and this permission notice shall be included in
-- all copies of this Software or works derived from this Software.
--
-- THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
-- IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
-- FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
-- AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
-- LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
-- FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
-- IN THE SOFTWARE.
-------------------------------------------------------------------------------
--
-- Description:
--
--   SQL statements to initialize a PostgreSQL database to store a GeoPackage.
--
-------------------------------------------------------------------------------

CREATE TABLE gpkg_spatial_ref_sys (
    srs_name TEXT NOT NULL,
    srs_id INTEGER NOT NULL PRIMARY KEY,
    organization TEXT NOT NULL,
    organization_coordsys_id INTEGER NOT NULL,
    definition TEXT NOT NULL,
    description TEXT
);

INSERT INTO gpkg_spatial_ref_sys (
    srs_name,
    srs_id,
    organization,
    organization_coordsys_id,
    definition,
    description
) VALUES (
    'WGS 84 geodetic',
    4326,
    'EPSG',
    4326,
    'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563,AUTHORITY["EPSG","7030"]],AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]',
    'longitude/latitude coordinates in decimal degrees on the WGS 84 spheroid'
);
INSERT INTO gpkg_spatial_ref_sys (
    srs_name,
    srs_id,
    organization,
    organization_coordsys_id,
    definition,
    description
) VALUES (
    'Undefined cartesian SRS',
    -1,
    'NONE',
    -1,
    'undefined',
    'undefined cartesian coordinate reference system'
);
INSERT INTO gpkg_spatial_ref_sys (
    srs_name,
    srs_id,
    organization,
    organization_coordsys_id,
    definition,
    description
) VALUES (
    'Undefined geographic SRS',
    0,
    'NONE',
    0,
    'undefined',
    'undefined geographic coordinate reference system'
);

CREATE TABLE gpkg_contents (
    table_name TEXT NOT NULL PRIMARY KEY,
    data_type TEXT NOT NULL,
    identifier TEXT UNIQUE,
    description TEXT DEFAULT '',
    last_change TIMESTAMPTZ NOT NULL DEFAULT now(),
    min_x FLOAT,
    min_y FLOAT,
    max_x FLOAT,
    max_y FLOAT,
    srs_id INTEGER,
    CONSTRAINT fk_gc_r_srs_id FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys(srs_id)
);

CREATE TABLE gpkg_tile_matrix_set (
    table_name TEXT NOT NULL PRIMARY KEY,
    srs_id INTEGER NOT NULL,
    min_x FLOAT NOT NULL,
    min_y FLOAT NOT NULL,
    max_x FLOAT NOT NULL,
    max_y FLOAT NOT NULL,
    CONSTRAINT fk_gtms_table_name FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name),
    CONSTRAINT fk_gtms_srs FOREIGN KEY (srs_id) REFERENCES gpkg_spatial_ref_sys (srs_id)
);

CREATE TABLE gpkg_tile_matrix (
    table_name TEXT NOT NULL,
    zoom_level INTEGER NOT NULL,
    matrix_width INTEGER NOT NULL,
    matrix_height INTEGER NOT NULL,
    tile_width INTEGER NOT NULL,
    tile_height INTEGER NOT NULL,
    pixel_x_size FLOAT NOT NULL,
    pixel_y_size FLOAT NOT NULL,
    CONSTRAINT pk_ttm PRIMARY KEY (table_name, zoom_level),
    CONSTRAINT fk_tmm_table_name FOREIGN KEY (table_name) REFERENCES gpkg_contents(table_name)
);

CREATE FUNCTION gpkg_tile_matrix_zoom_level_insert() RETURNS trigger AS $gpkg_tile_matrix_zoom_level_insert$
    BEGIN
        IF NEW.zoom_level < 0 THEN
            RAISE EXCEPTION 'insert on table ''gpkg_tile_matrix'' violates constraint: zoom_level cannot be less than 0';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_zoom_level_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_zoom_level_insert
BEFORE INSERT ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_zoom_level_insert();

CREATE FUNCTION gpkg_tile_matrix_zoom_level_update() RETURNS trigger AS $gpkg_tile_matrix_zoom_level_update$
    BEGIN
        IF NEW.zoom_level < 0 THEN
            RAISE EXCEPTION 'update on table ''gpkg_tile_matrix'' violates constraint: zoom_level cannot be less than 0';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_zoom_level_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_zoom_level_update
BEFORE UPDATE ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_zoom_level_update();

CREATE FUNCTION gpkg_tile_matrix_matrix_width_insert() RETURNS trigger AS $gpkg_tile_matrix_matrix_width_insert$
    BEGIN
        IF NEW.matrix_width < 1 THEN
            RAISE EXCEPTION 'insert on table ''gpkg_tile_matrix'' violates constraint: matrix_width cannot be less than 1';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_matrix_width_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_matrix_width_insert
BEFORE INSERT ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_matrix_width_insert();

CREATE FUNCTION gpkg_tile_matrix_matrix_width_update() RETURNS trigger AS $gpkg_tile_matrix_matrix_width_update$
    BEGIN
        IF NEW.matrix_width < 1 THEN
            RAISE EXCEPTION 'update on table ''gpkg_tile_matrix'' violates constraint: matrix_width cannot be less than 1';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_matrix_width_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_matrix_width_update
BEFORE UPDATE ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_matrix_width_update();

CREATE FUNCTION gpkg_tile_matrix_matrix_height_insert() RETURNS trigger AS $gpkg_tile_matrix_matrix_height_insert$
    BEGIN
        IF NEW.matrix_height < 1 THEN
            RAISE EXCEPTION 'insert on table ''gpkg_tile_matrix'' violates constraint: matrix_height cannot be less than 1';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_matrix_height_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_matrix_height_insert
BEFORE INSERT ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_matrix_height_insert();

CREATE FUNCTION gpkg_tile_matrix_matrix_height_update() RETURNS trigger AS $gpkg_tile_matrix_matrix_height_update$
    BEGIN
        IF NEW.matrix_width < 1 THEN
            RAISE EXCEPTION 'update on table ''gpkg_tile_matrix'' violates constraint: matrix_height cannot be less than 1';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_matrix_height_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_matrix_height_update
BEFORE UPDATE OF matrix_height ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_matrix_height_update();

CREATE FUNCTION gpkg_tile_matrix_pixel_x_size_insert() RETURNS trigger AS $gpkg_tile_matrix_pixel_x_size_insert$
    BEGIN
        IF NOT (NEW.pixel_x_size > 0) THEN
            RAISE EXCEPTION 'insert on table ''gpkg_tile_matrix'' violates constraint: pixel_x_size must be greater than 0';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_pixel_x_size_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_pixel_x_size_insert
BEFORE INSERT ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_pixel_x_size_insert();

CREATE FUNCTION gpkg_tile_matrix_pixel_x_size_update() RETURNS trigger AS $gpkg_tile_matrix_pixel_x_size_update$
    BEGIN
        IF NOT (NEW.pixel_x_size > 0) THEN
            RAISE EXCEPTION 'update on table ''gpkg_tile_matrix'' violates constraint: pixel_x_size must be greater than 0';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_pixel_x_size_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_pixel_x_size_update
BEFORE UPDATE OF pixel_x_size ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_pixel_x_size_update();

CREATE FUNCTION gpkg_tile_matrix_pixel_y_size_insert() RETURNS trigger AS $gpkg_tile_matrix_pixel_y_size_insert$
    BEGIN
        IF NOT (NEW.pixel_y_size > 0) THEN
            RAISE EXCEPTION 'insert on table ''gpkg_tile_matrix'' violates constraint: pixel_y_size must be greater than 0';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_pixel_y_size_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_pixel_y_size_insert
BEFORE INSERT ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_pixel_y_size_insert();

CREATE FUNCTION gpkg_tile_matrix_pixel_y_size_update() RETURNS trigger AS $gpkg_tile_matrix_pixel_y_size_update$
    BEGIN
        IF NOT (NEW.pixel_y_size > 0) THEN
            RAISE EXCEPTION 'update on table ''gpkg_tile_matrix'' violates constraint: pixel_y_size must be greater than 0';
        END IF;
        RETURN NEW;
    END;
$gpkg_tile_matrix_pixel_y_size_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_tile_matrix_pixel_y_size_update
BEFORE UPDATE OF pixel_y_size ON gpkg_tile_matrix
FOR EACH ROW EXECUTE PROCEDURE gpkg_tile_matrix_pixel_y_size_update();

CREATE TABLE gpkg_metadata (
    id INTEGER NOT NULL PRIMARY KEY,
    md_scope TEXT NOT NULL DEFAULT 'dataset',
    md_standard_uri TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'text/xml',
    metadata TEXT NOT NULL
);

CREATE FUNCTION gpkg_metadata_md_scope_insert() RETURNS trigger AS $gpkg_metadata_md_scope_insert$
    BEGIN
        IF NOT NEW.md_scope IN ('undefined','fieldSession','collectionSession','series','dataset', 'featureType','feature','attributeType','attribute','tile','model', 'catalog','schema','taxonomy','software','service', 'collectionHardware','nonGeographicDataset','dimensionGroup') THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata violates constraint: md_scope must be one of undefined | fieldSession | collectionSession | series | dataset | featureType | feature | attributeType | attribute | tile | model | catalog | schema | taxonomy software | service | collectionHardware | nonGeographicDataset | dimensionGroup';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_md_scope_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_md_scope_insert
BEFORE INSERT ON gpkg_metadata
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_md_scope_insert();

CREATE FUNCTION gpkg_metadata_md_scope_update() RETURNS trigger AS $gpkg_metadata_md_scope_update$
    BEGIN
        IF NOT NEW.md_scope IN ('undefined','fieldSession','collectionSession','series','dataset', 'featureType','feature','attributeType','attribute','tile','model', 'catalog','schema','taxonomy','software','service', 'collectionHardware','nonGeographicDataset','dimensionGroup') THEN
            RAISE EXCEPTION 'update on table gpkg_metadata violates constraint: md_scope must be one of undefined | fieldSession | collectionSession | series | dataset | featureType | feature | attributeType | attribute | tile | model | catalog | schema | taxonomy software | service | collectionHardware | nonGeographicDataset | dimensionGroup';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_md_scope_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_md_scope_update
BEFORE UPDATE ON gpkg_metadata
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_md_scope_update();

CREATE TABLE gpkg_metadata_reference (
    reference_scope TEXT NOT NULL,
    table_name TEXT,
    column_name TEXT,
    row_id_value INTEGER,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    md_file_id INTEGER NOT NULL,
    md_parent_id INTEGER,
    CONSTRAINT crmr_mfi_fk FOREIGN KEY (md_file_id) REFERENCES gpkg_metadata(id),
    CONSTRAINT crmr_mpi_fk FOREIGN KEY (md_parent_id) REFERENCES gpkg_metadata(id)
);

CREATE FUNCTION gpkg_metadata_reference_reference_scope_insert() RETURNS trigger AS $gpkg_metadata_reference_reference_scope_insert$
    BEGIN
        IF NOT NEW.reference_scope IN ('geopackage','table','column','row','row/col') THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata_reference violates constraint: reference_scope must be one of "geopackage", table", "column", "row", "row/col"';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_reference_scope_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_reference_scope_insert
BEFORE INSERT ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_reference_scope_insert();

CREATE FUNCTION gpkg_metadata_reference_reference_scope_update() RETURNS trigger AS $gpkg_metadata_reference_reference_scope_update$
    BEGIN
        IF NOT NEW.reference_scope IN ('geopackage','table','column','row','row/col') THEN
            RAISE EXCEPTION 'update on table gpkg_metadata_reference violates constraint: reference_scope must be one of "geopackage", "table", "column", "row", "row/col"';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_reference_scope_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_reference_scope_update
BEFORE UPDATE ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_reference_scope_update();

CREATE FUNCTION gpkg_metadata_reference_column_name_insert() RETURNS trigger AS $gpkg_metadata_reference_column_name_insert$
    BEGIN
        IF NEW.reference_scope IN ('geopackage','table','row') AND NEW.column_name IS NOT NULL THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata_reference violates constraint: column name must be NULL when reference_scope is "geopackage", "table" or "row"';
        END IF;
        IF NEW.reference_scope IN ('column','row/col') AND NOT NEW.table_name IN (SELECT table_name FROM information_schema.columns WHERE table_name = NEW.table_name AND column_name = NEW.column_name) THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata_reference violates constraint: column name must be defined for the specified table when reference_scope is "column" or "row/col"';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_column_name_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_column_name_insert
BEFORE INSERT ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_column_name_insert();

CREATE FUNCTION gpkg_metadata_reference_column_name_update() RETURNS trigger AS $gpkg_metadata_reference_column_name_update$
    BEGIN
        IF NEW.reference_scope IN ('geopackage','table','row') AND NEW.column_name IS NOT NULL THEN
            RAISE EXCEPTION 'update on table gpkg_metadata_reference violates constraint: column name must be NULL when reference_scope is "geopackage", "table" or "row"';
        END IF;
        IF NEW.reference_scope IN ('column','row/col') AND NOT NEW.table_name IN (SELECT table_name FROM information_schema.columns WHERE table_name = NEW.table_name AND column_name = NEW.column_name) THEN
            RAISE EXCEPTION 'update on table gpkg_metadata_reference violates constraint: column name must be defined for the specified table when reference_scope is "column" or "row/col"';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_column_name_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_column_name_update
BEFORE UPDATE ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_column_name_update();

CREATE FUNCTION gpkg_metadata_reference_row_id_value_insert() RETURNS trigger AS $gpkg_metadata_reference_row_id_value_insert$
    DECLARE
        row_id_value int;
    BEGIN
        IF NEW.reference_scope IN ('geopackage','table','column') AND NEW.row_id_value IS NOT NULL THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata_reference violates constraint: row_id_value must be NULL when reference_scope is "geopackage", "table" or "column"';
        END IF;
        IF NEW.table_name IS NOT NULL AND NEW.row_id_value IS NOT NULL THEN
            EXECUTE 'SELECT id FROM ' || quote_ident(NEW.table_name) || ' WHERE id = ' || NEW.row_id_value INTO row_id_value;
        END IF;
        IF NEW.reference_scope IN ('row','row/col') AND row_id_value IS NULL THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata_reference violates constraint: row_id_value must exist in specified table when reference_scope is "row" or "row/col"';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_row_id_value_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_row_id_value_insert
BEFORE INSERT ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_row_id_value_insert();

CREATE FUNCTION gpkg_metadata_reference_row_id_value_update() RETURNS trigger AS $gpkg_metadata_reference_row_id_value_update$
    DECLARE
        row_id_value int;
    BEGIN
        IF NEW.reference_scope IN ('geopackage','table','column') AND NEW.row_id_value IS NOT NULL THEN
            RAISE EXCEPTION 'update on table gpkg_metadata_reference violates constraint: row_id_value must be NULL when reference_scope is "geopackage", "table" or "column"';
        END IF;
        IF NEW.table_name IS NOT NULL AND NEW.row_id_value IS NOT NULL THEN
            EXECUTE 'SELECT id FROM ' || quote_ident(NEW.table_name) || ' WHERE id = ' || NEW.row_id_value INTO row_id_value;
        END IF;
        IF NEW.reference_scope IN ('row','row/col') AND row_id_value IS NULL THEN
            RAISE EXCEPTION 'update on table gpkg_metadata_reference violates constraint: row_id_value must exist in specified table when reference_scope is "row" or "row/col"';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_row_id_value_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_row_id_value_update
BEFORE UPDATE ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_row_id_value_update();

CREATE FUNCTION gpkg_metadata_reference_timestamp_insert() RETURNS trigger AS $gpkg_metadata_reference_timestamp_insert$
    BEGIN
        IF NOT to_char(NEW.timestamp,'YYYY-MM-DD"T"HH:MI:SS.MS"Z"') ~ '[1-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9][0-9][0-9]Z' THEN
            RAISE EXCEPTION 'insert on table gpkg_metadata_reference violates constraint: timestamp must be a valid time in ISO 8601 "yyyy-mm-ddThh:mm:ss.cccZ" form';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_timestamp_insert$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_timestamp_insert
BEFORE INSERT ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_timestamp_insert();

CREATE FUNCTION gpkg_metadata_reference_timestamp_update() RETURNS trigger AS $gpkg_metadata_reference_timestamp_update$
    BEGIN
        IF NOT to_char(NEW.timestamp,'YYYY-MM-DD"T"HH:MI:SS.MS"Z"') ~ '[1-2][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9].[0-9][0-9][0-9]Z' THEN
            RAISE EXCEPTION 'update on table gpkg_metadata_reference violates constraint: timestamp must be a valid time in ISO 8601 "yyyy-mm-ddThh:mm:ss.cccZ" form';
        END IF;
        RETURN NEW;
    END;
$gpkg_metadata_reference_timestamp_update$ LANGUAGE plpgsql;
CREATE TRIGGER gpkg_metadata_reference_timestamp_update
BEFORE UPDATE ON gpkg_metadata_reference
FOR EACH ROW EXECUTE PROCEDURE gpkg_metadata_reference_timestamp_update();
