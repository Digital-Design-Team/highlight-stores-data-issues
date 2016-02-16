#!/usr/bin/env python

"""
Highlights potential issues with the store finder CSV file, as output
by Episerver.

Input: Tab-separated file extracted from Episerver
Output:  CSV file extra columns indicating different checks

Usage: highlight_issues.py <in.csv> <out.csv>
"""

import csv
import json
import logging
import sys
import urllib2
import math

DELIMITER = '\t'
ADDITIONAL_FIELDS = [
    '_postcode_latitude',
    '_postcode_longitude',
    '_postcode_vs_lat_long',
    '_postcode_error',
    '_postcode_map_url',
    '_lat_long_map_url',
]

POSTCODES_IO_SERVER = 'http://postcodes.io'
# POSTCODES_IO_SERVER = 'http://localhost:8000'  # if running your own instance


class GeocodingError(RuntimeError):
    pass


def main(argv):
    logging.basicConfig(level=logging.DEBUG)
    highlight_csv_issues(sys.stdin, sys.stdout)

    logging.info('All done.')


def usage():
    sys.stderr.write('Usage: {} <input.csv> <output.csv>\n'.format(
        sys.argv[0]))


def highlight_csv_issues(f_in, f_out):

    reader = csv.DictReader(f_in, delimiter=DELIMITER)
    writer = csv.DictWriter(
        f_out, reader.fieldnames + ADDITIONAL_FIELDS)
    writer.writeheader()

    for row in reader:
        logging.debug('input row: {}'.format(row))
        out_row = highlight_row_issues(row)
        writer.writerow(out_row)


def highlight_row_issues(input_row):

    def highlight_postcode_vs_lat_long(row):
        postcode = row['pc']
        claimed_lat = float(row['latitude'])
        claimed_lng = float(row['longitude'])

        try:
            lat, lng = geocode_postcode(postcode)
        except GeocodingError as e:
            logging.exception(e)
            return {'_postcode_error': e}

        return {
            '_postcode_latitude': lat,
            '_postcode_longitude': lng,
            '_postcode_vs_lat_long': calculate_distance(
                (lat, lng),
                (claimed_lat, claimed_lng)),
            '_postcode_map_url': make_maps_url(lat, lng),
            '_lat_long_map_url': make_maps_url(claimed_lat, claimed_lng),
        }

    input_row.update(highlight_postcode_vs_lat_long(input_row))
    return input_row


def make_maps_url(lat, lng):
    return 'https://www.google.com/maps?q={lat},{lng}'.format(lat=lat, lng=lng)


def geocode_postcode(postcode):
    """
    Return a latitude/longitude for a given postcode, or raise a GeocodingError
    """
    def call_geocoding_api():
        try:
            response = urllib2.urlopen(
                POSTCODES_IO_SERVER + '/postcodes/{}'.format(postcode))

        except urllib2.HTTPError as e:
            logging.exception(e)
            raise GeocodingError('{}: {}'.format(postcode, repr(e)))

        else:
            return json.load(response)

    def validate_response(response):
        if response['status'] != 200:
            raise GeocodingError(response)

        logging.debug('Geocode data: {}'.format(response))
        return response['result']

    def validate_lat_lng(result):
        lat, lng = result['latitude'], result['longitude']

        if not lat or not lng:
            raise GeocodingError('{}: no lat/lng found in OS data')

        return lat, lng

    response = call_geocoding_api()
    result = validate_response(response)
    lat, lng = validate_lat_lng(result)

    return lat, lng


def calculate_distance(point_1, point_2):
    "Calculate distance in metres between two lat/longs"
    # Thanks to https://gist.github.com/rochacbruno/2883505

    lat1, lon1 = point_1
    lat2, lon2 = point_2
    radius = 6371 * 1000  # metres

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return round(d, 2)


if __name__ == '__main__':
    main(sys.argv)
