#!/bin/bash

##############################################################
# This downloads all (submissions) listed in a submit.cs50.io
# provided CSV file into separate directories

TOKEN=$1  # Github API token 
INPUTCSV=$2  # submission csv as downloaded from submit.cs50.io
SUBMISSIONS_DIR=$3  # directory to hold all submissions

# go over all lines after the header and extract columns 1,2,3,5
while IFS="," read -r SLUG GITHUB_ID GITHUB_USER SUBMISSION_URL
do
  # ensure that the user name is all lower case
  GITHUB_USER=`echo $GITHUB_USER | tr '[:upper:]' '[:lower:]'`
  echo "GITHUB_USER: $GITHUB_USER"
  
  # extract the commit hash from the url (the suffix after the 7th slash apparently)
  COMMIT=`echo $SUBMISSION_URL | cut -d '/' -f 7-`
  echo "COMMIT: $COMMIT"

  DIR=$SUBMISSIONS_DIR/$GITHUB_USER
  echo "DIR: $DIR"

  echo "loading submission of $GITHUB_USER..."
  git clone --branch $SLUG https://$TOKEN@github.com/me50/$GITHUB_USER $DIR

  # check out the version that was submitted (not the latest)
  pushd $DIR
  git checkout $COMMIT
  popd
done < <(cut -d "," -f1,2,3,5 $INPUTCSV | tail -n +2)
