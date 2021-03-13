#!/bin/bash

########################
# This iterates over all (submission) directories in some common dir
# and in each one calls check50 to produce a report.json

PSET_DIR=`realpath $1`
SUBMISSIONS_DIR=$2

for DIR in $SUBMISSIONS_DIR/*;
do
  echo "DIR: $DIR"
  
  pushd $DIR
  check50 -o json -d $PSET_DIR > report.json
  popd
done
