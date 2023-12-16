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
    inbounds_tags = set()
    outbounds_dict = {}
    outbounds_lock = Lock()
    outbounds_tags = set()
    outbounds_tags_lock = Lock()
    routing_original_cell_values = {}
    routing_original_cell_values_lock = Lock()
    routing_used_inbound_options = set()
    routing_used_inbound_options_lock = Lock()
    routing_used_outbound_options = set()
    routing_used_outbound_options_lock = Lock()