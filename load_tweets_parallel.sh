#!/bin/sh

files=$(find data/*)
echo '================================================================================'
echo 'load pg_normalized_batch'
echo '================================================================================'
time echo "$files" | parallel ./load_normalized.sh
