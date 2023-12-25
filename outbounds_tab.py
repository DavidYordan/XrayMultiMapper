import base64
import json
import os
import re
import requests
from PyQt6.QtCore import (
    pyqtSignal,
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
    QAbstractItemView,
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
    parse_qs,
    quote,
    unquote,
    urlparse
)

from globals import Globals
from outbounds_dialog import OutboundsDialog

class OutboundsTab(QWidget):
    add_row_signal = pyqtSignal(dict)
    modify_row_signal = pyqtSignal(dict, int)

    def __init__(
            self,
            parent,
            outbounds_tag_changed_signal
        ):
        super().__init__(parent)
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        self.columns = ['select', 'source_tag', 'protocol', 'address', 'port', 'encryption', 'net', 'security', 'remarks']
        self.orange_datas = {}
        self.outbounds = {}
        self.outbounds_tag_changed_signal = outbounds_tag_changed_signal
        self.user = 'OutboundsTab'
        self.setup_ui()

        self.add_row_signal.connect(self.add_row)
        self.modify_row_signal.connect(self.modify_row_outbounds)

        Globals._Log.info(self.user, 'OutboundsTab successfully initialized.')

    @pyqtSlot(dict)
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
            elif col == 8:
                self.table.item(insert_position, 8).setText(data.get('remarks', '').replace('|', '').lower())
            else:
                self.table.item(insert_position, col).setText(data.get(column, ''))
        self.table.blockSignals(False)

        self.update_orange_datas()

        with Globals.outbounds_lock:
            Globals.outbounds_dict[key] = data

        self.valid_data_by_row(insert_position)

        Globals._Log.info(self.user, f'New row added with key: {key}.')

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
            return text

    def cell_was_clicked(self, row, column):
        if column == 0:
            chk_box = self.get_checkbox(row)
            if not chk_box:
                return
            chk_box.setChecked(not chk_box.isChecked())
        elif column == 1:
            self.set_checked_by_source_tag(row)

    def cell_was_double_clicked(self, index):
        protocol = self.table.item(index.row(), 2).text()
        OutboundsDialog(self, self.modify_row_signal, protocol, index.row())

    def delete_data(self, key):
        with Globals.outbounds_lock:
            if key in Globals.outbounds_dict.keys():
                del Globals.outbounds_dict[key]

    def delete_row(self, row):
        address = self.table.item(row, 3).text()
        port = self.table.item(row, 4).text()
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
            address = self.table.item(row, 3).text()
            port = self.table.item(row, 4).text()
            if key == f'{address}:{port}':
                return row
        return -1
    
    def find_source_tag(self, key, source=''):
        source = source if source else self.outbounds.get(key, {}).get('source', '')
        source_tag = self.outbounds.get(key, {}).get('source_tag', '')
        source_tags = set()
        with Globals.outbounds_lock:
            for _, data in Globals.outbounds_dict.items():
                _source_tag = data.get('source_tag', '')
                if _source_tag:
                    source_tags.add(_source_tag)
                _source = data.get('source', '')
                if not _source:
                    continue
                if source != _source:
                    continue
                if _source_tag:
                    return _source_tag
        if source_tag:
            return source_tag
        if not source:
            return ''
        num = 1
        while f'sub-{num:03}' in source_tags:
            num += 1
        return f'sub-{num:03}'
    
    def get_checkbox(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget is None:
            return None
        chk_box = widget.layout().itemAt(0).widget()
        if isinstance(chk_box, QCheckBox):
            return chk_box
        return None
    
    def highlight_row(self, row, color_key, col=-1):
        if color_key == 'blue':
            color = QColor(Qt.GlobalColor.blue)
        elif color_key == 'green':
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
            with Globals.outbounds_lock:
                Globals.outbounds_dict.clear()
            self.orange_datas.clear()

            self.table.blockSignals(True)
            while self.table.rowCount() > 0:
                self.table.removeRow(0)
            self.table.blockSignals(False)

        def _load_json():
            self.outbounds.clear()
            if not os.path.exists('outbounds.json'):
                return
            with open('outbounds.json', 'r') as file:
                datas = json.load(file)
            for key, data in datas.items():
                if key != f'{data.get("address", "")}:{data.get("port", "")}':
                    continue
                self.outbounds[key] = data
                remarks = data['remarks'].replace('|', '').lower()
                self.outbounds[key]['remarks'] = remarks
            Globals._Log.info(self.user, 'outbounds datas loaded successfully from outbounds.json.')

        _clear_table()
        _load_json()
        if not os.path.exists('outbounds.txt'):
            return
        with open('outbounds.txt', 'r') as file:
            for line in file:
                self.parse_link(line.strip())
        Globals._Log.info(self.user, 'outbound data loaded successfully from outbounds.txt.')

    @pyqtSlot(dict, int)
    def modify_row_outbounds(self, data, row):
        if row < 0:
            Globals._Log.error(self.user, f'Invalid row: {row}')
            return
        if row > self.table.rowCount():
            Globals._Log.error(self.user, f'Invalid row: {row}')
            return
        
        for col, column in enumerate(self.columns):
            if col == 0:
                continue
            old_value = self.table.item(row, col).text()
            new_value = data[column]
            if old_value == new_value:
                continue
            self.table.item(row, col).setText(new_value)

        Globals._Log.info(self.user, f'New row added with row: {row}.')

    def parse_row_data(self, row):
        source_tag = self.table.item(row, 1).text()
        protocol = self.table.item(row, 2).text()
        address = self.table.item(row, 3).text()
        port = self.table.item(row, 4).text()
        encryption = self.table.item(row, 5).text()
        net = self.table.item(row, 6).text()
        security = self.table.item(row, 7).text()
        remarks = self.table.item(row, 8).text()
        return source_tag, protocol, address, port, encryption, net, security, remarks, f'{address}:{port}'

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

    def parse_link(self, url, source=''):
        try:
            if url.count('://') != 1:
                return
            protocol, rest = url.split('://')
            if protocol == 'socks':
                self.parse_socks(rest, source)
            elif protocol == 'ss':
                self.parse_shadowsocks(rest, source)
            elif protocol == 'trojan':
                self.parse_trojan(rest, source)
            elif protocol == 'vless':
                self.parse_vless(rest, source)
            elif protocol == 'vmess':
                self.parse_vmess(rest, source)
            elif protocol in ['http', 'https']:
                if '/' not in rest:
                    return
                self.parse_subscribe(url)
        except Exception as e:
            Globals._Log.error(self.user, f'Failed to parse link: {url}, Error: {e}')

    def parse_socks(self, rest, source):
        match = re.match(r'(?P<params>.+)@(?P<address>[^:]+):(?P<port>\d+)(?:#(?P<remarks>.+))?', rest)
        if not match:
            return
        user_password = self.base64_decode(match.group('params'))
        if user_password.count(':') != 1:
            return
        user, password = user_password.split(':')
        address = match.group('address')
        port = match.group('port')
        key = f'{address}:{port}'
        remarks = unquote(match.group('remarks')).strip() if match.group('remarks') else ''
        source_tag = self.find_source_tag(key, source)
        self.add_row({
            'source_tag': source_tag,
            'source': source,
            'protocol': 'socks',
            'address': address,
            'port': port,
            'encryption': '',
            'password': password,
            'net': '',
            'security': '',
            'user': user,
            'remarks': remarks
        })

    def parse_shadowsocks(self, rest, source):
        match = re.match(r'(?P<params>.+)@(?P<server>[^:]+):(?P<port>\d+)(?:#(?P<remarks>.+))?', rest)
        if not match:
            return
        encryption_password = self.base64_decode(match.group('params'))
        if encryption_password.count(':') != 1:
            return
        encryption, password = encryption_password.split(':')
        address = match.group('server')
        port = match.group('port')
        key = f'{address}:{port}'
        remarks = unquote(match.group('remarks')).strip() if match.group('remarks') else ''
        source = source if source else self.outbounds.get(key, {}).get('source', '')
        source_tag = self.find_source_tag(key, source)
        self.add_row({
            'source_tag': source_tag,
            'source': source,
            'protocol': 'shadowsocks',
            'address': address,
            'port': port,
            'encryption': encryption,
            'password': password,
            'net': '',
            'security': '',
            'remarks': remarks
        })

    def parse_subscribe(self, source):
        try:
            res = requests.get(source, headers=self.headers)
            if res.status_code != 200:
                return
            urls = res.text
            if not urls:
                return
            if '://' not in urls:
                urls = self.base64_decode(urls)
            if '://' not in urls:
                return
            url_list = urls.split('\n')
            for url in url_list:
                if not url:
                    return
                if '://' not in url:
                    url = self.base64_decode(url)
                if '://' not in url:
                    continue
                self.parse_link(url, source)
        except Exception as e:
            Globals._Log.info(self.user, f'Failed to parse subscription: {source}, Error: {e}')

    def parse_trojan(self, rest, source):
        base, _, fragment = rest.partition('#')
        parsed_url = urlparse(f'trojan://{base}')
        params = parse_qs(parsed_url.query)

        password = parsed_url.username
        address = parsed_url.hostname
        port = str(parsed_url.port)
        key = f'{address}:{port}'
        remarks = unquote(fragment).strip() if fragment else ''
        source = source if source else self.outbounds.get(key, {}).get('source', '')
        source_tag = self.find_source_tag(key, source)

        additional_params = {k: v[0] for k, v in params.items()}

        self.add_row({
            'source_tag': source_tag,
            'source': source,
            'protocol': 'trojan',
            'address': address,
            'port': port,
            'encryption': '',
            'password': password,
            'net': additional_params.get('type', ''),
            'security': '',
            'remarks': remarks,
            **additional_params
        })

    def parse_vless(self, rest, source):
        base, _, fragment = rest.partition('#')
        parsed_url = urlparse(f'vless://{base}')
        params = parse_qs(parsed_url.query)

        uuid = parsed_url.username
        address = parsed_url.hostname
        port = str(parsed_url.port)
        key = f'{address}:{port}'
        remarks = unquote(fragment).strip() if fragment else ''
        source = source if source else self.outbounds.get(key, {}).get('source', '')
        source_tag = self.find_source_tag(key, source)

        additional_params = {k: v[0] for k, v in params.items()}

        self.add_row({
            'source_tag': source_tag,
            'source': source,
            'protocol': 'vless',
            'address': address,
            'port': port,
            'encryption': '',
            'password': '',
            'net': additional_params.get('type', ''),
            'security': '',
            'remarks': remarks,
            'uuid': uuid,
            **additional_params
        })

    def parse_vmess(self, rest, source):
        json_str = self.base64_decode(rest)
        data = json.loads(json_str)
        address = data.get('add', '')
        port = data.get('port', '')
        key = f'{address}:{port}'
        remarks = data.get('ps', '')
        source = source if source else self.outbounds.get(key, {}).get('source', '')
        source_tag = self.find_source_tag(key, source)

        self.add_row({
            'source_tag': source_tag,
            'source': source,
            'protocol': 'vmess',
            'address': address,
            'port': port,
            'encryption': data.get('scy', ''),
            'password': '',
            'net': '',
            'security': data.get('tls', ''),
            'remarks': remarks,
            **data
        })

    def reload_rows(self):
        self.load_data_from_file()
        Globals._Log.info(self.user, f'Reload complete.')

    def save_data_to_file(self):

        def _encode_shadowsocks(address, port):
            key = f'{address}:{port}'
            encryption = self.outbounds[key]['encryption']
            password = self.outbounds[key]['password']
            remarks = self.outbounds[key]['remarks']
            encryption_password = f'{encryption}:{password}'
            encryption_password_encoded = base64.urlsafe_b64encode(encryption_password.encode()).decode().rstrip("=")
            url = f'ss://{encryption_password_encoded}@{address}:{port}'
            if remarks:
                url += f'#{quote(remarks)}'
            return url
        
        def _encode_socks(address, port):
            key = f'{address}:{port}'
            user = self.outbounds[key]['user']
            password = self.outbounds[key]['password']
            remarks = self.outbounds[key]['remarks']
            user_password = f'{user}:{password}'
            user_password_encoded = base64.urlsafe_b64encode(user_password.encode()).decode().rstrip("=")
            url = f'socks://{user_password_encoded}@{address}:{port}'
            if remarks:
                url += f'#{quote(remarks)}'
            return url
        
        def _encode_trojan(address, port):
            key = f'{address}:{port}'
            data = self.outbounds[key]
            password = data['password']
            remarks = data['remarks']
            url = f'trojan://{password}@{address}:{port}'

            excluded_keys = {'source_tag', 'source', 'protocol', 'address', 'port', 'encryption', 'password', 'net', 'remarks'}
            query_params = {k: v for k, v in data.items() if k not in excluded_keys and v}
            params_string = '&'.join([f'{k}={quote(str(v))}' for k, v in query_params.items()])
            url += f'?{params_string}'

            if remarks:
                url += f'#{quote(remarks)}'

            return url
        
        def _encode_vless(address, port):
            key = f'{address}:{port}'
            data = self.outbounds[key]
            uuid = data['uuid']
            remarks = data['remarks']
            url = f'vless://{uuid}@{address}:{port}'

            excluded_keys = {'source_tag', 'source', 'protocol', 'address', 'port', 'password', 'net', 'remarks', 'uuid'}
            query_params = {k: v for k, v in data.items() if k not in excluded_keys and v}
            params_string = '&'.join([f'{k}={quote(str(v))}' for k, v in query_params.items()])
            url += f'?{params_string}'

            if remarks:
                url += f'#{quote(remarks)}'

            return url
        
        def _encode_vmess(address, port):
            key = f'{address}:{port}'
            data = self.outbounds[key]

            excluded_keys = {'source_tag', 'source', 'protocol', 'address', 'encryption', 'password', 'security', 'remarks'}
            vmess_config = {k: v for k, v in data.items() if k not in excluded_keys}

            json_str = json.dumps(vmess_config)

            encoded_str = base64.urlsafe_b64encode(json_str.encode()).decode()

            url = f'vmess://{encoded_str}'

            return url
        
        if not self.valid_datas():
            Globals._Log.error(self.user, 'Failed to save outbounds datas.')
            return
        with Globals.outbounds_lock:
            self.outbounds = Globals.outbounds_dict

        lines = ''
        for row in range(self.table.rowCount()):
            protocol = self.table.item(row, 2).text()
            address = self.table.item(row, 3).text()
            port = self.table.item(row, 4).text()
            if protocol == 'socks':
                lines += _encode_socks(address, port)
            elif protocol == 'shadowsocks':
                lines += _encode_shadowsocks(address, port)
            elif protocol == 'trojan':
                lines += _encode_trojan(address, port)
            elif protocol == 'vless':
                lines += _encode_vless(address, port)
            elif protocol == 'vmess':
                lines += _encode_vmess(address, port)
            else:
                continue
            lines += '\n'

        try:
            with open('outbounds.json', 'w') as file:
                json.dump(self.outbounds, file, indent=4)
            Globals._Log.info(self.user, 'outbounds datas saved successfully to outbounds.json.')
            with open('outbounds.txt', 'w') as file:
                file.write(lines)
            Globals._Log.info(self.user, 'outbounds datas saved successfully to outbounds.txt.')
        except Exception as e:
            Globals._Log.error(self.user, f'Failed to save outbounds datas, Error: {e}')

    def set_checked_by_source_tag(self, row):
        chk_box = self.get_checkbox(row)
        if not chk_box:
            return
        checked = not chk_box.isChecked()
        source_tag = self.table.item(row, 1).text()
        if not source_tag:
            chk_box.setChecked(checked)
            return
        for _row in range(self.table.rowCount()):
            chk_box = self.get_checkbox(_row)
            if source_tag == self.table.item(_row, 1).text():
                chk_box.setChecked(checked)
            else:
                chk_box.setChecked(False)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        button_add = QPushButton('Add')
        button_add.clicked.connect(self.show_add_menu)
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
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setColumnWidth(0, 50)
        for column in range(1, self.table.columnCount()):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeMode.ResizeToContents)
        self.table.cellClicked.connect(self.cell_was_clicked)
        self.table.doubleClicked.connect(self.cell_was_double_clicked)
        self.load_data_from_file()

    def show_add_menu(self):
        menu = QMenu(self)
        action_add_shadowsocks = QAction('shadowsocks', self)
        action_add_socks = QAction('socks', self)
        action_add_vless = QAction('vless', self)
        action_add_vmess = QAction('vmess', self)
        action_add_trojan = QAction('trojan', self)
        action_from_clipboard = QAction('from_clipboard', self)

        action_add_shadowsocks.triggered.connect(lambda: OutboundsDialog(self, self.add_row_signal, 'shadowsocks'))
        action_add_socks.triggered.connect(lambda: OutboundsDialog(self, self.add_row_signal, 'socks'))
        action_add_trojan.triggered.connect(lambda: OutboundsDialog(self, self.add_row_signal, 'trojan'))
        action_add_vless.triggered.connect(lambda: OutboundsDialog(self, self.add_row_signal, 'vless'))
        action_add_vmess.triggered.connect(lambda: OutboundsDialog(self, self.add_row_signal, 'vmess'))
        action_from_clipboard.triggered.connect(self.parse_from_clipboard)

        menu.addAction(action_add_shadowsocks)
        menu.addAction(action_add_socks)
        menu.addAction(action_add_vless)
        menu.addAction(action_add_vmess)
        menu.addAction(action_add_trojan)
        menu.addAction(action_from_clipboard)
        menu.popup(QCursor.pos())

    @pyqtSlot(str)
    def update_background(self, key='', row=-1):

        def _highlight_row(row, key):
            with Globals.routing_used_outbounds_keys_lock:
                if key not in Globals.routing_used_outbounds_keys:
                    self.highlight_row(row, 'white')
                    return
                if key in Globals.routing_used_outbounds_through_keys:
                    self.highlight_row(row, 'blue')
                    return
                self.highlight_row(row, 'green')

        rowCount = self.table.rowCount()
        if row >= 0 and row <= rowCount:
            if not key:
                key = f'{self.table.item(row, 3).text()}:{self.table.item(row, 4).text()}'
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
                cell_value = self.table.item(row, col).text() if self.table.item(row, col) else ''
                self.orange_datas[(row, col)] = cell_value

    def valid_datas(self):
        keys = {}
        remarkses = {}
        for row in range(self.table.rowCount()):
            source_tag, protocol, address, port, encryption, net, security, remarks, key = self.parse_row_data(row)
        
            if not self.valid_protocol(protocol):
                self.highlight_row(row, 'red', 2)
                return False
            
            if not self.valid_address(address):
                self.highlight_row(row, 'red', 3)
                return False
            
            if not self.valid_port(port):
                self.highlight_row(row, 'red', 4)
                return False
            
            if key in keys:
                self.highlight_row(row, 'red', 3)
                self.highlight_row(row, 'red', 4)
                self.highlight_row(keys[key], 'red', 3)
                self.highlight_row(keys[key], 'red', 4)
                return False
            else:
                keys[key] = row
            
            if not self.valid_encryption(encryption):
                self.highlight_row(row, 'red', 5)
                return False
            
            if not self.valid_net(net):
                self.highlight_row(row, 'red', 6)
                return False
            
            if not self.valid_security(security):
                self.highlight_row(row, 'red', 7)
                return False
            
            if remarks:
                if remarks in remarkses:
                    self.highlight_row(row, 'red', 8)
                    self.highlight_row(remarkses[remarks], 'red', 8)
                    return False
                else:
                    remarkses[remarks] = row
            
            self.update_background(key, row)

        return True

    def valid_data_by_row(self, row):
        rowCount = self.table.rowCount()
        if row > rowCount or row < 0:
            return False
        
        source_tag, protocol, address, port, encryption, net, security, remarks, key = self.parse_row_data(row)
        
        if not self.valid_protocol(protocol):
            self.highlight_row(row, 'red', 2)
            return False
        
        if not self.valid_address(address):
            self.highlight_row(row, 'red', 3)
            return False
        
        if not self.valid_port(port):
            self.highlight_row(row, 'red', 4)
            return False
        
        if not self.valid_encryption(encryption):
            self.highlight_row(row, 'red', 5)
            return False
        
        if not self.valid_net(net):
            self.highlight_row(row, 'red', 6)
            return False
        
        if not self.valid_security(security):
            self.highlight_row(row, 'red', 7)
            return False
        
        duplicate_row = self.valid_key(row, address, port)
        if duplicate_row != -1:
            self.highlight_row(row, 'red', 3)
            self.highlight_row(row, 'red', 4)
            self.highlight_row(duplicate_row, 'red', 3)
            self.highlight_row(duplicate_row, 'red', 4)
            return False
        
        duplicate_row = self.valid_remarks(row, remarks)
        if duplicate_row != -1:
            self.highlight_row(row, 'red', 8)
            self.highlight_row(duplicate_row, 'red', 8)
            return False

        self.update_background(key, row)
        return True

    def valid_address(self, address):
        if not address:
            Globals._Log.error(self, 'Error!', 'Address field cannot be empty.')
            return False
        if '.' not in address:
            Globals._Log.error(self.user, f'Invalid server: {address}')
            return False
        return True
    
    def valid_encryption(self, encryption):
        if encryption not in ['', 'auto', 'none', 'plain', 'aes-128-gcm', 'chacha20-poly1305', 'chacha20-ietf-poly1305', 'xchacha20-poly1305',
                              'xchacha20-ietf-poly1305', '2022-blake3-aes-128-gcm', '2022-blake3-aes-256-gcm', '2022-blake3-chacha20-poly1305']:
            Globals._Log.error(self.user, f'Invalid encryption: {encryption}')
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
            if address != self.table.item(i, 3).text():
                continue
            if port != self.table.item(i, 4).text():
                continue
            return i
        return -1
    
    def valid_net(self, net):
        if net not in ['', 'tcp', 'kcp', 'ws', 'h2', 'quic', 'grpc']:
            Globals._Log.error(self.user, f'Invalid transfer protocol: {net}')
            return False
        return True
        
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
        if protocol not in ['shadowsocks', 'socks', 'trojan', 'vless', 'vmess']:
            Globals._Log.error(self.user, f'Invalid protocol: {protocol}')
            return False
        return True
    
    def valid_remarks(self, row, remarks):
        if not remarks:
            return -1
        for i in range(self.table.rowCount()):
            if row == i:
                continue
            if remarks != self.table.item(i, 8).text():
                continue
            return i
        return -1
    
    def valid_security(self, security):
        if security not in ['', 'tls', 'reality']:
            Globals._Log.error(self.user, f'Invalid security: {security}')
            return False
        return True
        
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