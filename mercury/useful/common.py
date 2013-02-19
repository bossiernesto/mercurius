"""
.. module:: Common functions for mercurius
   :platform: Linux
   :synopsis: function helpers for Mercurius
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

from mercury.logger.coloredLogger import MercuryLogger
import sys
from mercury import *

def getLogger():
    return appContext().getObject(MercuryLogger)

def pythonver_applies(version):
    """"Compare if python version is same or greater"""
    return tuple([int(x) for x in version.split('.')]) <= sys.version_info

def ifdebug():
    return appContext().getValue("SHOW_DEBUG_INFO")==True