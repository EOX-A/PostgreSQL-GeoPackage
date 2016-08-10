#!/bin/sh -e

echo "Package installation provision step"

aptitude install -y gdal-bin postgis
