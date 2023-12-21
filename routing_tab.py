import json
import os
from PyQt6.QtCore import (
    pyqtSignal,
    Qt
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QCheckBox,
    QHeaderView,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QWidgetAction
)

from globals import Globals

class RoutingTab(QWidget):
    def __init__(
            self,
            parent,
            highlight_inbounds_row_signal,
            highlight_outbounds_row_signal,
            unhighlight_inbounds_row_signal,
            unhighlight_outbounds_row_signal
        ):
        super().__init__(parent)
        self.columns = ['Select', 'Inbounds', 'InitialHop', 'SecondHop', 'ThirdHop', 'FinalHop']
        self.highlight_inbounds_row_signal = highlight_inbounds_row_signal
        self.highlight_outbounds_row_signal = highlight_outbounds_row_signal
        self.inbounds_protocol_map = {'http': 'http', 'socks5': 'socks'}
        self.original_cell_values = {}
        self.outbounds_protocol_map = {'ss': 'shadowsocks', 'socks5': 'socks'}
        self.tag_end = {}
        self.tag_through = {}
        self.unhighlight_inbounds_row_signal = unhighlight_inbounds_row_signal
        self.unhighlight_outbounds_row_signal = unhighlight_outbounds_row_signal
        self.user = 'RoutingTab'
        self.setup_ui()

    def add_row_routing(self, data={}):

        def _make_checkbox(insert_position, idx):
            widget = QWidget()
            layout = QHBoxLayout(widget)
            chk_box = QCheckBox()
            layout.addWidget(chk_box)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(insert_position, idx, widget)

        def _set_inbounds(row, inbounds):
            text = '\n'.join(inbounds)
            _set_text(row, 1, text)
            with Globals.routing_used_inbound_options_lock:
                for inbound in inbounds:
                    if inbound not in Globals.routing_used_inbound_options.keys():
                        Globals.routing_used_inbound_options[inbound] = []
                    if (row, 1) not in Globals.routing_used_inbound_options[inbound]:
                        Globals.routing_used_inbound_options[inbound].append((row, 1))

        def _set_outbounds(row, outbounds):
            col = 2
            throughs = outbounds.get('Through')
            if throughs:
                for through in throughs:
                    if not self.add_through(through):
                        
                    _set_text(row, col, through)
                    col += 1
            end = outbounds.get('End')
            if end:
                _set_text(row, col, end)
            with Globals.routing_used_outbound_options_lock:
                if outbound not in Globals.routing_used_outbound_options.keys():
                    Globals.routing_used_outbound_options[outbound] = []
                if (row, col) not in Globals.routing_used_outbound_options[outbound]:
                    Globals.routing_used_outbound_options[outbound].append((row, col))

        def _set_text(row, col, text):
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, col, item)

        try:
            if data:
                if not self.is_row_data_valid(data):
                    return
            else:
                data = {}
            inbounds = data.get('Inbounds', [])
            inbounds.sort()
            outbounds = data.get('Outbounds', [])
            if self.is_row_exists(inbounds):
                return
            insert_position = self.find_insert_position(inbounds)

            self.table.blockSignals(True)
            try:
                self.table.insertRow(insert_position)

                _make_checkbox(insert_position, 0)
                _set_inbounds(insert_position, inbounds)
                _set_outbounds(insert_position, outbounds)
            except Exception as e:
                Globals._Log.error(self.user, f'Error in add_row_routing: {e}')
            finally:
                self.table.blockSignals(False)

        except Exception as e:
            Globals._Log.error(self.user, f'Error in add_row_routing: {e}')

    def build_config(self, inbounds_data, outbounds_data):

        def _build_inbound(tag, row):
            if not row:
                return []
            with open('json_model/inbounds.json', 'r') as file:
                inbound = json.load(file)
            inbound['protocol'] = self.inbounds_protocol_map[row['Protocol']]
            inbound['listen'] = row['Address']
            inbound['port'] = int(row['Port'])
            inbound['tag'] = tag
            if bool(row['User']) != bool(row['Password']):
                return []
            if inbound['protocol'] == 'http':
                with open('json_model/inbounds_settings_http.json', 'r') as file:
                    settings = json.load(file)
                settings['accounts'][0]['user'] = row['User']
                settings['accounts'][0]['pass'] = row['Password']
                inbound['settings'] = settings
            elif inbound['protocol'] == 'socks':
                with open('json_model/inbounds_settings_socks.json', 'r') as file:
                    settings = json.load(file)
                settings['accounts'][0]['user'] = row.get('User', '')
                settings['accounts'][0]['pass'] = row.get('Password', '')
                inbound['settings'] = settings
            else:
                return []
            return [inbound]
        
        def _build_outbound(tag, through):
            row = outbounds_data.get(tag, '')
            if not row:
                return []
            with open('json_model/outbounds.json', 'r') as file:
                outbound = json.load(file)
            outbound['protocol'] = self.outbounds_protocol_map[row['Protocol']]
            outbound['tag'] = tag
            if through:
                outbound['outboundsSettings'] = {'tag': through}
            if outbound['protocol'] == 'socks':
                with open('json_model/outbounds_settings_socks.json', 'r') as file:
                    settings = json.load(file)
                settings['servers'][0]['address'] = row['Address']
                settings['servers'][0]['port'] = int(row['Port'])
                settings['servers'][0]['users'][0]['user'] = row['User']
                settings['servers'][0]['users'][0]['pass'] = row['Password']
                outbound['settings'] = settings
            elif outbound['protocol'] == 'shadowsocks':
                with open('json_model/outbounds_settings_shadowsocks.json', 'r') as file:
                    settings = json.load(file)
                settings['servers'][0]['address'] = row['Address']
                settings['servers'][0]['port'] = int(row['Port'])
                settings['servers'][0]['method'] = row['Encryption']
                settings['servers'][0]['password'] = row['Password']
                outbound['settings'] = settings
            return [outbound]
        
        def _build_routing_rule(row):
            with open('json_model/routing_rules.json', 'r') as file:
                rule = json.load(file)
            rule['inboundTag'] = row.get('Inbounds', '').split('\n')
            outbounds = row.get('Outbounds', [])
            if not outbounds:
                return []
            rule['outboundTag'] = outbounds[-1]
            return [rule]

        routing_data = self.extract_table_data()
        need_through_dict, no_need_through_set =  self.is_outbounds_data_valid(routing_data)
        if not need_through_dict and not no_need_through_set:
            return
        with open('json_model/main.json', 'r') as file:
            config = json.load(file)
        with open('json_model/log.json', 'r') as file:
            config['log'] = json.load(file)
        with open('json_model/routing.json', 'r') as file:
            config['routing'] = json.load(file)
        
        for row in routing_data:
            for tag in row.get('Inbounds').split('\n'):
                config['inbounds'].extend(_build_inbound(tag, inbounds_data.get(tag, '')))
            config['routing']['rules'].extend(_build_routing_rule(row))

        for tag, through in need_through_dict.items():
            outbound = _build_outbound(tag, through)
            config['outbounds'].extend(outbound)
        for tag in no_need_through_set:
            outbound = _build_outbound(tag, None)
            config['outbounds'].extend(outbound)

        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    def cell_was_clicked(self, row, column):
        if column == 0:
            chk_box = self.get_checkbox(row)
            if not chk_box:
                return
            chk_box.setChecked(not chk_box.isChecked())
        elif column == 1:
            self.show_inbounds_selection_menu(row, column)
        else:
            self.show_outbounds_selection_menu(row, column)

    def delete_selected_rows_inbounds(self):
        rows_to_delete = []
        with Globals.routing_used_inbound_options_lock:
            for row in reversed(range(self.table.rowCount())):
                chk_box = self.get_checkbox(row)
                if not chk_box:
                    continue
                if chk_box.isChecked():
                    inbounds_text = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
                    for option in inbounds_text.split('\n'):
                        if option:
                            Globals.routing_used_inbound_options.discard(option)
                    rows_to_delete.append(row)
            for row in rows_to_delete:
                self.table.removeRow(row)
        self.reload_original_values()

    def extract_table_data(self):
        table_data = []
        for row in range(self.table.rowCount()):
            outbounds = []
            for outbound in [
                self.table.item(row, 2).text() if self.table.item(row, 2) else '',
                self.table.item(row, 3).text() if self.table.item(row, 3) else '',
                self.table.item(row, 4).text() if self.table.item(row, 4) else '',
                self.table.item(row, 5).text() if self.table.item(row, 5) else ''
            ]:
                if not outbound:
                    continue
                outbounds.append(outbound)
            row_data = {
                "Inbounds": self.table.item(row, 1).text().split('\n') if self.table.item(row, 1) else [],
                'Outbounds': outbounds
            }
            if not self.is_row_data_valid(row_data):
                continue
            table_data.append(row_data)
        return table_data

    def find_insert_position(self, inbounds):
        row_count = self.table.rowCount()
        for row in range(row_count):
            row_address = self.table.item(row, 1).text().split('\n') if self.table.item(row, 1) else []
            row_address.sort()
            if inbounds[0] < row_address[0]:
                return row
        return row_count
    
    def get_checkbox(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget is not None:
            chk_box = widget.layout().itemAt(0).widget()
            if isinstance(chk_box, QCheckBox):
                return chk_box
        return None
    
    def highlight_inbounds_row(self):
        pass
    
    def highlight_outbounds_row(self):
        pass
    
    def is_row_exists(self, inbounds, ignore_row=None):
        inbounds_set = set(inbounds)
        for row in range(self.table.rowCount()):
            if row == ignore_row:
                continue
            existing_inbounds = set(self.table.item(row, 1).text().split('\n')) if self.table.item(row, 1) else set()
            if inbounds_set == existing_inbounds:
                return True
        return False
    
    def is_outbounds_data_valid(self, routing_data):
        if not routing_data:
            return {}, set()
        need_through_set = set()
        need_through_dict = {}
        no_need_through_set = set()
        for data in routing_data:
            tags = data.get('Outbounds')
            for idx, tag in enumerate(tags):
                if idx:
                    if tag in need_through_dict and tags[idx-1] != need_through_dict[tag]:
                        QMessageBox.warning(None, 'Error!', f'Conflict in "outbounds" tag: {tag}')
                        return {}, set()
                    need_through_set.add(tag)
                    need_through_dict[tag] = tags[idx-1]
                else:
                    no_need_through_set.add(tag)
        if need_through_set & no_need_through_set:
            QMessageBox.warning(None, 'Error!', f'Conflict in "outbounds" tags: {need_through_set & no_need_through_set}')
            return {}, set()
        return need_through_dict, no_need_through_set

    def is_row_data_valid(self, row_data):
        if not isinstance(row_data.get('Inbounds'), list):
            return False
        if not isinstance(row_data.get('Outbounds'), list):
            return False
        return True
    
    def load_data_from_file(self):
        if not os.path.exists("routing.json"):
            return
        with open("routing.json", "r") as file:
            routings = json.load(file)
        for routing in routings:
            self.add_row_routing(routing)

    def modify_outbounds(self, method, key, )

    def on_cell_changed(self, row, column):
        if column == 0:
            return
        
        self.table.blockSignals(True)

        try:
            current_value = self.table.item(row, column).text() if self.table.item(row, column) else ''

            if column == 1:
                with Globals.routing_original_cell_values_lock:
                    original_inbounds = Globals.routing_original_cell_values.get((row, column), '').split('\n')
                    current_inbounds_set = set(filter(None, current_value.split('\n')))

                    with Globals.routing_used_inbound_options_lock:
                        if any(inbound in Globals.routing_used_inbound_options.keys() and inbound not in original_inbounds for inbound in current_inbounds_set):
                            self.table.item(row, column).setText(Globals.routing_original_cell_values.get((row, column), ''))
                        else:
                            for inbound in current_inbounds_set:
                                if inbound not in original_inbounds:
                                    Globals.routing_used_inbound_options.add(inbound)
                            for inbound in original_inbounds:
                                if inbound not in current_inbounds_set:
                                    Globals.routing_used_inbound_options.discard(inbound)

                            Globals.routing_original_cell_values[(row, column)] = current_value
            else:
                with Globals.routing_original_cell_values_lock:
                    Globals.routing_original_cell_values[(row, column)] = current_value
        finally:
            self.table.blockSignals(False)

    def reload_original_values(self):
        with Globals.routing_original_cell_values_lock:
            Globals.routing_original_cell_values.clear()
        self.update_original_values(0)

    def reload_rows(self):
        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)
        self.load_data_from_file()

    def save_data_to_file(self):
        table_data = self.extract_table_data()
        with open("routing.json", "w") as file:
            json.dump(table_data, file, indent=4)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        button_add = QPushButton('Add')
        button_add.clicked.connect(self.add_row_routing)
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
        self.table = QTableWidget(0, 6)
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

    def show_inbounds_selection_menu(self, row, column):

        def _checkbox_changed(state, option, row, column):
            current_cell_value = self.table.item(row, column).text() if self.table.item(row, column) else ''
            selections = set(current_cell_value.split('\n'))

            if state and option not in selections:
                selections.add(option)
                self.highlight_inbounds_row_signal.emit(option)
            elif not state and option in selections:
                selections.remove(option)
                self.unhighlight_inbounds_row_signal.emit(option)

            sorted_selections = sorted(selections)
            new_value = '\n'.join(sorted_selections).strip()
            self.table.item(row, column).setText(new_value)

            with Globals.routing_used_inbound_options_lock:
                if state:
                    Globals.routing_used_inbound_options.add(option)
                else:
                    Globals.routing_used_inbound_options.discard(option)

        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)

        current_cell_value = self.table.item(row, column).text() if self.table.item(row, column) else ''
        current_selections = set(current_cell_value.split('\n'))

        self.checkboxes = []
        with Globals.acquire(Globals.routing_used_inbound_options_lock, Globals.inbounds_lock):
            for key, value in Globals.inbounds_dict.items():
                option = value.get('Tag') if value.get('Tag') else key
                if option in Globals.routing_used_inbound_options and option not in current_selections:
                    continue
                checkbox = QCheckBox(option)
                checkbox.setChecked(option in current_selections)
                checkbox.stateChanged.connect(lambda state, opt=option: _checkbox_changed(state, opt, row, column))
                self.checkboxes.append(checkbox)
                menu_layout.addWidget(checkbox)

        scroll_area = QScrollArea()
        scroll_area.setWidget(menu_widget)
        scroll_area.setWidgetResizable(True)

        custom_menu = QMenu(self)
        action = QWidgetAction(custom_menu)
        action.setDefaultWidget(scroll_area)
        custom_menu.addAction(action)

        item = self.table.item(row, column)
        cell_rect = self.table.visualItemRect(item)
        pos = self.table.viewport().mapToGlobal(cell_rect.topLeft())
        custom_menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        custom_menu.exec(pos)

    def show_outbounds_selection_menu(self, row, column):

        def _button_clicked(button_text, menu):
            old_tag = self.table.item(row, column).text() if self.table.item(row, column) else ''
            if old_tag:
                self.unhighlight_outbounds_row_signal.emit(old_tag)
            self.table.item(row, column).setText(button_text)
            if button_text:
                self.highlight_outbounds_row_signal.emit(button_text)
            menu.close()

        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        custom_menu = QMenu(self)
        button = QPushButton('')
        button.clicked.connect(lambda _, opt='', menu=custom_menu: _button_clicked(opt, menu))
        menu_layout.addWidget(button)
        with Globals.acquire(Globals.routing_used_outbound_options_lock, Globals.outbounds_lock):
            for key, value in Globals.outbounds_dict.items():
                option = value.get('Tag') if value.get('Tag') else (value.get('Remarks') if value.get('Remarks') else key)
                button = QPushButton(option)
                button.clicked.connect(lambda _, opt=option, menu=custom_menu: _button_clicked(opt, menu))
                menu_layout.addWidget(button)

        scroll_area = QScrollArea()
        scroll_area.setWidget(menu_widget)
        scroll_area.setWidgetResizable(True)

        action = QWidgetAction(custom_menu)
        action.setDefaultWidget(scroll_area)
        custom_menu.addAction(action)

        item = self.table.item(row, column)
        cell_rect = self.table.visualItemRect(item)
        pos = self.table.viewport().mapToGlobal(cell_rect.topLeft())
        custom_menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        custom_menu.exec(pos)