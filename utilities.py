# -*- coding: utf-8
"""
Copyright © 2020 Stephen McEntee
Licensed under the MIT license. 
See LICENSE file for details https://github.com/qwilka/data-visualizer-2015/blob/master/LICENSE
"""
import calendar
import datetime
import logging
import os
import re
import sys
import time
import uuid

valid_identifier = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')


def identify_number(strg):
    if type(strg).__name__ in ("float", "int"):
        return type(strg).__name__
    try:
        float(strg)
        strg_type = "float"
        if strg[0] in ("+", "-"):
            strg = strg[1:]
        if strg.isdigit():
            strg_type = "int"
        return strg_type
    except ValueError:
        return "str"


def args_into_func(func, **args): 
    '''Assign a dictionary of keyword arguments to a function
    Ref: http://stackoverflow.com/questions/817087/call-a-function-with-argument-list-in-python
    '''
    return func(**args)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def make_timestamp(timestring=None, formatstring='%Y-%m-%dT%H:%M:%SZ', truncate=True):
    """Return a POSIX timestamp. (Default, return timestamp for current time).
    
    :param timestring: string specifying date and time in UTC
    :param formatstring: string specifying format for timestring (default ISO 8601)
    :param truncate: if True, truncate timestamp to second
    :returns: POSIX timestamp as int (truncate=True), or float (truncate=False)
    
    Examples:
    >>> make_timestamp('2013-06-05T15:19:10Z')
    1370445550
    >>> make_timestamp('04/01/2008 08:29:55', '%d/%m/%Y %H:%M:%S')
    1199435395
    >>> make_timestamp()
    14357...
    """
    # http://www.avilpage.com/2014/11/python-unix-timestamp-utc-and-their.html
    if timestring:
        timestamp = calendar.timegm( time.strptime(timestring, formatstring) )
    else:
        try:
            timestamp = datetime.datetime.utcnow().timestamp()
        except AttributeError:
            timestamp = time.time()
    if truncate:
        timestamp = int( timestamp )
    return timestamp


def timestamp_to_timestring(timestamp, formatstring='%Y-%m-%dT%H:%M:%SZ'):
    """Return a date and time string from a POSIX timestamp.
    
    :param timestamp: POSIX timestamp
    :param formatstring: string specifying format for timestring (default ISO 8601)
    :returns: date and time string in UTC

    Examples:
    >>> timestamp_to_timestring(1009931465, '%d/%m/%Y %H:%M:%S')
    '02/01/2002 00:31:05'
    >>> timestamp_to_timestring(810637651)
    '1995-09-09T09:07:31Z'
    """
    dt = datetime.datetime.utcfromtimestamp(timestamp)
    return dt.strftime(formatstring)


def make_uuid():
    return uuid.uuid4().hex


def make_file_metadata(dict_=None, reset=False):
    if not dict_:
        dict_ = {}


def traverse_tree(dic, func=None, level=0):
    # http://stackoverflow.com/questions/380734/how-to-do-this-python-dictionary-traverse-and-search
    # http://stackoverflow.com/questions/12399259/finding-the-level-of-recursion-call-in-python
    for key, value in dic.items():
        if func:
            func(key)
        else:
            print(key, level)
        if value and type(value).__name__ == 'dict':
            traverse_tree(value, func, level=level+1)

# --------------set up logging--------------------------------------
# Redirect stdout and stderr to a logger in Python Electricmonk.nl
class StreamToLogger(object):
   """
   Fake file-like stream object that redirects writes to a logger instance.
   """
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''
 
   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())


def setup_logger(logfile=None, lvl=logging.INFO, 
                redir_STOUT=False, redir_STDERR=False,
                frmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
    if redir_STOUT:
        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl
     
    if redir_STDERR:
        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl 
    
    logger = logging.getLogger("")
    logger.setLevel(lvl)
    if logfile:
		fh = logging.FileHandler(logfile, mode='w')
    else:
		fh = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(frmt)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    if not redir_STOUT and logger.level <= logging.WARN:
        print("Logging application messages to file {}," 
               " if problems check this file.".format( os.path.abspath(logfile)) )
    return logger


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True, optionflags=doctest.ELLIPSIS) # optionflags=(doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE)

