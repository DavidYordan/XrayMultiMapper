from contextlib import contextmanager
from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import (
    QLabel,
    QTextEdit
)
from threading import Lock

from dylogging import Logging

class Globals(QObject):
    _log_textedit = QTextEdit()
    _log_label = QLabel()
    _Log = Logging(_log_textedit, _log_label)
    inbounds_dict = {}
    inbounds_lock = Lock()
    outbounds_dict = {}
    outbounds_lock = Lock()
    routing_used_inbounds_keys = {}
    routing_used_inbounds_keys_lock = Lock()
    routing_used_outbounds_keys = {}
    routing_used_outbounds_keys_lock = Lock()
    routing_used_outbounds_through_keys = set()

    @contextmanager
    def acquire(*locks):
        for lock in locks:
            lock.acquire()
        try:
            yield
        finally:
            for lock in reversed(locks):
                lock.release()