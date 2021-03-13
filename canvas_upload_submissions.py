#!/usr/bin/env python3

import csv
import sys
import logging
import argparse
import os
import json
from canvasapi import Canvas

# which canvas instance to interact with
API_URL = "https://liverpool.instructure.com"

# index roster and submission_metadata byt this column
# should be the roster column corresponding to submission directories
KEY = "github_username"

SUBMISSION_BODY = """
<p>You have made the following submission via <code>submit50</code>.</p>
<em>GitHub User</em>: {github_username}<br>
<em>Submitted code</em>: <a href="{github_url}">{github_url}</a><br>
<em>Timestamp</em>: {timestamp}<br>
"""

helpmsg = """
Create dummy submission for an assignment on canvas.

This will iterate through sub directories and for each
make a submission (with dummy text body and timestamp).

The timestamps are read from a CSV file providing metadata for submissions,
one per row. The submission body is defined in this file and may contain
metadata entries.

For authentification, the script relies on an API token from canvas,
given via the -t argument or read from the CANVAS_TOKEN env var.
"""
parser = argparse.ArgumentParser(description=helpmsg)
parser.add_argument('course', help='canvas course id')
parser.add_argument('assignment', help='canvas assignment id')
parser.add_argument(
    'roster',
    help="csv roster from canvas",
    type=argparse.FileType('r'))
parser.add_argument(
    'metadata',
    help='csv containing submission data such as timestamps and user ids.',
    type=argparse.FileType('r'),
    default='-')
parser.add_argument(
    'submissions_dir',
    help='directory containing student submissions as subdirectories')
parser.add_argument('-t', '--token',
                    help='canvas API token',
                    metavar='TOKEN',
                    default=os.environ.get('CANVAS_TOKEN', 'token'))
parser.add_argument("--dryrun", '-d', action='store_true', help="don't do it")
parser.add_argument('-v', '--verbose', action='count', default=0)

_LOG_LEVEL_STRINGS = [logging.ERROR, logging.INFO, logging.DEBUG]


def find_canvas_id_from_dirname(dir_name, roster):
    # The roster maps the the value of a user's KEY entry to the user info dict
    if dir_name not in roster:
        # some students have submitted via submit50 but did not give me their
        # github ID
        return None
    canvas_id = roster[dir_name]['Student ID']
    return canvas_id


def find_submission_metadata(sid, dir_name, submissions_data, roster):
    """
    Try to find the metadata for a submission made by a given student.
    """
    # The submission_data maps the the value of a user's KEY entry to
    # the dictionary with their submission entry
    submission = submissions_data[dir_name]
    return submission


def make_canvas_submission(assignment, sid, meta):

    logging.debug("\ncreating submission..")
    logging.debug(str(meta))

    body = SUBMISSION_BODY.format(**meta)
    timestamp = meta['timestamp']
    logging.debug(body)

    assignment.submit({'submission_type': 'online_text_entry',
                       'body': body,
                       'submitted_at': timestamp,
                       'user_id': sid,
                       })


def get_assignment(token, aid, cid):
    """ get canvas assignment object """
    canvas = Canvas(API_URL, token)
    course = canvas.get_course(cid)
    return course.get_assignment(aid)


def load_roster(filehandle, keyterm='Student ID'):
    """ interpret canvas roster csv """
    entries = {}
    reader = csv.DictReader(filehandle)
    fieldnames = reader.fieldnames
    for student in reader:
        entries[student[keyterm]] = student
    return entries, fieldnames


if __name__ == "__main__":
    # read arguments and set up logging
    args = parser.parse_args()
    logging.basicConfig(
            level=_LOG_LEVEL_STRINGS[args.verbose],
            format='%(message)s',
            )
    # silence canvasapi logger
    logging.getLogger("canvasapi.requester").setLevel(logging.ERROR)

    # read Canvas student roster
    roster, fieldnames = load_roster(args.roster, keyterm=KEY)

    # find submission on disk and its timestamp.
    logging.debug("loading submissions data")
    submissions_data = {}
    for e in csv.DictReader(args.metadata):
        if 'github_username' in e:
            e['github_username'] = e['github_username'].lower()
        submissions_data[e[KEY]] = e

    # read assignment from canvas
    logging.info("loading assignment " + args.assignment)
    assignment = get_assignment(args.token, args.assignment, args.course)
    # change assignment submission type.
    # we will make a submission in each students' name later
    assignment = assignment.edit(assignment={
        'submission_types': ['online_text_entry'],
        # 'allowed_attempts': 1,
    })

    # store write operations for later
    ops = []

    # GO!
    logging.info("iterating over submission directories")
    for sub_dir in os.listdir(args.submissions_dir):

        sid = find_canvas_id_from_dirname(sub_dir, roster)
        if sid is None:
            # could not find canvas id for this directory. Ignore and move on
            logging.error('no canvas ID found for ' + sub_dir)
            continue

        # find submission metadata (timestamp)
        metadata = find_submission_metadata(
            sid, sub_dir, submissions_data, roster)
        if metadata is None:
            logging.error('no submission metadata found for ' + sub_dir)
            sys.exit(1)

        ops.append((sid, metadata))

    if args.dryrun:
        print(json.dumps(ops, indent=2))

    else:
        for sid, meta in ops:
            make_canvas_submission(assignment, sid, meta)
