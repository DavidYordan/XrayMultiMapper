import html
import logging
import os

from datetime import datetime, timedelta
from PyQt6 import (
    QtCore,
    QtWidgets,
    QtGui
)

class Logging(logging.Handler):
    def __init__(self, textedit:QtWidgets.QTextEdit, textlabel:QtGui.QAction):
        super().__init__()
        
        self.textedit = textedit
        self.textlable = textlabel
        self.setFormatter(logging.Formatter('<font color=\"#%(color)s\">%(user)s - %(asctime)s - %(level)s - %(message)s</font>'))
        self.log_directory = "logs"
        os.makedirs(self.log_directory, exist_ok=True)
        self.update_file_handler()
        self.logger = logging.getLogger('AirDrop')
        self.logger.addHandler(self)
        self.logger.setLevel(logging.INFO)

        self.info('Logging', 'Logging successfully initialized.')

    def delete_old_logs(self):
        retention_period = timedelta(days=7)
        for file in os.listdir(self.log_directory):
            file_path = os.path.join(self.log_directory, file)
            file_date_str = file.split(".")[0]
            file_date = datetime.strptime(file_date_str, "%Y-%m-%d")
            if datetime.now() - file_date > retention_period:
                os.remove(file_path)

    def update_file_handler(self):
        if hasattr(self, 'file_handler'):
            self.logger.removeHandler(self.file_handler)
            self.file_handler.close()

        today = datetime.now().strftime("%Y-%m-%d")
        file_name = f"{self.log_directory}/{today}.log"
        self.file_handler = logging.FileHandler(file_name, encoding='utf-8')
        self.file_handler.setFormatter(logging.Formatter('%(user)s - %(asctime)s - %(level)s - %(message)s'))
        self.logger.addHandler(self.file_handler)

        self.delete_old_logs()

    def emit(self, record_edit, record_label, file_record):
        try:
            QtCore.QMetaObject.invokeMethod(self.textedit, 'append', QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, self.format(record_edit)))
            QtCore.QMetaObject.invokeMethod(self.textlable, 'setText', QtCore.Qt.ConnectionType.QueuedConnection, QtCore.Q_ARG(str, self.format(record_label)))
            self.file_handler.emit(file_record)
        except Exception as e:
            print(str(e))

    def debug(self, user, message):
        message = str(message)
        self.emit(
            logging.makeLogRecord({'user': user, 'level': 'DEBUG', 'msg': html.escape(message), 'color': '000000'}),
            logging.makeLogRecord({'user': user, 'level': 'DEBUG', 'msg': html.escape(message if len(message)<30 else message[:30]), 'color': '000000'}),
            logging.makeLogRecord({'user': user, 'level': 'DEBUG', 'msg': message, 'color': '000000'})
        )

    def info(self, user, message):
        message = str(message)
        self.emit(
            logging.makeLogRecord({'user': user, 'level': 'INFO', 'msg': html.escape(message), 'color': '3CB371'}),
            logging.makeLogRecord({'user': user, 'level': 'INFO', 'msg': html.escape(message if len(message)<30 else message[:30]), 'color': '3CB371'}),
            logging.makeLogRecord({'user': user, 'level': 'INFO', 'msg': message, 'color': '000000'})
        )

    def warning(self, user, message):
        message = str(message)
        self.emit(
            logging.makeLogRecord({'user': user, 'level': 'WARNING', 'msg': html.escape(message), 'color': 'FF8C00'}),
            logging.makeLogRecord({'user': user, 'level': 'WARNING', 'msg': html.escape(message if len(message)<30 else message[:30]), 'color': 'FF8C00'}),
            logging.makeLogRecord({'user': user, 'level': 'WARNING', 'msg': message, 'color': '000000'})
        )

    def error(self, user, message):
        message = str(message)
        self.emit(
            logging.makeLogRecord({'user': user, 'level': 'ERROR', 'msg': html.escape(message), 'color': 'FF0000'}),
            logging.makeLogRecord({'user': user, 'level': 'ERROR', 'msg': html.escape(message if len(message)<30 else message[:30]), 'color': 'FF0000'}),
            logging.makeLogRecord({'user': user, 'level': 'ERROR', 'msg': message, 'color': '000000'})
        )