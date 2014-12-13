"""
.. module:: Common functions for mercurius
   :platform: Linux
   :synopsis: function helpers for Mercurius
   :copyright: (c) 2012-2013 by Ernesto Bossi.
   :license: MIT.

.. moduleauthor:: Ernesto Bossi <bossi.ernestog@gmail.com>

"""

import inspect

def get_current_method_name():
    """Auxiliary function to not to do DRY"""
    return inspect.stack()[1][3]

def bytedecode(bytestring):
    return str(bytestring,'utf-8')

def encode_str(string):
    str.encode(string)