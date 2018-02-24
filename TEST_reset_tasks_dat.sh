#!/bin/bash

cp TEST_tasks.dat tasks.dat
cp TEST_tasks_trash.dat tasks_trash.dat
rm -f tasks.dat.diffnew
rm -f tasks_trash.dat.diffnew
rm -f woolnote.dat
echo "" > TEST_INTEGRATION_OUTFILE.txt
echo "" > TEST_INTEGRATION_REPLAY_STATUS_EXPECTED.txt
echo "" > TEST_INTEGRATION_REPLAY_STATUS_OBSERVED.txt
rm -f backups/*.dat
rm -rf woolnote/__pycache__ 

