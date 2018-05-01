#!/bin/bash

cp TEST_tasks.dat tasks.dat
cp TEST_tasks_trash.dat tasks_trash.dat
rm -f tasks.dat.diffnew
rm -f tasks_trash.dat.diffnew
rm -f woolnote.dat
echo "" > PICKLETEST_OUTFILE.txt
echo "" > PICKLETEST_REPLAY_STATUS_EXPECTED.txt
echo "" > PICKLETEST_REPLAY_STATUS_OBSERVED.txt
echo "" > TEST_GEN_SERIALIZABLE_OUTFILE.txt
rm -f backups/*.dat
rm -rf woolnote/__pycache__ 

