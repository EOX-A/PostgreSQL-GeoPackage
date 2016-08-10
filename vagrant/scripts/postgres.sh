#!/bin/sh -e

echo "PostgreSQL provision step"

# PostgreSQL defaults
DB_USER="gpkg"

# Allow DB_USER to access all databases locally
if ! grep -Fxq "local all $DB_USER trust" /etc/postgresql/9.5/main/pg_hba.conf ; then
    echo "Adding user '$DB_USER' to pg_hba.conf."
    sed -e "s/^# \"local\" is for Unix domain socket connections only$/&\nlocal all $DB_USER trust/" \
        -i /etc/postgresql/9.5/main/pg_hba.conf
fi

# Reload PostgreSQL
systemctl force-reload postgresql.service

# Write database configuration script
TMPFILE=`mktemp`
cat << EOF > "$TMPFILE"
#!/bin/sh -e
echo "Running database configuration script."
# cd to a "safe" location
cd /tmp
# Create database user for testing
if [ "\$(psql postgres -tAc "SELECT 1 FROM pg_user WHERE usename='$DB_USER'")" != 1 ] ; then
    echo "Creating database user '$DB_USER'."
    psql postgres -tAc "CREATE USER $DB_USER WITH NOSUPERUSER CREATEDB NOCREATEROLE LOGIN"
fi
EOF
# End of database configuration script

if [ -f $TMPFILE ] ; then
    chgrp postgres $TMPFILE
    chmod g+rx $TMPFILE
    su postgres -c "$TMPFILE"
    rm "$TMPFILE"
else
    echo "Script to configure database not found."
fi
