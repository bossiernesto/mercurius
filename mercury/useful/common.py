from mercury.useful import *
from mercury.logger.coloredLogger import MercuryLogger
import sys

def getLogger():
    return appContext().getObject(MercuryLogger)

def pythonver_applies(version):
    """"Compare if python version is same or greater"""
    return tuple([int(x) for x in version.split('.')]) <= sys.version_info


