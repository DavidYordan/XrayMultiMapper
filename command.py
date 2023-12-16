import re
from PyQt6 import QtCore, QtWidgets
from typing import Dict, Optional, Text

from globals import Globals

class Command(QtCore.QThread):

    finished_signal = QtCore.pyqtSignal()

    def __init__(
        self,
        parent: Optional[QtWidgets.QMainWindow] = None
    ):
        super().__init__(parent)
        self.user = 'Command'
        self.mutex = QtCore.QMutex()
        self.condition = QtCore.QWaitCondition()
        self.stop_flag = False
        self.isWorking = False
        self.method = None
        self.kwargs = {}
        self.pattern = re.compile(r'\bprint\((.*)\)')
        Globals._Log.info(self.user, 'Command successfully initialized.')

    def run(self):
        while not self.stop_flag:
            self.isWorking = False
            self.method = None
            self.kwargs = {}
            self.condition.wait(self.mutex)
            self.isWorking = True
            getattr(self, self.method)(**self.kwargs)

    def command(self, **kwargs):
        if 'text' not in kwargs:
            self.finished_signal.emit()
            return
        text = kwargs['text']
        Globals._Log.debug(self.user, text)
        text = re.sub(self.pattern, r'Globals._Log.debug(self.user, \1)', text.replace('\\t', '\t').replace('\\n', '\n'))
        try:
            exec(text)
        except Exception as e:
            Globals._Log.warning(self.user, str(e))
        self.finished_signal.emit()