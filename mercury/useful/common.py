from mercury.config.AppContext import appContext
from mercury.logger.coloredLogger import MercuryLogger

def getLogger():
    return appContext().getObject(MercuryLogger)
