import base64
import os
import re
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QAction,
    QCursor,
    QGuiApplication
)
from PyQt6.QtWidgets import (
    QCheckBox,
    QHeaderView,
    QHBoxLayout,
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

from globals import (
    proxy_original_cell_values,
    proxy_original_cell_values_lock
)

class ProxyTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'}
        self.columns = ['Select', 'Protocol', 'Address', 'Port', 'User', 'Password', 'Encryption', 'Remarks']
        self.setup_ui()

    def add_row_proxy(self, data={}):

        def _make_checkbox(insert_position, idx):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            chk_box = QCheckBox()
            layout.addWidget(chk_box)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(insert_position, idx, widget)

        try:
            if data:
                if not self.is_row_data_valid(data):
                    return
            else:
                data = {}
            if self.is_row_exists(data):
                return
            insert_position = self.find_insert_position(data.get('Address', ''), data.get('Port', ''))

            self.table.blockSignals(True)
            try:
                self.table.insertRow(insert_position)

                for idx, col in enumerate(self.columns):
                    if col == 'Select':
                        _make_checkbox(insert_position, idx)
                        continue
                    item = QTableWidgetItem(data.get(col, ''))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(insert_position, idx, item)
            except Exception as e:
                print(str(e))
            finally:
                self.table.blockSignals(False)

            self.update_original_values(insert_position)

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

    def delete_selected_rows_proxy(self):
        for row in reversed(range(self.table.rowCount())):
            chk_box = self.get_checkbox(row)
            if not chk_box:
                continue
            if chk_box.isChecked():
                self.table.removeRow(row)
        self.reload_original_values()

    def extract_table_data(self):
        table_data = {}
        for row in range(self.table.rowCount()):
            row_data = {}
            for col, col_name in enumerate(self.columns):
                if col_name == 'Select':
                    continue
                else:
                    item = self.table.item(row, col)
                    row_data[col_name] = item.text() if item else ''
            if not self.is_row_data_valid(row_data):
                continue
            if row_data['Remarks']:
                table_data[f'{row_data["Remarks"].strip()}:{row_data["Address"]}:{row_data["Port"]}'] = row_data
            else:
                table_data[f'{row_data["Address"]}:{row_data["Port"]}'] = row_data
        return table_data

    def find_insert_position(self, address, port):
        row_count = self.table.rowCount()
        for row in range(row_count):
            row_address = self.table.item(row, 2).text()
            row_port = self.table.item(row, 3).text()
            if address < row_address or (address == row_address and port < row_port):
                return row
        return row_count
    
    def get_checkbox(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget is not None:
            chk_box = widget.layout().itemAt(0).widget()
            if isinstance(chk_box, QCheckBox):
                return chk_box
        return None
    
    def is_row_exists(self, data, ignore_row=None):
        address = data.get('Address', '')
        port = data.get('Port', '')

        with proxy_original_cell_values_lock:
            for row in range(int(len(proxy_original_cell_values)/7)):
                if row == ignore_row:
                    continue
                row_address = proxy_original_cell_values.get((row, 2))
                row_port = proxy_original_cell_values.get((row, 3))
                if address == row_address and port == row_port:
                    return True
        return False
    
    def is_row_data_valid(self, row_data):
        if row_data.get('Protocol', '') not in ['ss', 'socks5']:
            return False
        if '.' not in row_data.get('Address', ''):
            return False
        if not row_data.get('Port', '').isdigit():
            return False
        if row_data.get('Protocol', '') == 'ss':
            if not row_data.get('Encryption', ''):
                return False
            if not row_data.get('Password', ''):
                return False
        return True

    def load_data_from_file(self):
        if os.path.exists("proxy.txt"):
            with open("proxy.txt", "r") as file:
                for line in file:
                    self.parse_link(line.strip())

    def on_cell_changed(self, row, column):
        if column == 0:
            return
        
        elif column in [2, 3]:
            address = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
            port = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
            data = {'Address': address, 'Port': port}
            if self.is_row_exists(data, ignore_row=row):
                self.table.item(row, column).setText(proxy_original_cell_values[(row, column)])
                return

        with proxy_original_cell_values_lock:
            proxy_original_cell_values[(row, column)] = self.table.item(row, column).text()

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
            if url.count('://') != 1:
                return
            protocol, rest = url.split('://')
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
            method_password = self.base64_decode(match.group('params'))
            if method_password.count(':') != 1:
                return
            method, password = method_password.split(':')
            if not method or not password:
                return
            server = match.group('server')
            if '.' not in server:
                return
            port = match.group('port')
            remarks = unquote(match.group('remarks'))
            pars = {
                'Protocol': 'ss',
                'Address': server,
                'Port': port,
                'Encryption': method,
                'Password': password,
                'Remarks': remarks
            }
            self.add_row_proxy(pars)
        except Exception as e:
            print(str(e))

    def parse_socks5(self, rest):

        def _make_pars(address, port, user, password):
            if user:
                return {
                    'Protocol': 'socks5',
                    'Address': address,
                    'Port': port,
                    'User': user,
                    'Password': password
                }
            return {
                    'Protocol': 'socks5',
                    'Address': address,
                    'Port': port,
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
            urls = res.text
            if '://' not in urls:
                urls = self.base64_decode(urls)
            if '://' not in urls:
                return
            url_list = urls.split('\n')
            for url in url_list:
                self.parse_link(url)
        except Exception as e:
            print(str(e))

    def reload_original_values(self):
        with proxy_original_cell_values_lock:
            proxy_original_cell_values.clear()
        self.update_original_values(0)

    def reload_rows(self):
        with proxy_original_cell_values_lock:
            for row in reversed(range(self.table.rowCount())):
                self.table.removeRow(row)
            proxy_original_cell_values.clear()

        self.load_data_from_file()

    def save_data_to_file(self):

        def _encode_ss(row_data):
            method_password = f'{row_data["Encryption"]}:{row_data["Password"]}'
            method_password_encoded = base64.urlsafe_b64encode(method_password.encode()).decode().rstrip("=")
            ss_link = f'ss://{method_password_encoded}@{row_data["Address"]}:{row_data["Port"]}'
            if row_data['Remarks']:
                remarks_encoded = quote(row_data['Remarks'])
                ss_link += f"#{remarks_encoded}"
            return ss_link

        with proxy_original_cell_values_lock:
            with open("proxy.txt", "w") as file:
                for row in range(int(len(proxy_original_cell_values)/7)):
                    row_data = {
                        'Protocol': proxy_original_cell_values.get((row, 1)),
                        'Address': proxy_original_cell_values.get((row, 2)),
                        'Port': proxy_original_cell_values.get((row, 3)),
                        'User': proxy_original_cell_values.get((row, 4)),
                        'Password': proxy_original_cell_values.get((row, 5)),
                        'Encryption': proxy_original_cell_values.get((row, 6)),
                        'Remarks': proxy_original_cell_values.get((row, 7)),
                    }
                    if not self.is_row_data_valid(row_data):
                        continue
                    if row_data['Protocol'] == 'ss':
                        line = _encode_ss(row_data)
                    elif row_data['Protocol'] == 'socks5':
                        line = f'{row_data["Protocol"]}://{row_data["Address"]}:{row_data["Port"]}'
                        if row_data['User'] and row_data['Password']:
                            line += f'@{row_data["User"]}:{row_data["Password"]}'
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
        button_save.clicked.connect(self.save_data_to_file)
        top_layout.addWidget(button_save)

        middle_layout = QHBoxLayout()
        layout.addLayout(middle_layout)
        self.table = QTableWidget(0, 8)
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

    def update_original_values(self, start_row):
        with proxy_original_cell_values_lock:
            for row in range(start_row, self.table.rowCount()):
                for col in range(1, self.table.columnCount()):
                    cell_value = self.table.item(row, col).text() if self.table.item(row, col) else ''
                    proxy_original_cell_values[(row, col)] = cell_value
