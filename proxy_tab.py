import base64
import os
import re
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCursor, QGuiApplication
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QTableWidget, QCheckBox, QMenu, QWidget
from urllib.parse import quote, unquote

class ProxyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        self.columns = ['Select', 'Protocol', 'Address', 'Port', 'User', 'Password', 'Encryption', 'Remarks']
        self.original_cell_values = {}
        self.setup_ui()

    def add_row_proxy(self, data={}):

        def _make_checkbox(insert_position, idx):
            chk_box = QCheckBox()
            chk_box.setStyleSheet("QCheckBox { margin-left: 50%; margin-right: 50%; }")
            self.table.setCellWidget(insert_position, idx, chk_box)

        try:
            if self.is_row_exists(data):
                return
            insert_position = self.find_insert_position(data.get('address', ''), data.get('port', ''))
            self.table.insertRow(insert_position)

            for idx, col in enumerate(self.columns):
                if col == 'Select':
                    _make_checkbox(insert_position, idx)
                    continue
                item = QTableWidgetItem(data.get(col.lower()))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(insert_position, idx, item)

        except Exception as e:
            print(str(e))

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
        except Exception as e:
            return ''

    def cell_was_clicked(self, row, column):
        if column == 1:
            self.show_protocol_selection_menu(row, column)

    def delete_selected_rows_proxy(self):
        for row in reversed(range(self.table.rowCount())):
            chk_box = self.table.cellWidget(row, 0)
            if chk_box and chk_box.isChecked():
                self.table.removeRow(row)

    def find_insert_position(self, address, port):
        row_count = self.table.rowCount()
        for row in range(row_count):
            row_address = self.table.item(row, 2).text()
            row_port = self.table.item(row, 3).text()
            if address < row_address or (address == row_address and port < row_port):
                return row
        return row_count
    
    def is_row_exists(self, data, ignore_row=None):
        for row in range(self.table.rowCount()):
            if row == ignore_row:
                continue
            if all(self.table.item(row, col) and self.table.item(row, col).text() == data.get(self.columns[col].lower(), '') for col in range(1, 8)):
                return True
        return False

    def load_data_from_file(self):
        if os.path.exists("proxy.txt"):
            with open("proxy.txt", "r") as file:
                for line in file:
                    self.parse_link(line.strip())

    def on_cell_changed(self, row, column):
        if (row, column) not in self.original_cell_values:
            self.original_cell_values[(row, column)] = self.table.item(row, column).text()
            
        data = {self.columns[col].lower(): self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(1, 8)}
        if self.is_row_exists(data, ignore_row=row):
            self.table.item(row, column).setText(self.original_cell_values[(row, column)])
        else:
            self.original_cell_values[(row, column)] = self.table.item(row, column).text()

    def parse_from_clipboard(self):
        try:
            clipboard = QGuiApplication.clipboard()
            mime_data = clipboard.mimeData()
            if not mime_data.hasText():
                return
            urls = mime_data.text().split('\n')
            for url in urls:
                self.parse_link(url)
        except Exception as e:
            print(str(e))

    def parse_link(self, url):
        try:
            protocol, rest = url.split("://")
            if protocol == 'socks5':
                self.parse_socks5(rest)
            elif protocol == 'ss':
                self.parse_ss(rest)
            elif protocol in ['http', 'https']:
                if '/' not in rest:
                    return
                self.parse_subscribe(url)
        except Exception as e:
            print(str(e))

    def parse_ss(self, rest):
        try:
            match = re.match(r'(?P<params>.+)@(?P<server>[^:]+):(?P<port>\d+)(?:#(?P<remarks>.+))?', rest)
            if not match:
                return
            method, password = self.base64_decode(match.group('params')).split(':')
            if not method or not password:
                return
            server = match.group('server')
            if '.' not in server:
                return
            port = match.group('port')
            remarks = unquote(match.group('remarks'))
            pars = {
                'protocol': 'ss',
                'address': server,
                'port': port,
                'encryption': method,
                'password': password,
                'remarks': remarks
            }
            self.add_row_proxy(pars)
        except Exception as e:
            print(str(e))

    def parse_socks5(self, rest):

        def _make_pars(address, port, user, password):
            if user:
                return {
                    'protocol': 'socks5',
                    'address': address,
                    'port': port,
                    'user': user,
                    'password': password
                }
            return {
                    'protocol': 'socks5',
                    'address': address,
                    'port': port,
                }

        try:
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
                return
            if not par1 or not par2:
                return
            if par3:
                if not par4:
                    return
                if '.' in par3 and par4.isdigit():
                    if '.' in par1 and par2.isdigit():
                        return
                    pars = _make_pars(par3, par4, par1, par2)
                elif '.' in par1 and par2.isdigit():
                    pars = _make_pars(par1, par2, par3, par4)
                else:
                    return
            else:
                if par4:
                    return
                if '.' not in par1:
                    return
                if not par2.isdigit():
                    return
                pars = _make_pars(par1, par2, par3, par4)
            self.add_row_proxy(pars)
        except Exception as e:
            print(str(e))

    def parse_subscribe(self, source):
        try:
            res = requests.get(source, headers=self.headers)
            if res.status_code != 200:
                return
            if '://' in res.text:
                url_list = res.text.split('\n')
            else:
                res_decode = self.base64_decode(res.text)
                url_list = res_decode.split('\n')
            for url in url_list:
                self.parse_link(url)
        except Exception as e:
            print(str(e))

    def reload_rows(self):
        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)
        self.load_data_from_file()

    def save_data_to_file_proxy(self):

        def _encode_ss(address, port, password, encryption, remarks):
            method_password = f"{encryption}:{password}"
            method_password_encoded = base64.urlsafe_b64encode(method_password.encode()).decode().rstrip("=")
            ss_link = f"ss://{method_password_encoded}@{address}:{port}"
            if remarks:
                remarks_encoded = quote(remarks)
                ss_link += f"#{remarks_encoded}"
            return ss_link

        with open("proxy.txt", "w") as file:
            for row in range(self.table.rowCount()):
                protocol, address, port, user, password, encryption, remarks = (self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(1, 8))
                if protocol == 'ss':
                    line = _encode_ss(address, port, password, encryption, remarks)
                elif protocol == 'socks5':
                    line = f"{protocol}://{address}:{port}"
                    if user and password:
                        line += f"@{user}:{password}"
                else:
                    continue
                file.write(line + '\n')

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
        button_delete.clicked.connect(self.delete_selected_rows_proxy)
        top_layout.addWidget(button_delete)
        button_reload = QPushButton('Reload')
        button_reload.clicked.connect(self.reload_rows)
        top_layout.addWidget(button_reload)
        top_layout.addStretch()
        button_save = QPushButton('Save')
        button_save.clicked.connect(self.save_data_to_file_proxy)
        top_layout.addWidget(button_save)

        middle_layout = QHBoxLayout()
        layout.addLayout(middle_layout)
        self.table = QTableWidget(0, 8)
        middle_layout.addWidget(self.table)
        header_labels = self.columns
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.cellClicked.connect(self.cell_was_clicked)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.load_data_from_file()

    def show_add_menu(self):
        menu = QMenu(self)
        action_blank_line = QAction('blank_line', self)
        action_from_clipboard = QAction('from_clipboard', self)

        action_blank_line.triggered.connect(lambda: self.add_row_proxy())
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
