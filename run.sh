#!/bin/sh -eux

INPUT_FILE="data/2016-02-16_StoresDataFile.txt"
OUTPUT_FILE="data/2016-02-16_StoresDataFile_annotated.csv"

cat "${INPUT_FILE}" | python ./highlight_issues.py > "${OUTPUT_FILE}"
