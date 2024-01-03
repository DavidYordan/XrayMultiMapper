import base64
import ipaddress
import json
import os
import re
from PyQt6.QtCore import (
    pyqtSlot,
    Qt
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)
from urllib.parse import (
    quote,
    unquote
)

from globals import Globals

class InboundsTab(QWidget):
    def __init__(
            self,
            parent,
            inbounds_tag_changed_signal
        ):
        super().__init__(parent)

        self.columns = ['select', 'protocol', 'address', 'port', 'user', 'password', 'remarks']
        self.inbounds_tag_changed_signal = inbounds_tag_changed_signal
        self.orange_datas = {}
        self.user = 'InboundsTab'
        self.setup_ui()

        Globals._Log.info(self.user, 'InboundsTab successfully initialized.')

    def add_blank_row(self):
        ports = set()

        for row in range(self.table.rowCount()):
            address = self.table.item(row, 2).text()
            if address != '0.0.0.0':
                continue
            row_port = self.table.item(row, 3).text()
            if not row_port:
                continue
            ports.add(row_port)

        port = 30001
        while str(port) in ports:
            port += 1

        self.add_row({
            'protocol': 'socks',
            'address': '0.0.0.0',
            'port': str(port),
            'user': '',
            'password': '',
            'remarks': ''
        })
        
    def add_row(self, data: dict):

        def _add_blank_row(insert_position):
            self.table.insertRow(insert_position)

            widget = QWidget()
            layout = QHBoxLayout(widget)
            chk_box = QCheckBox()
            layout.addWidget(chk_box)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(insert_position, 0, widget)

            for col in range(1, self.table.columnCount()):
                item = QTableWidgetItem('')
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(insert_position, col, item)

        def _find_insert_position(address, port):
            row_count = self.table.rowCount()
            for row in range(row_count):
                row_address = self.table.item(row, 3).text()
                if address < row_address:
                    return row
                elif address > row_address:
                    continue
                row_port = self.table.item(row, 4).text()
                if int(port) < int(row_port):
                    return row
            return row_count

        address = data.get('address', '')
        port = data.get('port', '')
        key = f'{address}:{port}'

        with Globals.inbounds_lock:
            keys = Globals.inbounds_dict.keys()
        if key in keys:
            Globals._Log.error(self.user, f'Failed to add row with key: {key}.')
            return

        insert_position = _find_insert_position(address, port)

        self.table.blockSignals(True)
        _add_blank_row(insert_position)
        for col, column in enumerate(self.columns):
            if col == 0:
                continue
            elif col == 6:
                self.table.item(insert_position, col).setText(data.get('remarks', '').replace('|', '').lower())
            else:
                self.table.item(insert_position, col).setText(data.get(column, ''))
        self.table.blockSignals(False)

        self.update_orange_datas()

        with Globals.inbounds_lock:
            Globals.inbounds_dict[key] = data

        self.valid_data_by_row(insert_position)

        Globals._Log.info(self.user, f'New row added with key: {key}.')

    def base64_decode(self, source):
        try:
            text = source.replace('_', '/').replace('-', '+')
            padding = -len(text) % 4
            text += '=' * padding
            return base64.urlsafe_b64decode(text).decode()
        except:
            return source

    def cell_was_clicked(self, row, column):
        if column == 0:
            chk_box = self.get_checkbox(row)
            if not chk_box:
                return
            chk_box.setChecked(not chk_box.isChecked())
        if column == 1:
            self.show_protocol_selection_menu(row, column)

    def delete_data(self, key):
        with Globals.inbounds_lock:
            if key in Globals.inbounds_dict.keys():
                del Globals.inbounds_dict[key]

    def delete_row(self, row):
        address = self.table.item(row, 2).text()
        port = self.table.item(row, 3).text()
        self.table.removeRow(row)
        self.delete_data(f'{address}:{port}')
        Globals._Log.info(self.user, f'Row with key: {address}:{port} has been deleted.')

    def delete_selected_rows(self):
        self.table.blockSignals(True)
        for row in reversed(range(self.table.rowCount())):
            chk_box = self.get_checkbox(row)
            if not chk_box:
                continue
            if not chk_box.isChecked():
                continue
            self.delete_row(row)
        self.table.blockSignals(False)
        self.update_orange_datas()

    def find_row_by_key(self, key):
        for row in range(self.table.rowCount()):
            address = self.table.item(row, 2).text()
            port = self.table.item(row, 3).text()
            if key == f'{address}:{port}':
                return row
        return -1
    
    def get_checkbox(self, row):
        if row < 0:
            return None
        rowCount = self.table.rowCount()
        if row > rowCount:
            return None
        return self.table.cellWidget(row, 0).layout().itemAt(0).widget()
    
    def highlight_row(self, row, color_key, col=-1):
        if color_key == 'green':
            color = QColor(Qt.GlobalColor.green)
        elif color_key == 'red':
            color = QColor(Qt.GlobalColor.red)
        else:
            color = QColor(Qt.GlobalColor.white)
        self.table.blockSignals(True)
        if col < 0:
            for column in range(1, self.table.columnCount()):
                self.table.item(row, column).setBackground(color)
        elif col < len(self.columns):
            self.table.item(row, col).setBackground(color)
        self.table.blockSignals(False)

    def load_data_from_file(self):

        def _clear_table():
            with Globals.inbounds_lock:
                Globals.inbounds_dict.clear()
            self.orange_datas.clear()

            self.table.blockSignals(True)
            while self.table.rowCount() > 0:
                self.table.removeRow(0)
            self.table.blockSignals(False)

        _clear_table()
        if not os.path.exists('inbounds.txt'):
            return
        with open('inbounds.txt', 'r') as file:
            for line in file:
                self.parse_link(line.strip())
        Globals._Log.info(self.user, 'Inbound data loaded successfully from inbounds.txt.')

    def on_cell_changed(self, row, column):

        def _reset_value(row, column):
            self.table.blockSignals(True)
            self.table.item(row, column).setText(self.orange_datas[(row, column)])
            self.table.blockSignals(False)

        if column == 0:
            return
        
        protocol, address, port, user, password, remarks, key = self.parse_row_data(row)

        if column == 1:
            if not self.valid_protocol(protocol):
                _reset_value(row, 1)
                return
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key]['protocol'] = protocol
            self.orange_datas[(row, column)] = protocol

        elif column == 2:
            if not self.valid_address(address):
                _reset_value(row, 2)
                return
            if self.valid_key(row, address, port) != -1:
                _reset_value(row, 2)
                return
            old_key = f'{self.orange_datas[(row, 2)]}:{self.orange_datas[(row, 3)]}'
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key] = Globals.inbounds_dict.pop(old_key)
                Globals.inbounds_dict[key]['address'] = address
            self.orange_datas[(row, 2)] = address
            self.inbounds_tag_changed_signal.emit(old_key, key)

        elif column == 3:
            if not self.valid_port(port):
                _reset_value(row, 3)
                return
            if self.valid_key(row, address, port) != -1:
                _reset_value(row, 3)
                return
            old_key = f'{self.orange_datas[(row, 2)]}:{self.orange_datas[(row, 3)]}'
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key] = Globals.inbounds_dict.pop(old_key)
                Globals.inbounds_dict[key]['port'] = port
            self.orange_datas[(row, 3)] = port
            self.inbounds_tag_changed_signal.emit(old_key, key)
        
        elif column == 4:
            if not self.valid_user(user):
                _reset_value(row, 4)
                return
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key]['user'] = user
            self.orange_datas[(row, 4)] = user
        
        elif column == 5:
            if not self.valid_password(password):
                _reset_value(row, 5)
                return
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key]['password'] = password
            self.orange_datas[(row, 5)] = password
        
        elif column == 6:
            remarks = remarks.replace('|', '').lower()
            if self.valid_remarks(row, remarks) != -1:
                _reset_value(row, 6)
                return
            self.table.blockSignals(True)
            self.table.item(row, 6).setText(remarks)
            self.table.blockSignals(False)
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key]['remarks'] = remarks
            self.orange_datas[(row, 6)] = remarks
            self.inbounds_tag_changed_signal.emit(key, key)

    def parse_row_data(self, row):
        protocol = self.table.item(row, 1).text()
        address = self.table.item(row, 2).text()
        port = self.table.item(row, 3).text()
        user = self.table.item(row, 4).text()
        password = self.table.item(row, 5).text()
        remarks = self.table.item(row, 6).text()
        return protocol, address, port, user, password, remarks, f'{address}:{port}'
        
    def parse_link(self, url):
        if url.count('://') != 1:
            return
        protocol, rest = url.split("://")
        if protocol not in ['http', 'socks']:
            return
        match = re.match(r'(?P<params>.+)@(?P<address>[^:]+):(?P<port>\d+)(?:#(?P<remarks>.+))?', rest)
        if not match:
            return
        user_password = self.base64_decode(match.group('params'))
        if user_password.count(':') != 1:
            return
        user, password = user_password.split(':')
        address = match.group('address')
        port = match.group('port')
        remarks = unquote(match.group('remarks')).strip() if match.group('remarks') else ''
        self.add_row({
            'protocol': protocol,
            'address': address,
            'port': port,
            'user': user,
            'password': password,
            'remarks': remarks
        })

    def reload_rows(self):
        self.load_data_from_file()
        Globals._Log.info(self.user, f'Reload complete.')

    def save_data_to_file(self):

        def _encode_data(protocol, address, port, user, password, remarks):
            user_password = f'{user}:{password}'
            user_password_encoded = base64.urlsafe_b64encode(user_password.encode()).decode().rstrip("=")
            url = f'{protocol}://{user_password_encoded}@{address}:{port}'
            if remarks:
                remarks_encoded = quote(remarks)
                url += f"#{remarks_encoded}"
            return url
        
        if not self.valid_datas():
            Globals._Log.error(self.user, 'Failed to save Inbounds datas.')
            return
        lines = ''
        for row in range(self.table.rowCount()):
            protocol, address, port, user, password, remarks, key = self.parse_row_data(row)
            lines += _encode_data(protocol, address, port, user, password, remarks)
            lines += '\n'
        try:
            with Globals.inbounds_lock:
                with open('inbounds.json', 'w') as file:
                    json.dump(Globals.inbounds_dict, file, indent=4)
            Globals._Log.info(self.user, 'Inbounds datas saved successfully to inbounds.json.')
            with open('inbounds.txt', 'w') as file:
                file.write(lines)
            Globals._Log.info(self.user, 'Inbounds datas saved successfully to inbounds.txt.')
        except Exception as e:
            Globals._Log.error(self.user, f'Failed to save Inbounds datas, Error: {e}')

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        button_add = QPushButton('Add')
        button_add.clicked.connect(self.add_blank_row)
        top_layout.addWidget(button_add)
        button_delete = QPushButton('Delete')
        button_delete.clicked.connect(self.delete_selected_rows)
        top_layout.addWidget(button_delete)
        button_reload = QPushButton('Reload')
        button_reload.clicked.connect(self.reload_rows)
        top_layout.addWidget(button_reload)
        top_layout.addStretch()
        button_save = QPushButton('Save')
        button_save.clicked.connect(self.save_data_to_file)
        top_layout.addWidget(button_save)

        middle_layout = QHBoxLayout()
        layout.addLayout(middle_layout)
        self.table = QTableWidget(0, len(self.columns))
        middle_layout.addWidget(self.table)
        header_labels = self.columns
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        for column in range(1, self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellClicked.connect(self.cell_was_clicked)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.load_data_from_file()

    def show_protocol_selection_menu(self, row, column):

        def _set_protocol(row, column, protocol):
            item = QTableWidgetItem(protocol)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, column, item)

        menu = QMenu(self)
        action_socks = QAction('socks', self)
        action_http = QAction('http', self)
        action_socks.triggered.connect(lambda: _set_protocol(row, column, 'socks'))
        action_http.triggered.connect(lambda: _set_protocol(row, column, 'http'))
        menu.addAction(action_socks)
        menu.addAction(action_http)
        menu.popup(QCursor.pos())

    @pyqtSlot(str)
    def update_background(self, key='', row=-1):

        def _highlight_row(row, key):
            with Globals.routing_used_inbounds_keys_lock:
                if key in Globals.routing_used_inbounds_keys:
                    self.highlight_row(row, 'green')
                else:
                    self.highlight_row(row, 'white')

        rowCount = self.table.rowCount()
        if row >= 0 and row <= rowCount:
            if not key:
                key = f'{self.table.item(row, 2).text()}:{self.table.item(row, 3).text()}'
            _highlight_row(row, key)
            return
        if not key:
            return
        row = self.find_row_by_key(key)
        if row >= 0 and row <= rowCount:
            _highlight_row(row, key)

    def update_orange_datas(self):
        self.orange_datas.clear()
        for row in range(0, self.table.rowCount()):
            for col in range(1, self.table.columnCount()):
                cell_value = self.table.item(row, col).text()
                self.orange_datas[(row, col)] = cell_value

    def valid_datas(self):
        keys = {}
        remarkses = {}
        for row in range(self.table.rowCount()):
            protocol, address, port, user, password, remarks, key = self.parse_row_data(row)

            if not self.valid_protocol(protocol):
                self.highlight_row(row, 'red', 1)
                return False
            
            if not self.valid_address(address):
                self.highlight_row(row, 'red', 2)
                return False
            
            if not self.valid_port(port):
                self.highlight_row(row, 'red', 3)
                return False
            
            if key in keys:
                self.highlight_row(row, 'red', 2)
                self.highlight_row(row, 'red', 3)
                self.highlight_row(keys[key], 'red', 2)
                self.highlight_row(keys[key], 'red', 3)
                return False
            else:
                keys[key] = row
            
            if not self.valid_user(user):
                self.highlight_row(row, 'red', 4)
                return False
            
            if not self.valid_password(password):
                self.highlight_row(row, 'red', 5)
                return False
            
            if not self.valid_user_password(user, password):
                self.highlight_row(row, 'red', 4)
                self.highlight_row(row, 'red', 5)
                return False
            
            if  remarks:
                if remarks in remarkses:
                    self.highlight_row(row, 'red', 6)
                    self.highlight_row(remarkses[remarks], 'red', 6)
                    return False
                else:
                    remarkses[remarks] = row
            
            self.update_background(key, row)

        return True

    def valid_data_by_row(self, row):
        rowCount = self.table.rowCount()
        if row > rowCount or row < 0:
            return False
        
        protocol, address, port, user, password, remarks, key = self.parse_row_data(row)

        if not self.valid_protocol(protocol):
            self.highlight_row(row, 'red', 1)
            return False
        
        if not self.valid_address(address):
            self.highlight_row(row, 'red', 2)
            return False
        
        if not self.valid_port(port):
            self.highlight_row(row, 'red', 3)
            return False
        
        if not self.valid_user(user):
            self.highlight_row(row, 'red', 4)
            return False
        
        if not self.valid_password(password):
            self.highlight_row(row, 'red', 5)
            return False
        
        if not self.valid_user_password(user, password):
            self.highlight_row(row, 'red', 4)
            self.highlight_row(row, 'red', 5)
            return False
        
        duplicate_row = self.valid_key(row, address, port)
        if duplicate_row != -1:
            self.highlight_row(row, 'red', 2)
            self.highlight_row(row, 'red', 3)
            self.highlight_row(duplicate_row, 'red', 2)
            self.highlight_row(duplicate_row, 'red', 3)
            return False
        
        duplicate_row = self.valid_remarks(row, remarks)
        if duplicate_row != -1:
            self.highlight_row(row, 'red', 6)
            self.highlight_row(duplicate_row, 'red', 6)
            return False

        self.update_background(key, row)
        return True

    def valid_address(self, address):
        try:
            ipaddress.ip_address(address)
        except ValueError:
            Globals._Log.error(self.user, f'Invalid ip: {address}')
            return False
        return True
    
    def valid_key(self, row, address, port):
        if not address:
            return -1
        if not port:
            return -1
        for i in range(self.table.rowCount()):
            if row == i:
                continue
            if address != self.table.item(i, 2).text():
                continue
            if port != self.table.item(i, 3).text():
                continue
            return i
        return -1
        
    def valid_password(self, password):
        if ':' in password:
            Globals._Log.error(self.user, f'Invalid password: {password}')
            return False
        return True
        
    def valid_port(self, port):
        if not port.isdigit():
            Globals._Log.error(self.user, f'Invalid port: {port}')
            return False
        if not (0 < int(port) < 65536):
            Globals._Log.error(self.user, f'Invalid port: {port}')
            return False
        return True

    def valid_protocol(self, protocol):
        if protocol not in ['http', 'socks']:
            Globals._Log.error(self.user, f'Invalid protocol: {protocol}')
            return False
        return True
    
    def valid_remarks(self, row, remarks):
        if not remarks:
            return -1
        for i in range(self.table.rowCount()):
            if row == i:
                continue
            if remarks != self.table.item(i, 6).text():
                continue
            return i
        return -1
        
    def valid_user(self, user):
        if ':' in user:
            Globals._Log.error(self.user, f'Invalid user: {user}')
            return False
        return True
        
    def valid_user_password(self, user, password):
        if bool(user) != bool(password):
            Globals._Log.error(self.user, f'Invalid user/password combination: {user}, {password}')
            return False
        return True