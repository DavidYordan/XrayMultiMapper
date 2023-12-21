import base64
import ipaddress
import json
import os
import re
import requests
from PyQt6.QtCore import (
    pyqtSlot,
    Qt
)
from PyQt6.QtGui import (
    QAction,
    QColor,
    QCursor,
    QGuiApplication
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QHBoxLayout,
    QMenu,
    QMessageBox,
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

class OutboundsTab(QWidget):
    def __init__(self, parent, statistics_routings_signal):
        super().__init__(parent)
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        self.columns = ['Select', 'Protocol', 'Address', 'Port', 'User', 'Password', 'Encryption', 'Remarks', 'Tag']
        self.orange_datas = {}
        self.statistics_routings_signal = statistics_routings_signal
        self.user = 'OutboundsTab'
        self.setup_ui()

        Globals._Log.info(self.user, 'OutboundsTab successfully initialized.')

    def add_blank_row(self):

        def _make_checkbox():
            widget = QWidget()
            layout = QHBoxLayout(widget)
            chk_box = QCheckBox()
            layout.addWidget(chk_box)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(0, 0, widget)

        def _make_text_item(idx):
            item = QTableWidgetItem('')
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(0, idx, item)

        self.table.blockSignals(True)
        self.table.insertRow(0)
        _make_checkbox()
        for i in range(1, 9):
            _make_text_item(i)
        self.table.blockSignals(False)
        self.update_orange_datas()

        Globals._Log.info(self.user, f'New blank row added.')

    def add_row_outbounds(self, key):

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

        with Globals.outbounds_lock:
            protocol, address, port, user, password, encryption, remarks, tag, build_key = self.parse_dict_data(Globals.outbounds_dict[key])
        if key != build_key:
            self.delete_json(key)
            return False
        if not self.is_row_valid(protocol, address, port, user, password, encryption):
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
        _make_text_item(insert_position, 6, encryption)
        _make_text_item(insert_position, 7, remarks)
        _make_text_item(insert_position, 8, tag)
        self.table.blockSignals(False)

        Globals._Log.info(self.user, f'New row added with key: {key}.')

        return True

    def base64_decode(self, text):
        try:
            text = text.replace('_', '/').replace('-', '+')
            remain = len(text) % 4
            if remain == 1:
                text += '==='
            elif remain == 2:
                text += '=='
            elif remain == 3:
                text += '='
            return base64.urlsafe_b64decode(text).decode()
        except:
            return ''

    def cell_was_clicked(self, row, column):
        if column == 0:
            chk_box = self.get_checkbox(row)
            if not chk_box:
                return
            chk_box.setChecked(not chk_box.isChecked())
        if column == 1:
            self.show_protocol_selection_menu(row, column)

    def delete_json(self, key):
        with Globals.outbounds_lock:
            if key not in Globals.outbounds_dict.keys():
                return
            Globals.outbounds_tags.discard(Globals.outbounds_dict[key]['Tag'].lower())
            del Globals.outbounds_dict[key]

    def delete_row(self, row):
        address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
        port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
        self.table.removeRow(row)
        self.delete_json(f'{address}:{port}')
        Globals._Log.info(self.user, f'Row with key: {address}:{port} has been deleted.')

    def delete_selected_rows_outbounds(self):
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

    def find_row_by_tag(self, tag):
        for row in range(self.table.rowCount()):
            _tag = self.table.item(row, 8).text() if self.table.item(row, 3) else ''
            if not _tag:
                _tag = self.table.item(row, 7).text() if self.table.item(row, 3) else ''
                if not _tag:
                    address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
                    port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
                    _tag = f'{address}:{port}'
            if _tag == tag:
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
    
    @pyqtSlot
    def handle_highlight_row(self, tag):
        row = self.find_row_by_tag(tag)
        if row != -1:
            self.highlight_row(row, True)

    @pyqtSlot
    def handle_unhighlight_row(self, tag):
        row = self.find_row_by_tag(tag)
        if row != -1:
            self.highlight_row(row, False)

    def highlight_row(self, row, highlight=True):
        color = QColor(Qt.GlobalColor.green) if highlight else QColor(Qt.GlobalColor.white)
        self.table.blockSignals(True)
        for column in range(self.table.columnCount()):
            item = self.table.item(row, column)
            if item:
                item.setBackground(color)
        self.table.blockSignals(False)

    def is_row_valid(self, protocol, address, port, user, password, encryption):
        if not self.is_row_data_valid(protocol, address, port, user, password):
            return False
        if protocol == 'socks5':
            if (bool(user) != bool(password)):
                return False
        elif protocol == 'ss':
            if not all([encryption, password]):
                return False
        return True
    
    def is_row_data_valid(self, protocol, address, port, user, password):
        if bool(protocol) and protocol not in ['ss', 'socks5']:
            Globals._Log.error(self.user, f'Invalid protocol: {protocol}')
            return False
        if ':' in address or '@' in address or '.' not in address:
            Globals._Log.error(self.user, f'Invalid server address: {address}')
            return False
        if not port.isdigit():
            Globals._Log.error(self.user, f'Invalid port: {port}')
            return False
        if not (0 < int(port) < 65536):
            Globals._Log.error(self.user, f'Invalid port: {port}')
            return False
        if protocol == 'socks5':
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
            with Globals.outbounds_lock:
                for key in Globals.outbounds_dict.copy().keys():
                    if key in keys:
                        continue
                    Globals.outbounds_tags.discard(Globals.outbounds_dict[key]['Tag'].lower())
                    del Globals.outbounds_dict[key]

        def _load_json():
            with Globals.outbounds_lock:
                if not os.path.exists('outbounds.json'):
                    return
                with open('outbounds.json') as file:
                    datas = json.load(file)
                for key, data in datas.items():
                    protocol, address, port, user, password, encryption, remarks, tag, build_key = self.parse_dict_data(data)
                    if key != build_key:
                        continue
                    if not self.is_row_valid(protocol, address, port, user, password, encryption):
                        continue
                    Globals.outbounds_dict[key] = data
                    if not tag:
                        continue
                    Globals.outbounds_tags.add(tag.lower())
            Globals._Log.info(self.user, 'Outbound data loaded successfully from outbounds.json.')

        self.orange_datas.clear()
        with Globals.outbounds_lock:
            Globals.outbounds_dict.clear()
            Globals.outbounds_tags.clear()
        if not os.path.exists('outbounds.txt'):
            return
        _load_json()
        keys = set()
        with open('outbounds.txt', 'r') as file:
            for line in file:
                key = self.parse_link(line.strip())
                if not key:
                    Globals._Log.error(self.user, f'Invalid parameters provided: {line}')
                    continue
                keys.add(key)
        Globals._Log.info(self.user, 'Outbound data loaded successfully from outbounds.txt.')
        _clear_json(keys)
        self.update_orange_datas()

    def on_cell_changed(self, row, column):

        def _reset_value(row, column):
            self.table.blockSignals(True)
            self.table.item(row, column).setText(self.orange_datas[(row, column)])
            self.table.blockSignals(False)

        def _set_outbounds_data(protocol, address, port, user, password, encryption, remarks, tag, key):
            if not self.is_row_valid(protocol, address, port, user, password, encryption):
                return
            with Globals.outbounds_lock:
                Globals.outbounds_dict[key] = {
                    'Protocol': protocol,
                    'Address': address,
                    'Port': port,
                    'User': user,
                    'Password': password,
                    'Encryption': encryption,
                    'Remarks': remarks,
                    'Tag': tag
                }
                if not tag:
                    return
                Globals.outbounds_tags.add(tag.lower())

        def _set_orange_value(row, column):
            self.orange_datas[(row, column)] = self.table.item(row, column).text()

        if column == 0:
            return
        
        protocol, address, port, user, password, encryption, remarks, tag, key = self.parse_row_data(row)

        if not self.is_row_data_valid(protocol, address, port, user, password):
            _reset_value(row, column)
            return
        
        if column in [2, 3, 8]:
            with Globals.routing_used_outbound_options_lock:
                if key in Globals.routing_used_outbound_options:
                    _reset_value(row, column)
                    QMessageBox.warning(self, 'Error!', f'Please unbind {key} from routing_tab first.')
                    return
        
        if column in [2, 3]:
            if self.is_row_exists(address, port, ignore_row=row):
                _reset_value(row, column)
                return
            self.delete_json(f'{self.orange_datas[(row, 2)]}:{self.orange_datas[(row, 3)]}')
            _set_outbounds_data(protocol, address, port, user, password, encryption, remarks, tag, key)
            _set_orange_value(row, column)
            return
            
        if not all([address, port]):
            _reset_value(row, column)
            QMessageBox.warning(self, 'Error!', 'Please input address and port first!')
            return
        
        if column == 8:
            if tag.lower() in Globals.outbounds_tags:
                _reset_value(row, 8)
                QMessageBox.warning(self, 'Error!', 'Duplicate values found in tags.')
                return
            
        self.delete_json(key)
        _set_outbounds_data(protocol, address, port, user, password, encryption, remarks, tag, key)
        _set_orange_value(row, column)

    def parse_dict_data(self, data):
        protocol = data.get('Protocol', '')
        address = data.get('Address', '')
        port = data.get('Port', '')
        user = data.get('User', '')
        password = data.get('Password', '')
        encryption = data.get('Encryption', '')
        remarks = data.get('Remarks', '')
        tag = data.get('Tag', '')
        return protocol, address, port, user, password, encryption, remarks, tag, f'{address}:{port}'

    def parse_row_data(self, row):
        protocol = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
        address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
        port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
        user = self.table.item(row, 4).text() if self.table.item(row, 4) else ''
        password = self.table.item(row, 5).text() if self.table.item(row, 5) else ''
        encryption = self.table.item(row, 6).text() if self.table.item(row, 6) else ''
        remarks = self.table.item(row, 7).text() if self.table.item(row, 7) else ''
        tag = self.table.item(row, 8).text() if self.table.item(row, 8) else ''
        return protocol, address, port, user, password, encryption, remarks, tag, f'{address}:{port}'

    def parse_from_clipboard(self):
        try:
            clipboard = QGuiApplication.clipboard()
            mime_data = clipboard.mimeData()
            if not mime_data.hasText():
                return
            urls = mime_data.text().split('\n')
            for url in urls:
                self.parse_link(url)
            Globals._Log.info(self.user, 'Data successfully imported from clipboard.')
        except Exception as e:
            Globals._Log.info(self.user, f'Failed to import from clipboard: {e}')

    def parse_link(self, url):
        try:
            key = None
            if url.count('://') != 1:
                return key
            protocol, rest = url.split('://')
            if protocol == 'socks5':
                key = self.parse_socks5(rest)
            elif protocol == 'ss':
                key = self.parse_ss(rest)
            elif protocol in ['http', 'https']:
                if '/' not in rest:
                    return key
                self.parse_subscribe(url)
            return key
        except Exception as e:
            Globals._Log.error(self.user, f'Failed to parse link: {url}, Error: {e}')
            return None

    def parse_socks5(self, rest):

        def _make_outbounds_dict(address, port, user, password):
            if not self.is_row_valid('socks5', address, port, user, password, ''):
                return False
            key = f'{address}:{port}'
            with Globals.outbounds_lock:
                if key not in Globals.outbounds_dict:
                    Globals.outbounds_dict[key] = {'Tag': ''}
                Globals.outbounds_dict[key]['Protocol'] = 'socks5'
                Globals.outbounds_dict[key]['Address'] = address
                Globals.outbounds_dict[key]['Port'] = port
                Globals.outbounds_dict[key]['User'] = user
                Globals.outbounds_dict[key]['Password'] = password
                Globals.outbounds_dict[key]['Encryption'] = ''
                Globals.outbounds_dict[key]['Remarks'] = ''
            return key

        par1, par2, par3, par4 = ('', '', '', '')
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
                key = _make_outbounds_dict(par3, par4, par1, par2)
            elif '.' in par1 and par2.isdigit():
                key = _make_outbounds_dict(par1, par2, par3, par4)
            else:
                return False
        else:
            if par4:
                return False
            if '.' not in par1:
                return False
            if not par2.isdigit():
                return False
            key = _make_outbounds_dict(par1, par2, par3, par4)
        if not key:
            return False
        if not self.add_row_outbounds(key):
            return False
        return key

    def parse_ss(self, rest):

        def _make_outbounds_dict(server, port, method, password, remarks):
            if not self.is_row_valid('ss', server, port, '', password, method):
                return False
            key = f'{server}:{port}'
            with Globals.outbounds_lock:
                if key not in Globals.outbounds_dict:
                    Globals.outbounds_dict[key] = {'Tag': ''}
                Globals.outbounds_dict[key]['Protocol'] = 'ss'
                Globals.outbounds_dict[key]['Address'] = server
                Globals.outbounds_dict[key]['Port'] = port
                Globals.outbounds_dict[key]['User'] = ''
                Globals.outbounds_dict[key]['Password'] = password
                Globals.outbounds_dict[key]['Encryption'] = method
                Globals.outbounds_dict[key]['Remarks'] = remarks
            return key

        match = re.match(r'(?P<params>.+)@(?P<server>[^:]+):(?P<port>\d+)(?:#(?P<remarks>.+))?', rest)
        if not match:
            return False
        method_password = self.base64_decode(match.group('params'))
        if method_password.count(':') != 1:
            return False
        method, password = method_password.split(':')
        if not method or not password:
            return False
        server = match.group('server')
        if '.' not in server:
            return False
        port = match.group('port')
        remarks = unquote(match.group('remarks')).strip()
        key = _make_outbounds_dict(server, port, method, password, remarks)
        if not key:
            return False
        if not self.add_row_outbounds(key):
            return False
        return key

    def parse_subscribe(self, source):
        try:
            res = requests.get(source, headers=self.headers)
            if res.status_code != 200:
                return
            urls = res.text
            if '://' not in urls:
                urls = self.base64_decode(urls)
            if '://' not in urls:
                return
            url_list = urls.split('\n')
            for url in url_list:
                self.parse_link(url)
        except Exception as e:
            Globals._Log.info(self.user, f'Failed to parse subscription: {source}, Error: {e}')

    def reload_rows(self):
        self.table.blockSignals(True)
        for row in reversed(range(self.table.rowCount())):
            self.delete_row(row)
        self.table.blockSignals(False)
        self.load_data_from_file()
        Globals._Log.info(self.user, f'Reload complete.')

    def save_data_to_file(self):

        def _encode_ss(address, port, password, encryption, remarks):
            method_password = f'{encryption}:{password}'
            method_password_encoded = base64.urlsafe_b64encode(method_password.encode()).decode().rstrip("=")
            ss_link = f'ss://{method_password_encoded}@{address}:{port}'
            if remarks:
                remarks_encoded = quote(remarks)
                ss_link += f"#{remarks_encoded}"
            return ss_link
        
        lines = ''
        with Globals.outbounds_lock:
            datas = Globals.outbounds_dict.copy()
        for key, data in datas.items():
            protocol, address, port, user, password, encryption, remarks, tag, build_key = self.parse_dict_data(data)
            if key != build_key:
                self.delete_json(key)
                continue
            if not self.is_row_valid(protocol, address, port, user, password, encryption):
                self.delete_json(key)
                continue
            if protocol == 'socks5':
                lines += f'{protocol}://{address}:{port}'
                if all([user, password]):
                    lines += f'@{user}:{password}'
            elif protocol == 'ss':
                lines += _encode_ss(address, port, password, encryption, remarks)
            lines += '\n'
        try:
            with open('outbounds.json', 'w') as file:
                json.dump(Globals.outbounds_dict, file, indent=4)
            Globals._Log.info(self.user, 'Outbound data saved successfully to outbounds.json.')
            with open('outbounds.txt', 'w') as file:
                file.write(lines)
            Globals._Log.info(self.user, 'Outbound data saved successfully to outbounds.txt.')
        except Exception as e:
            Globals._Log.error(self.user, f'Failed to save Outbound data, Error: {e}')

    def set_protocol(self, row, column, protocol):
        item = QTableWidgetItem(protocol)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, column, item)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        button_add = QPushButton('Add')
        button_add.clicked.connect(self.show_add_menu)
        top_layout.addWidget(button_add)
        button_delete = QPushButton('Delete')
        button_delete.clicked.connect(self.delete_selected_rows_outbounds)
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

    def show_add_menu(self):
        menu = QMenu(self)
        action_blank_line = QAction('blank_line', self)
        action_from_clipboard = QAction('from_clipboard', self)

        action_blank_line.triggered.connect(self.add_blank_row)
        action_from_clipboard.triggered.connect(self.parse_from_clipboard)

        menu.addAction(action_blank_line)
        menu.addAction(action_from_clipboard)
        menu.popup(QCursor.pos())

    def show_protocol_selection_menu(self, row, column):
        menu = QMenu(self)
        action_socks5 = QAction('socks5', self)
        action_ss = QAction('ss', self)
        action_socks5.triggered.connect(lambda: self.set_protocol(row, column, 'socks5'))
        action_ss.triggered.connect(lambda: self.set_protocol(row, column, 'ss'))
        menu.addAction(action_socks5)
        menu.addAction(action_ss)
        menu.popup(QCursor.pos())

    def update_orange_datas(self):
        self.orange_datas.clear()
        for row in range(0, self.table.rowCount()):
            for col in range(1, self.table.columnCount()):
                cell_value = self.table.item(row, col).text() if self.table.item(row, col) else ''
                self.orange_datas[(row, col)] = cell_value
