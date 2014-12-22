import sys
from mercurius.config.AppContext import *
from mercurius.logger.coloredLogger import *
from logging import FileHandler, DEBUG
from mercurius.core.MercuriusProxy import execMercury
from mercurius.useful.common import bytedecode
from mercurius.gui.qt import *
import threading

class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)
    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n'%record)
        # originally: XStream.stdout().write("{}\n".format(record))

class XStream(QObject):
    _stdout = None
    _stderr = None

    messageWritten = pyqtSignal(str)

    def flush( self ):
        pass

    def fileno( self ):
        return -1

    def write( self, msg ):
        if ( not self.signalsBlocked() ):
            self.messageWritten.emit(str(msg))

    @staticmethod
    def stdout():
        if ( not XStream._stdout ):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        if ( not XStream._stderr ):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr

class MyDialog(QDialog):
    def __init__( self, parent = None ):

        super(MyDialog, self).__init__(parent)

        # setup the ui
        self._console = QTextBrowser(self)

        # create the layout
        layout = QVBoxLayout()
        layout.addWidget(self._console)
        self.setLayout(layout)

        # create connections
        XStream.stdout().messageWritten.connect( self._console.insertPlainText )
        XStream.stderr().messageWritten.connect( self._console.insertPlainText )

class MercuriusGui(QMainWindow):
    closeApp = pyqtSignal()

    def __init__(self, parent = None):
        super().__init__(parent)
        # scroll area widget contents - layout
        self.scrollLayout = QtGui.QFormLayout()

        # scroll area widget contents
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout)

        # scroll area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # main layout
        self.mainLayout = QtGui.QVBoxLayout()
        self.log_dialog = MyDialog()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.log_dialog)
        self.mainLayout.addWidget(self.scrollArea)

        # central widget
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.mainLayout)

        # set central widget
        self.setCentralWidget(self.centralWidget)

        self.resize(800, 750)
        self.setWindowTitle('Mercurius')
        self.setWindowIcon(QIcon('proxy3.png'))
        self.closeApp.connect(self.close)

        self.create_menu_status_bar()

        self.action_about = QtGui.QAction(self)
        self.action_about.setObjectName("action_About")
        self.menu_help.addAction(self.action_about)
        self.menubar.addAction(self.menu_help.menuAction())
        self.menu_help.setTitle(QtGui.QApplication.translate("MainWindow", "&Help", None, QtGui.QApplication.UnicodeUTF8))
        self.action_about.setText(QtGui.QApplication.translate("MainWindow", "&About", None, QtGui.QApplication.UnicodeUTF8))

        self.show()
        self._start_daemon()

    def create_menu_status_bar(self):
        #menu bar and status
        self.menubar = QtGui.QMenuBar(self)
        self.menubar.setGeometry(QRect(0, 0, 800, 25))
        self.menubar.setObjectName("menubar")
        self.menu_help = QtGui.QMenu(self.menubar)
        self.menu_help.setObjectName("menu_help")
        self.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(self)
        self.statusbar.setObjectName("statusbar")
        self.setStatusBar(self.statusbar)

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Exit Mercurius',
            "Are you sure to quit?", QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.daemon_thread._stop()
            event.accept()
            self.destroy()
        else:
            event.ignore()

    def _start_daemon(self):

        appContext.getInstance().build_defaultsettings()
        log_name = bytedecode(appContext.get(LOG, b'log_name'))
        log_file = bytedecode(appContext.get(LOG, b'log_file'))
        logger = ColoredLogger(log_name, log_file)

        file_handler = QtHandler()
        file_handler.setFormatter(logging.Formatter(FORMAT,"%Y-%m-%d %H:%M:%S"))

        logger.addHandler(file_handler)
        logger.setLevel(DEBUG)
        setMercuryLogger(logger)
        #instantiate a mercurius Proxy
        self.daemon_thread = threading.Thread(name='daemon', target=execMercury)
        self.daemon_thread.daemon = True

        self.daemon_thread.start()

if ( __name__ == '__main__' ):

    app = None
    if ( not QApplication.instance() ):
        app = QApplication([])

    myWidget = MercuriusGui()
    myWidget.show()
    app.exec_()