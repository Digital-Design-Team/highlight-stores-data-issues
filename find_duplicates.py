#!/usr/bin/env python

import csv
import logging
import sys

from collections import defaultdict

LAT_LONG_DECIMAL_PLACES = 4


def main(argv):
    logging.basicConfig(level=logging.INFO)

    find_duplicate_locations(sys.stdin)


def find_duplicate_locations(f):
    reader = csv.DictReader(f)

    colocated = find_colocated(reader)
    print_colocated(colocated)


def find_colocated(csv_rows):
    locations = defaultdict(list)

    def round_ordinate(ordinate):
        return str(round(ordinate, LAT_LONG_DECIMAL_PLACES))

    for row in csv_rows:
        logging.debug('Input row: {}'.format(row))

        if 'Food' not in row['business'] and 'Funeral' not in row['business']:
            continue

        try:
            key = '{lat},{lng}'.format(
                lat=round_ordinate(float(row['_postcode_latitude'])),
                lng=round_ordinate(float(row['_postcode_longitude'])))
        except ValueError as e:
            logging.exception(e)
            continue

        locations[key].append(row)

    return locations


def print_colocated(colocated):
    for key, stores in colocated.items():
        if len(stores) <= 1:
            continue

        print('{} locations at {}'.format(len(stores), key))
        for store in stores:
            print(' - {} ({}): {}'.format(
                format_branch_code(store['branch_code']),
                store['business'],
                store['store_name']))

        print('')


def format_branch_code(branch_code):
    return branch_code if branch_code else '[no branch code]'

if __name__ == '__main__':
    main(sys.argv)
