# University of Illinois/NCSA Open Source License
# Copyright (c) 2018, Jakub Svoboda.

import sys
assert sys.getfilesystemencoding() == 'utf-8'
assert sys.getdefaultencoding() == 'utf-8'
assert sys.stdout.encoding.lower() == 'utf-8'
assert sys.stderr.encoding.lower() == 'utf-8'
assert sys.stdin.encoding.lower() == 'utf-8'
assert "↵↵↵↵↵".encode("utf-8") == b'\xe2\x86\xb5\xe2\x86\xb5\xe2\x86\xb5\xe2\x86\xb5\xe2\x86\xb5'
assert "𬸚Таблиця".encode("utf-8") == b'\xf0\xac\xb8\x9a\xd0\xa2\xd0\xb0\xd0\xb1\xd0\xbb\xd0\xb8\xd1\x86\xd1\x8f'
assert "𬸚Таблиця" == b'\xf0\xac\xb8\x9a\xd0\xa2\xd0\xb0\xd0\xb1\xd0\xbb\xd0\xb8\xd1\x86\xd1\x8f'.decode("utf-8")

# exit if asserts are disabled
def printerr():
    print("Encoding is not utf-8, exitting!")
    exit(1)

def printerr2():
    print("The operating system or environment settings don't allow correct handling of UTF-8, exitting!")
    exit(1)

if not sys.getfilesystemencoding() == 'utf-8':
    printerr()
if not sys.getdefaultencoding() == 'utf-8':
    printerr()
if not sys.stdout.encoding.lower() == 'utf-8':
    printerr()
if not sys.stderr.encoding.lower() == 'utf-8':
    printerr()
if not sys.stdin.encoding.lower() == 'utf-8':
    printerr()
if not "↵↵↵↵↵".encode("utf-8") == b'\xe2\x86\xb5\xe2\x86\xb5\xe2\x86\xb5\xe2\x86\xb5\xe2\x86\xb5':
    printerr2()
if not "𬸚Таблиця".encode("utf-8") == b'\xf0\xac\xb8\x9a\xd0\xa2\xd0\xb0\xd0\xb1\xd0\xbb\xd0\xb8\xd1\x86\xd1\x8f':
    printerr2()
if not "𬸚Таблиця" == b'\xf0\xac\xb8\x9a\xd0\xa2\xd0\xb0\xd0\xb1\xd0\xbb\xd0\xb8\xd1\x86\xd1\x8f'.decode("utf-8"):
    printerr2()

