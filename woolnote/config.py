# University of Illinois/NCSA Open Source License
# Copyright (c) 2017, Jakub Svoboda.

# TODO: docstring for the file
import os
from woolnote import systemencoding

# environment variables
#######################

def get_environ_var_or_none(var_name):
    result = None
    try:
        val = os.environ[var_name]
        result = str(val)
    except:
        pass
    return result

__hardcode_path_save_db = get_environ_var_or_none("WOOLNOTE_HARDCODE_PATH_SAVE_DB")
__hardcode_path_save_db_backup = get_environ_var_or_none("WOOLNOTE_HARDCODE_PATH_SAVE_DB_BACKUP")
__hardcode_path_cert = get_environ_var_or_none("WOOLNOTE_HARDCODE_PATH_CERT")
__hardcode_path_dropbox_sync = get_environ_var_or_none("WOOLNOTE_HARDCODE_PATH_DROPBOX_SYNC")
__hardcode_ssl_cert_hash = get_environ_var_or_none("WOOLNOTE_HARDCODE_SSL_CERT_HASH")
__hardcode_login_password = get_environ_var_or_none("WOOLNOTE_HARDCODE_LOGIN_PASSWORD")


# constants for basic setup
###########################

# TODO: constant for "woolnote" name - so that woolnote can be renamed easily?

# if a note has empty folder string, use this instead
DEFAULT_FOLDER = "inbox"
# if a note has empty name string, use this instead
DEFAULT_TASKNAME = "Unnamed"

# TODO: use sha256 for storing the password / use a plaintext password for loopback only
LOGIN_PASSWORD = "please_change_me"
if __hardcode_login_password:
    LOGIN_PASSWORD = __hardcode_login_password

HTTP_PORT = 8088
HTTPS_PORT = 8089

# constants for filenames
#########################

THIS_IS_ANDROID = os.path.isdir("/sdcard")
DISPLAY_STARTUP_HELP = False  # if True, woolnote doesn't start but just serves static help
DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES = []
__HELP_MSG_FRAGMENT = " or the working dir './'" if not THIS_IS_ANDROID else ""

# Filenames for files
# * tasks.dat - the main internal task database
# * tasks_trash.dat - the internal trash
# * woolnote.dat - the task database for export/import (has updated export_lamport_clock/timestamps)
# * woolnote.zip - the task database for export/import zipped so that less data are transmitted
# - TODO: autocreate files?

DIFFNEW_EXTENSION = '.diffnew'  # appended to the path when accessing a differential database
FILE_TASKS_DAT = 'tasks.dat'
FILE_TASKS_TRASH_DAT = 'tasks_trash.dat'
FILE_WOOLNOTE_DAT = 'woolnote.dat'
FILE_WOOLNOTE_ZIP = 'woolnote.zip'

# Primary database location - this is written to on every save
# * tasks.dat - the main internal task database
# * tasks_trash.dat - the internal trash
# * woolnote.dat - for caching before ZIP / after unZIP before export.
# The first available path is selected - allows autodetection between multiple environments (pc, phone).
# If none is available, an empty path is used (depends on the environment what it actually resolves to).
_PATHS_SAVE_DB = ["/sdcard/woolnote/"]
PATH_SAVE_DB = "./"
if THIS_IS_ANDROID:
    # do not allow fallback on android
    PATH_SAVE_DB = None
if __hardcode_path_save_db:
    _PATHS_SAVE_DB = [__hardcode_path_save_db]
    PATH_SAVE_DB = None
for _path in _PATHS_SAVE_DB:
    if os.path.isdir(_path):
        PATH_SAVE_DB = _path
        break
if PATH_SAVE_DB is None:
    DISPLAY_STARTUP_HELP = True
    DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("Directory PATH_SAVE_DB not found. - e.g. one of {}{}.".format(repr(_PATHS_SAVE_DB), __HELP_MSG_FRAGMENT))


# Location for backup - this is written to on every startup, import, export
# * tasks.dat - timestamped filenames
# * tasks_trash.dat - timestamped filenames
# The first available path is selected - allows autodetection between multiple environments (pc, phone).
# If none is available, an empty path is used (depends on the environment what it actually resolves to).
_PATHS_SAVE_DB_BACKUP = ["/sdcard/woolnote/backups/", "backups"]
PATH_SAVE_DB_BACKUP = "./"
if THIS_IS_ANDROID:
    # do not allow fallback on android
    PATH_SAVE_DB_BACKUP = None
if __hardcode_path_save_db_backup:
    _PATHS_SAVE_DB_BACKUP = [__hardcode_path_save_db_backup]
    PATH_SAVE_DB_BACKUP = None
for _path in _PATHS_SAVE_DB_BACKUP:
    if os.path.isdir(_path):
        PATH_SAVE_DB_BACKUP = _path
        break
if PATH_SAVE_DB_BACKUP is None:
    DISPLAY_STARTUP_HELP = True
    DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("Directory PATH_SAVE_DB_BACKUP not found. - e.g. one of {}{}.".format(repr(_PATHS_SAVE_DB_BACKUP), __HELP_MSG_FRAGMENT))


# Location for import/export
# * woolnote.zip
# The first available path is selected - allows autodetection between multiple environments (pc, phone).
# If none is available, an empty path is used (depends on the environment what it actually resolves to).
_PATHS_SAVE_DROPBOX_EXPORT = [
    "/storage/emulated/0/Android/data/com.dropbox.android/files/u20358332/scratch/Dokumenty/docs_sync/dropbox2/woolnote/data/sync/",  # example
    "/sdcard/woolnote/",
    "../data/sync/"]
PATH_SAVE_DROPBOX_EXPORT = ""  # woolnote.dat
PATH_LOAD_DROPBOX_IMPORT = ""  # woolnote.dat
if THIS_IS_ANDROID:
    # do not allow fallback on android
    PATH_SAVE_DROPBOX_EXPORT = None
    PATH_LOAD_DROPBOX_IMPORT = None
if __hardcode_path_dropbox_sync:
    _PATHS_SAVE_DROPBOX_EXPORT = [__hardcode_path_dropbox_sync]
    PATH_SAVE_DROPBOX_EXPORT = None
    PATH_LOAD_DROPBOX_IMPORT = None
for _path in _PATHS_SAVE_DROPBOX_EXPORT:
    if os.path.isdir(_path):
        PATH_SAVE_DROPBOX_EXPORT = _path
        PATH_LOAD_DROPBOX_IMPORT = _path
        break
if PATH_SAVE_DROPBOX_EXPORT is None:
    DISPLAY_STARTUP_HELP = True
    DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("Directory PATH_SAVE_DROPBOX_EXPORT not found. - e.g. one of {}{}.".format(repr(_PATHS_SAVE_DROPBOX_EXPORT), __HELP_MSG_FRAGMENT))
if PATH_LOAD_DROPBOX_IMPORT is None:
    DISPLAY_STARTUP_HELP = True
    DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("Directory PATH_LOAD_DROPBOX_IMPORT not found. - e.g. one of {}{}.".format(repr(_PATHS_SAVE_DROPBOX_EXPORT), __HELP_MSG_FRAGMENT))

if not DISPLAY_STARTUP_HELP:
    __task_store_path = os.path.join(PATH_SAVE_DB, FILE_TASKS_DAT)
    __task_store_trash_path = os.path.join(PATH_SAVE_DB, FILE_TASKS_TRASH_DAT)
    if not os.path.isfile(__task_store_path):
        DISPLAY_STARTUP_HELP = True
        DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("File {} not found anywhere in {}{}.".format(repr(__task_store_path), repr(_PATHS_SAVE_DB), __HELP_MSG_FRAGMENT))
    if not os.path.isfile(__task_store_trash_path):
        DISPLAY_STARTUP_HELP = True
        DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("File {} not found anywhere in {}{}.".format(repr(__task_store_trash_path), repr(_PATHS_SAVE_DB), __HELP_MSG_FRAGMENT))

# https://stackoverflow.com/questions/10175812/how-to-create-a-self-signed-certificate-with-openssl
# openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 10000 -nodes
# https://unix.stackexchange.com/questions/140601/verifying-a-ssl-certificates-fingerprint
# openssl x509 -in cert.pem -noout -sha256 -fingerprint
# openssl x509 -in cert.pem -noout -text
# TODO: try to run openssl that is on the system to get the fingerprint
SSL_CERT_PEM_FINGERPRINT = '04 FD EA 0D 8E ... an https certificate hash for comfortable validation should be displayed here. Please read README.txt or the source code.'
if __hardcode_ssl_cert_hash:
    SSL_CERT_PEM_FINGERPRINT = __hardcode_ssl_cert_hash

# Location for SSL key and cert PEM files
# * cert.pem
# * key.pem
# The first available path is selected - allows autodetection between multiple environments (pc, phone).
# If none is available, an empty path is used (depends on the environment what it actually resolves to).
FILE_CERT_PEM = 'cert.pem'
FILE_KEY_PEM = 'key.pem'
_PATHS_SSL_PEM = [ '/storage/emulated/0/com.hipipal.qpyplus/projects3/woolnote/', "../../https_cert/", "/sdcard/woolnote/", './', ]
PATH_DIR_FOR_SSL_CERT_PEM = '' # cert.pem
PATH_DIR_FOR_SSL_KEY_PEM = '' # key.pem
if __hardcode_path_cert:
    _PATHS_SSL_PEM = [__hardcode_path_cert]
    PATH_DIR_FOR_SSL_CERT_PEM = None
    PATH_DIR_FOR_SSL_KEY_PEM = None
for _path in _PATHS_SSL_PEM:
    if os.path.isdir(_path):
        PATH_DIR_FOR_SSL_CERT_PEM = _path
        PATH_DIR_FOR_SSL_KEY_PEM = _path
        break

try:
    __cert_pem_path = os.path.join(PATH_DIR_FOR_SSL_CERT_PEM, FILE_CERT_PEM)
    __key_pem_path = os.path.join(PATH_DIR_FOR_SSL_KEY_PEM, FILE_KEY_PEM)
    if not os.path.isfile(__cert_pem_path):
        DISPLAY_STARTUP_HELP = True
        DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("File {} not found anywhere in {}.".format(repr(__cert_pem_path), repr(_PATHS_SSL_PEM)))
    if not os.path.isfile(__key_pem_path):
        DISPLAY_STARTUP_HELP = True
        DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("File {} not found anywhere in {}.".format(repr(__key_pem_path), repr(_PATHS_SSL_PEM)))
except:
    DISPLAY_STARTUP_HELP = True
    DISPLAY_STARTUP_HELP_LIST_OF_MESSAGES.append("Certificates not found anywhere in {}.".format(repr(_PATHS_SSL_PEM)))
