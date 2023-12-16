import ipaddress
import json
import os
from PyQt6.QtCore import (
    pyqtSignal,
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
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from globals import Globals

class InboundsTab(QWidget):
    highlight_row_signal = pyqtSignal(str)
    unhighlight_row_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)


        self.columns = ['Select', 'Protocol', 'Address', 'Port', 'User', 'Password', 'Tag']
        self.highlight_row_signal.connect(self.handle_highlight_row)
        self.orange_datas = {}
        self.unhighlight_row_signal.connect(self.handle_unhighlight_row)
        self.user = 'InboundsTab'
        self.setup_ui()

        Globals._Log.info(self.user, 'InboundsTab successfully initialized.')

    def add_blank_row(self):
        ports = set()
        with Globals.inbounds_lock:
            for key, data in Globals.inbounds_dict.items():
                if data.get('Address', '') != '0.0.0.0':
                    continue
                row_port = data.get('Port', '')
                if not row_port:
                    continue
                ports.add(row_port)
            port = 30001
            while str(port) in ports:
                port += 1
            key = f'0.0.0.0:{port}'
            Globals.inbounds_dict[key] = {
                'Protocol': 'socks5',
                'Address': '0.0.0.0',
                'Port': str(port),
                'User': '',
                'Password': '',
                'Tag': ''
            }
        if not self.add_row_inbounds(key):
            return
        self.update_orange_datas()

        Globals._Log.info(self.user, f'New row added with key: {key}.')

    def add_row_inbounds(self, key):

        def _find_insert_position(address, port):
            row_count = self.table.rowCount()
            for row in range(row_count):
                row_address = self.table.item(row, 2).text()
                row_port = self.table.item(row, 3).text()
                if address < row_address or (address == row_address and port < row_port):
                    return row
            return row_count

        def _make_checkbox(insert_position):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            chk_box = QCheckBox()
            layout.addWidget(chk_box)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(insert_position, 0, widget)

        def _make_text_item(insert_position, idx, value):
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(insert_position, idx, item)

        with Globals.inbounds_lock:
            protocol, address, port, user, password, tag, build_key = self.parse_dict_data(Globals.inbounds_dict[key])
        if key != build_key:
            self.delete_json(key)
            return False
        if not self.is_row_valid(protocol, address, port, user, password):
            self.delete_json(key)
            return False
        if self.is_row_exists(address, port):
            self.delete_json(key)
            return False
        insert_position = _find_insert_position(address, port)

        self.table.blockSignals(True)
        self.table.insertRow(insert_position)
        _make_checkbox(insert_position)
        _make_text_item(insert_position, 1, protocol)
        _make_text_item(insert_position, 2, address)
        _make_text_item(insert_position, 3, port)
        _make_text_item(insert_position, 4, user)
        _make_text_item(insert_position, 5, password)
        _make_text_item(insert_position, 6, tag)
        self.table.blockSignals(False)

        Globals._Log.info(self.user, f'New row added with key: {key}.')

        return True

    def cell_was_clicked(self, row, column):
        if column == 0:
            chk_box = self.get_checkbox(row)
            if not chk_box:
                return
            chk_box.setChecked(not chk_box.isChecked())
        if column == 1:
            self.show_protocol_selection_menu(row, column)

    def delete_json(self, key):
        with Globals.inbounds_lock:
            if key not in Globals.inbounds_dict.keys():
                return
            Globals.inbounds_tags.discard(Globals.inbounds_dict[key]['Tag'].lower())
            del Globals.inbounds_dict[key]

    def delete_row(self, row):
        address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
        port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
        self.table.removeRow(row)
        self.delete_json(f'{address}:{port}')
        Globals._Log.info(self.user, f'Row with key: {address}:{port} has been deleted.')

    def delete_selected_rows_inbounds(self):
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

    def find_row_by_address_port(self, address_port):
        for row in range(self.table.rowCount()):
            address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
            port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
            if f'{address}:{port}' == address_port:
                return row
        return -1
    
    def get_checkbox(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget is None:
            return None
        chk_box = widget.layout().itemAt(0).widget()
        if isinstance(chk_box, QCheckBox):
            return chk_box
        return None
    
    def handle_highlight_row(self, address_port):
        row = self.find_row_by_address_port(address_port)
        if row != -1:
            self.highlight_row(row, True)

    def handle_unhighlight_row(self, address_port):
        row = self.find_row_by_address_port(address_port)
        if row != -1:
            self.highlight_row(row, False)

    def highlight_row(self, row, highlight=True):
        color = QColor(Qt.GlobalColor.green) if highlight else QColor(Qt.GlobalColor.white)
        for column in range(self.table.columnCount()):
            item = self.table.item(row, column)
            if item:
                item.setBackground(color)

    def is_row_valid(self, protocol, address, port, user, password):
        if not self.is_row_data_valid(protocol, address, port, user, password):
            return False
        if (bool(user) != bool(password)):
            return False
        return True
    
    def is_row_data_valid(self, protocol, address, port, user, password):
        if protocol not in ['http', 'socks5']:
            Globals._Log.error(self.user, f'Invalid protocol: {protocol}')
            return False
        try:
            ipaddress.ip_address(address)
        except ValueError:
            Globals._Log.error(self.user, f'Invalid ip: {address}')
            return False
        if not port.isdigit():
            Globals._Log.error(self.user, f'Invalid port: {port}')
            return False
        if not (0 < int(port) < 65536):
            Globals._Log.error(self.user, f'Invalid port: {port}')
            return False
        for param in [user, password]:
            if ':' in param or '@' in param:
                Globals._Log.error(self.user, f'Invalid user/password combination: {user}, {password}')
                return False
        return True
    
    def is_row_exists(self, address, port, ignore_row=None):
        for row in range(self.table.rowCount()):
            if row == ignore_row:
                continue
            row_address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
            if address != row_address:
                continue
            row_port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
            if port != row_port:
                continue
            return True
        return False

    def load_data_from_file(self):

        def _clear_json(keys):
            with Globals.inbounds_lock:
                for key in Globals.inbounds_dict.copy().keys():
                    if key in keys:
                        continue
                    Globals.inbounds_tags.discard(Globals.inbounds_dict[key]['Tag'].lower())
                    del Globals.inbounds_dict[key]

        def _load_json():
            with Globals.inbounds_lock:
                if not os.path.exists('inbounds.json'):
                    return
                with open('inbounds.json', 'r') as file:
                    datas = json.load(file)
                for key, data in datas.items():
                    protocol, address, port, user, password, tag, build_key = self.parse_dict_data(data)
                    if key != build_key:
                        continue
                    if not self.is_row_valid(protocol, address, port, user, password):
                        continue
                    Globals.inbounds_dict[key] = data
                    if not tag:
                        continue
                    Globals.inbounds_tags.add(tag.lower())
            Globals._Log.info(self.user, 'Inbound data loaded successfully from inbounds.json.')

        self.orange_datas.clear()
        with Globals.inbounds_lock:
            Globals.inbounds_dict.clear()
            Globals.inbounds_tags.clear()
        if not os.path.exists('inbounds.txt'):
            return
        _load_json()
        keys = set()
        with open('inbounds.txt', 'r') as file:
            for line in file:
                key = self.parse_link(line.strip())
                if not key:
                    Globals._Log.error(self.user, f'Invalid parameters provided: {line}')
                    continue
                keys.add(key)
        Globals._Log.info(self.user, 'Inbound data loaded successfully from inbounds.txt.')
        _clear_json(keys)
        self.update_orange_datas()

    def on_cell_changed(self, row, column):

        def _reset_value(row, column):
            self.table.blockSignals(True)
            self.table.item(row, column).setText(self.orange_datas[(row, column)])
            self.table.blockSignals(False)

        def _set_inbounds_data(protocol, address, port, user, password, tag, key):
            if not self.is_row_valid(protocol, address, port, user, password):
                return
            with Globals.inbounds_lock:
                Globals.inbounds_dict[key] = {
                    'Protocol': protocol,
                    'Address': address,
                    'Port': port,
                    'User': user,
                    'Password': password,
                    'Tag': tag
                }
                if not tag:
                    return
                Globals.inbounds_tags.add(tag.lower())

        def _set_orange_value(row, column):
            self.orange_datas[(row, column)] = self.table.item(row, column).text()

        if column == 0:
            return
        
        protocol, address, port, user, password, tag, key = self.parse_row_data(row)

        if not self.is_row_data_valid(protocol, address, port, user, password):
            _reset_value(row, column)
            return
        
        if column in [2, 3, 6]:
            with Globals.routing_used_inbound_options_lock:
                if key in Globals.routing_used_inbound_options:
                    _reset_value(row, column)
                    QMessageBox.warning(self, 'Error!', f'Please unbind {key} from routing_tab first.')
                    return
        
        if column in [2, 3]:
            if self.is_row_exists(address, port, ignore_row=row):
                _reset_value(row, column)
                return
            self.delete_json(f'{self.orange_datas[(row, 2)]}:{self.orange_datas[(row, 3)]}')
            _set_inbounds_data(protocol, address, port, user, password, tag, key)
            _set_orange_value(row, column)
            return
            
        if not all([address, port]):
            _reset_value(row, column)
            QMessageBox.warning(self, 'Error!', 'Please input address and port first!')
            return
        
        if column == 6:
            if tag.lower() in Globals.inbounds_tags:
                _reset_value(row, 6)
                QMessageBox.warning(self, 'Error!', 'Duplicate values found in tags.')
                return
            
        self.delete_json(key)
        _set_inbounds_data(protocol, address, port, user, password, tag, key)
        _set_orange_value(row, column)

    def parse_dict_data(self, data):
        protocol = data.get('Protocol', '')
        address = data.get('Address', '')
        port = data.get('Port', '')
        user = data.get('User', '')
        password = data.get('Password', '')
        tag = data.get('Tag', '')
        return protocol, address, port, user, password, tag, f'{address}:{port}'

    def parse_row_data(self, row):
        protocol = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
        address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
        port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
        user = self.table.item(row, 4).text() if self.table.item(row, 4) else ''
        password = self.table.item(row, 5).text() if self.table.item(row, 5) else ''
        tag = self.table.item(row, 6).text() if self.table.item(row, 6) else ''
        return protocol, address, port, user, password, tag, f'{address}:{port}'
        
    def parse_link(self, url):

        def _make_inbounds_dict(protocol, address, port, user, password):
            if not self.is_row_valid(protocol, address, port, user, password):
                return False
            key = f'{address}:{port}'
            with Globals.inbounds_lock:
                if key not in Globals.inbounds_dict:
                    Globals.inbounds_dict[key] = {'Tag': ''}
                Globals.inbounds_dict[key]['Protocol'] = protocol
                Globals.inbounds_dict[key]['Address'] = address
                Globals.inbounds_dict[key]['Port'] = port
                Globals.inbounds_dict[key]['User'] = user
                Globals.inbounds_dict[key]['Password'] = password
            return key

        par1, par2, par3, par4 = ('', '', '', '')
        protocol, rest = url.split("://")
        if protocol not in ['http', 'socks5']:
            return False
        if rest.count('@') == 1 and rest.count(':') == 2:
            rest_l, rest_r = rest.split('@')
            par1, par2 = rest_l.split(':')
            par3, par4 = rest_r.split(':')
        elif rest.count(':') == 3:
            par1, par2, par3, par4 = rest.split(':')
        elif rest.count(':') == 1:
            par1, par2 = rest.split(':')
        else:
            return False
        if not par1 or not par2:
            return False
        if par3:
            if not par4:
                return False
            if '.' in par3 and par4.isdigit():
                if '.' in par1 and par2.isdigit():
                    return False
                key = _make_inbounds_dict(protocol, par3, par4, par1, par2)
            elif '.' in par1 and par2.isdigit():
                key = _make_inbounds_dict(protocol, par1, par2, par3, par4)
            else:
                return False
        else:
            if par4:
                return False
            if '.' not in par1:
                return False
            if not par2.isdigit():
                return False
            key = _make_inbounds_dict(protocol, par1, par2, par3, par4)
        if not key:
            return False
        if not self.add_row_inbounds(key):
            return False
        return key

    def reload_rows(self):
        self.table.blockSignals(True)
        for row in reversed(range(self.table.rowCount())):
            self.delete_row(row)
        self.table.blockSignals(False)
        self.load_data_from_file()
        Globals._Log.info(self.user, f'Reload complete.')

    def save_data_to_file(self):
        lines = ''
        with Globals.inbounds_lock:
            datas = Globals.inbounds_dict.copy()
        for key, data in datas.items():
            protocol, address, port, user, password, tag, build_key = self.parse_dict_data(data)
            if key != build_key:
                self.delete_json(key)
                continue
            if not self.is_row_valid(protocol, address, port, user, password):
                self.delete_json(key)
                continue
            lines += f'{protocol}://{address}:{port}'
            if all([user, password]):
                lines += f'@{user}:{password}'
            lines += '\n'
        try:
            with open('inbounds.json', 'w') as file:
                json.dump(Globals.inbounds_dict, file, indent=4)
            Globals._Log.info(self.user, 'Inbound data saved successfully to inbounds.json.')
            with open('inbounds.txt', 'w') as file:
                file.write(lines)
            Globals._Log.info(self.user, 'Inbound data saved successfully to inbounds.txt.')
        except Exception as e:
            Globals._Log.error(self.user, f'Failed to save Inbound data, Error: {e}')

    def set_protocol(self, row, column, protocol):
        item = QTableWidgetItem(protocol)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, column, item)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        button_add = QPushButton('Add')
        button_add.clicked.connect(self.add_blank_row)
        top_layout.addWidget(button_add)
        button_delete = QPushButton('Delete')
        button_delete.clicked.connect(self.delete_selected_rows_inbounds)
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
        menu = QMenu(self)
        action_socks5 = QAction('socks5', self)
        action_http = QAction('http', self)
        action_socks5.triggered.connect(lambda: self.set_protocol(row, column, 'socks5'))
        action_http.triggered.connect(lambda: self.set_protocol(row, column, 'http'))
        menu.addAction(action_socks5)
        menu.addAction(action_http)
        menu.popup(QCursor.pos())

    def update_orange_datas(self):
        self.orange_datas.clear()
        for row in range(0, self.table.rowCount()):
            for col in range(1, self.table.columnCount()):
                cell_value = self.table.item(row, col).text() if self.table.item(row, col) else ''
                self.orange_datas[(row, col)] = cell_value
