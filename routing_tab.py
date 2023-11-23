import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QTableWidgetItem, QTableWidget, QCheckBox, QMenu, QWidget

class RoutingTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.columns = ['Select', 'Protocol', 'Address', 'Port', 'User', 'Password']
        self.original_cell_values = {}
        self.setup_ui()

    def add_row_local(self, data=None):

        def _make_checkbox(insert_position, idx):
            chk_box = QCheckBox()
            chk_box.setStyleSheet("QCheckBox { margin-left: 50%; margin-right: 50%; }")
            self.table.setCellWidget(insert_position, idx, chk_box)

        try:
            if not data:
                data = {
                    'protocol': 'socks5',
                    'address': '0.0.0.0',
                    'port': self.find_next_port()
                }
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

    def cell_was_clicked(self, row, column):
        if column == 0:
            chk_box = self.table.cellWidget(row, 0)
            if chk_box:
                chk_box.setChecked(not chk_box.isChecked())
        if column == 1:
            self.show_protocol_selection_menu(row, column)

    def delete_selected_rows_local(self):
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

    def find_next_port(self):
        ports = set()
        for row in range(self.table.rowCount()):
            if self.table.item(row, 2).text() != '0.0.0.0':
                continue
            row_port = self.table.item(row, 3)
            if row_port:
                ports.add(row_port.text())

        port = 30001
        while str(port) in ports:
            port += 1
        return str(port)
    
    def is_row_exists(self, data, ignore_row=None):
        for row in range(self.table.rowCount()):
            if row == ignore_row:
                continue
            if all(self.table.item(row, col) and self.table.item(row, col).text() == data.get(self.columns[col].lower(), '') for col in range(1, 6)):
                return True
        return False

    def load_data_from_file(self):
        if os.path.exists("routing.txt"):
            with open("routing.txt", "r") as file:
                for line in file:
                    self.parse_link(line.strip())

    def on_cell_changed(self, row, column):
        if (row, column) not in self.original_cell_values:
            self.original_cell_values[(row, column)] = self.table.item(row, column).text()
            
        data = {self.columns[col].lower(): self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(1, 6)}
        if self.is_row_exists(data, ignore_row=row):
            self.table.item(row, column).setText(self.original_cell_values[(row, column)])
        else:
            self.original_cell_values[(row, column)] = self.table.item(row, column).text()

    def parse_link(self, url):
        
        def _make_pars(protocol, address, port, user, password):
            if user:
                return {
                    'protocol': protocol,
                    'address': address,
                    'port': port,
                    'user': user,
                    'password': password
                }
            return {
                    'protocol': protocol,
                    'address': address,
                    'port': port,
                }

        try:
            par1, par2, par3, par4 = ('', '', '', '')
            protocol, rest = url.split("://")
            if protocol not in ['http', 'socks5']:
                return
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
                    pars = _make_pars(protocol, par3, par4, par1, par2)
                elif '.' in par1 and par2.isdigit():
                    pars = _make_pars(protocol, par1, par2, par3, par4)
                else:
                    return
            else:
                if par4:
                    return
                if '.' not in par1:
                    return
                if not par2.isdigit():
                    return
                pars = _make_pars(protocol, par1, par2, par3, par4)
            self.add_row_local(pars)
        except Exception as e:
            print(str(e))

    def reload_rows(self):
        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)
        self.load_data_from_file()

    def save_data_to_file_local(self):
        with open("routing.txt", "w") as file:
            for row in range(self.table.rowCount()):
                protocol, address, port, user, password = (self.table.item(row, col).text() if self.table.item(row, col) else '' for col in range(1, 6))
                line = f"{protocol}://{address}:{port}"
                if user and password:
                    line += f"@{user}:{password}"
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
        button_add.clicked.connect(self.add_row_local)
        top_layout.addWidget(button_add)
        button_delete = QPushButton('Delete')
        button_delete.clicked.connect(self.delete_selected_rows_local)
        top_layout.addWidget(button_delete)
        button_reload = QPushButton('Reload')
        button_reload.clicked.connect(self.reload_rows)
        top_layout.addWidget(button_reload)
        top_layout.addStretch()
        button_save = QPushButton('Save')
        button_save.clicked.connect(self.save_data_to_file_local)
        top_layout.addWidget(button_save)

        middle_layout = QHBoxLayout()
        layout.addLayout(middle_layout)
        self.table = QTableWidget(0, 6)
        middle_layout.addWidget(self.table)
        header_labels = self.columns
        self.table.setHorizontalHeaderLabels(header_labels)
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
