#!/bin/bash

########################
# This iterates over all (submission) directories in some common dir
# and calls grade50 to produce grading info and feedback text
# https://github.com/pazz/grade50


SCHEME_FILE=`realpath $1`  # grade50 grading scheme file
SUBMISSIONS_DIR=$2  # directory holding student submissions

full_path=$(realpath $0)

# # go over all lines after the header and extract columns 1,2,3,5
 for DIR in $SUBMISSIONS_DIR/*;
 do
   echo "DIR: $DIR"
   pushd $DIR
   grade50 -o json $SCHEME_FILE report.json > grade.json
   grade50 $SCHEME_FILE report.json > FEEDBACK.txt
   popd
 done
