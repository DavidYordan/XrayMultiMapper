import json
import os
from PyQt6.QtCore import (
    pyqtSlot,
    Qt
)
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QCheckBox,
    QHeaderView,
    QMenu,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QWidgetAction
)

from globals import Globals
from json_model import JsonModel

class RoutingTab(QWidget):
    def __init__(
            self,
            parent,
            update_inbounds_background_signal,
            update_outbounds_background_signal
        ):
        super().__init__(parent)

        self.user = 'RoutingTab'
        self.columns = ['select', 'Inbounds', 'InitialHop', 'SecondHop', 'ThirdHop', 'FinalHop']
        self.JM = JsonModel()
        self.original_cell_values = {}
        self.remarks_end = {}
        self.remarks_through = {}
        self.update_inbounds_background_signal = update_inbounds_background_signal
        self.update_outbounds_background_signal = update_outbounds_background_signal
        self.setup_ui()

    def add_row(self, data):

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

        def _find_insert_position(inbound):
            row_count = self.table.rowCount()
            for row in range(row_count):
                if inbound < self.table.item(row, 1).text():
                    return row
            return row_count
        
        def _is_row_exists(inbounds):
            with Globals.routing_used_inbounds_keys_lock:
                used_keys = Globals.routing_used_inbounds_keys.keys()
            for inbound in inbounds:
                _, key = inbound.split('|')
                if key in used_keys:
                    return True
            return False
        
        def _set_inbounds(row, inbounds):
            self.table.item(row, 1).setText('\n'.join(inbounds))
            update_keys = set()
            with Globals.routing_used_inbounds_keys_lock:
                for text in inbounds:
                    _, key = text.split('|')
                    if key in Globals.routing_used_inbounds_keys:
                        Globals.routing_used_inbounds_keys[key].append((row, 1))
                    else:
                        Globals.routing_used_inbounds_keys[key] = [(row, 1)]
                        update_keys.add(key)
            if update_keys:
                self.update_inbounds_background(update_keys)

        def _set_outbounds(row, outbounds):
            col = 2
            keys = []
            with Globals.routing_used_outbounds_keys_lock:
                for outbound in outbounds:
                    self.table.item(row, col).setText(outbound)
                    _, _, key = outbound.split('|')
                    keys.append(key)
                    if key in Globals.routing_used_outbounds_keys:
                        Globals.routing_used_outbounds_keys[key].append((row, col))
                    else:
                        Globals.routing_used_outbounds_keys[key] = [(row, col)]
                    col += 1

            self.update_outbounds_background(keys)

        try:
            if not data:
                _add_blank_row(0)
                return
            inbounds = data.get('Inbounds', [])
            if _is_row_exists(inbounds):
                return
            outbounds = data.get('Outbounds', [])
            
            insert_position = _find_insert_position(inbounds[0] if inbounds else '')

            _add_blank_row(insert_position)

            _set_inbounds(insert_position, inbounds)
            _set_outbounds(insert_position, outbounds)

        except Exception as e:
            Globals._Log.error(self.user, f'Error in add_row: {e}')

    def build_config(self):

        def _build_inbound(remarks, data):
            inbound = self.JM.inbound
            inbound['listen'] = data['address']
            inbound['port'] = int(data['port'])
            inbound['tag'] = remarks
            protocol = inbound['protocol']
            if protocol == 'http':
                settings = self.JM.inbound_settings_http
            elif protocol == 'socks':
                settings = self.JM.inbound_settings_socks
            if data['user']:
                settings['accounts'] = [{'user': data['user'], 'password': data['password']}]
                if protocol == 'socks':
                    settings['auth'] = 'password'
            inbound['settings'] = settings
            return inbound
        
        def _build_outbound(tag, data, through=None):
            outbound = self.JM.outbound
            outbound['tag'] = tag
            if through:
                outbound['proxySettings'] = {'tag': through}

            if data['protocol'] == 'socks':
                outbound['protocol'] = 'socks'
                settings = self.JM.outbound_settings_socks
                settings['servers'][0]['address'] = data['address']
                settings['servers'][0]['port'] = int(data['port'])
                if data['user']:
                    settings['servers'][0]['users'].append({
                        'user': data['user'],
                        'pass': data['password'],
                        'level': 0
                    })
                
            elif data['protocol'] == 'shadowsocks':
                outbound['protocol'] = 'shadowsocks'
                settings = self.JM.outbound_settings_shadowsocks
                settings['servers'][0]['address'] = data['address']
                settings['servers'][0]['port'] = int(data['port'])
                settings['servers'][0]['method'] = data['encryption']
                settings['servers'][0]['password'] = data['password']

            elif data['protocol'] == 'trojan':
                outbound['protocol'] = 'trojan'
                settings = self.JM.outbound_settings_trojan
                settings['servers'][0]['address'] = data['address']
                settings['servers'][0]['port'] = int(data['port'])
                settings['servers'][0]['password'] = data['password']

            elif data['protocol'] == 'vless':
                outbound['protocol'] = 'vless'
                settings = self.JM.outbound_settings_vless
                settings['vnext'][0]['address'] = data['address']
                settings['vnext'][0]['port'] = int(data['port'])
                settings['vnext'][0]['users'][0]['id'] = data['uuid']
                settings['vnext'][0]['users'][0]['encryption'] = data['encryption']
                settings['vnext'][0]['users'][0]['flow'] = data['flow']

            elif data['protocol'] == 'vmess':
                outbound['protocol'] = 'vmess'
                settings = self.JM.outbound_settings_vmess
                settings['vnext'][0]['address'] = data['address']
                settings['vnext'][0]['port'] = int(data['port'])
                settings['vnext'][0]['users'][0]['id'] = data['id']
                settings['vnext'][0]['users'][0]['security'] = data['security']
                
            outbound['settings'] = settings
            return outbound
        
        def _build_routing_rule(inbounds_tags, outbound_tag):
            rule = self.JM.routing_rule
            rule['inboundTag'] = inbounds_tags
            rule['outboundTag'] = outbound_tag
            return rule
        
        config = self.JM.main
        config['log'] = self.JM.log
        config['routing'] = self.JM.routing

        with Globals.inbounds_lock:
            inbounds_datas = Globals.inbounds_dict.copy()
        with Globals.outbounds_lock:
            outbounds_datas = Globals.outbounds_dict.copy()
        routing_datas = self.extract_table_data()

        outbounds_set = set()

        for routing_data in routing_datas:
            inbounds = routing_data.get('Inbounds', [])
            inbounds_tags = []
            for inbound in inbounds:
                remarks, key = inbound.split('|')
                tag = remarks if remarks else key
                inbounds_tags.append(tag)
                config['inbounds'].append(_build_inbound(tag, inbounds_datas[key]))

            outbounds = routing_data.get('Outbounds', [])
            outbound_tag, _, key = outbounds[-1].split('|')
            config['routing']['rules'].append(_build_routing_rule(inbounds_tags, outbound_tag if outbound_tag else key))

            last_tag = ''
            for idx, outbound in enumerate(outbounds):
                remarks, _, key = outbound.split('|')
                tag = remarks if remarks else key
                if tag in outbounds_set:
                    continue
                outbounds_set.add(tag)
                if idx == 0:
                    config['outbounds'].append(_build_outbound(tag, outbounds_datas[key]))
                else:
                    config['outbounds'].append(_build_outbound(tag, outbounds_datas[key], last_tag))
                last_tag = tag

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

    def delete_row(self, row):
        inbounds_text = self.table.item(row, 1).text()
        if inbounds_text:
            update_inbounds_keys = set()
            with Globals.routing_used_inbounds_keys_lock:
                for option in inbounds_text.split('\n'):
                    _, key = option.split('|')
                    if key not in Globals.routing_used_inbounds_keys:
                        continue
                    del Globals.routing_used_inbounds_keys[key]
                    update_inbounds_keys.add(key)
            self.update_inbounds_background(update_inbounds_keys)

        update_outbounds_keys = set()
        with Globals.routing_used_outbounds_keys_lock:
            for col in range(2, self.table.columnCount()):
                text = self.table.item(row, col).text()
                if not text:
                    continue
                _, _, key = text.split('|')
                if key not in Globals.routing_used_outbounds_keys:
                    continue
                if len(Globals.routing_used_outbounds_keys[key]) == 1:
                    del Globals.routing_used_outbounds_keys[key]
                    if key in Globals.routing_used_outbounds_through_keys:
                        Globals.routing_used_outbounds_through_keys.discard(key)
                    update_outbounds_keys.add(key)
                else:
                    Globals.routing_used_outbounds_keys[key].remove((row, col))
        
        self.table.removeRow(row)

        self.update_outbounds_background(update_outbounds_keys)

        Globals._Log.info(self.user, f'Row {row} has been deleted.')

    def delete_selected_rows(self):
        for row in reversed(range(self.table.rowCount())):
            chk_box = self.get_checkbox(row)
            if not chk_box:
                continue
            if not chk_box.isChecked():
                continue
            self.delete_row(row)

    def extract_table_data(self):
        table_data = []
        for row in range(self.table.rowCount()):
            inbounds_str = self.table.item(row, 1).text()
            inbounds = inbounds_str.split('\n') if inbounds_str else []
            outbounds = []
            for col in range(2, self.table.columnCount()):
                outbound = self.table.item(row, col).text()
                if not outbound:
                    continue
                outbounds.append(outbound)
            row_data = {
                "Inbounds": inbounds,
                'Outbounds': outbounds
            }
            table_data.append(row_data)
        return table_data

    def get_checkbox(self, row):
        widget = self.table.cellWidget(row, 0)
        if widget is None:
            return None
        chk_box = widget.layout().itemAt(0).widget()
        if isinstance(chk_box, QCheckBox):
            return chk_box
        return None

    @pyqtSlot(str, str)
    def inbounds_tag_changed(self, old_key, new_key):
        with Globals.acquire(Globals.routing_used_inbounds_keys_lock, Globals.inbounds_lock):
            if old_key not in Globals.routing_used_inbounds_keys:
                return
            if old_key != new_key:
                Globals.routing_used_inbounds_keys[new_key] = Globals.routing_used_inbounds_keys.pop(old_key)
            row, col = Globals.routing_used_inbounds_keys[new_key]
            inbounds = self.table.item(row, col).text().split('\n')
            for inbound in inbounds.copy():
                _, key = inbound.split('|')
                if key != old_key:
                    continue
                remarks = Globals.inbounds_dict[new_key]['remarks']
                inbounds.remove(inbound)
                inbounds.append(f'{remarks}|{new_key}')
                inbounds.sort()
                self.table.item(row, col).setText('\n'.join(inbounds))

    def load_data_from_file(self):

        def _clear_table():
            with Globals.routing_used_inbounds_keys_lock:
                Globals.routing_used_inbounds_keys.clear()
            with Globals.routing_used_outbounds_keys_lock:
                Globals.routing_used_outbounds_keys.clear()
                Globals.routing_used_outbounds_through_keys.clear()

            while self.table.rowCount() > 0:
                self.table.removeRow(0)

        _clear_table()

        if not os.path.exists("routing.json"):
            return
        with open("routing.json", "r") as file:
            routings = json.load(file)
        for routing in routings:
            self.add_row(routing)

    @pyqtSlot(str, str)
    def outbounds_tag_changed(self, old_key, new_key):
        with Globals.acquire(Globals.routing_used_outbounds_keys_lock, Globals.outbounds_lock):
            if old_key not in Globals.routing_used_outbounds_keys:
                return
            if old_key != new_key:
                Globals.routing_used_outbounds_keys[new_key] = Globals.routing_used_outbounds_keys.pop(old_key)
            remarks = Globals.outbounds_dict[new_key]['remarks']
            for row, col in Globals.routing_used_outbounds_keys[new_key]:
                self.table.item(row, col).setText(f'{remarks}|{new_key}')

    def reload_rows(self):
        self.load_data_from_file()
        Globals._Log.info(self.user, f'Reload complete.')

    def save_data_to_file(self):
        table_data = self.extract_table_data()
        with open("routing.json", "w") as file:
            json.dump(table_data, file, indent=4)

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        layout.addLayout(top_layout)
        button_add = QPushButton('Add')
        button_add.clicked.connect(self.add_row)
        top_layout.addWidget(button_add)
        button_delete = QPushButton('Delete')
        button_delete.clicked.connect(self.delete_selected_rows)
        top_layout.addWidget(button_delete)
        button_reload = QPushButton('Reload')
        button_reload.clicked.connect(self.reload_rows)
        top_layout.addWidget(button_reload)
        top_layout.addStretch()
        self.checkbox_unique_outbounds = QCheckBox('Unique Outbounds')
        self.checkbox_unique_outbounds.setChecked(True)
        top_layout.addWidget(self.checkbox_unique_outbounds)
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
        self.load_data_from_file()

    def show_inbounds_selection_menu(self, row, column):

        def _checkbox_changed(state, option, row, column):
            current_cell_value = self.table.item(row, column).text()
            if current_cell_value:
                selections = current_cell_value.split('\n')
            else:
                selections = []

            _, key = option.split('|')
            update_signal = False

            if state and option not in selections:
                selections.append(option)
                with Globals.routing_used_inbounds_keys_lock:
                    Globals.routing_used_inbounds_keys[key] = (row, column)
                    update_signal = True
                        
            elif not state and option in selections:
                selections.remove(option)
                with Globals.routing_used_inbounds_keys_lock:
                    del Globals.routing_used_inbounds_keys[key]
                    update_signal = True

            selections.sort()
            self.table.item(row, column).setText('\n'.join(selections))
            if update_signal:
                self.update_inbounds_background_signal.emit(key)

        def _get_current_keys(row):
            current_cell_value = self.table.item(row, 1).text()
            if current_cell_value:
                current_selections = current_cell_value.split('\n')
            else:
                current_selections = []
            current_keys = {}
            for current_selection in current_selections:
                _, key = current_selection.split('|')
                current_keys[key] = current_selection
            return current_keys

        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)

        current_keys = _get_current_keys(row)

        options = []
        with Globals.inbounds_lock:
            inbounds_keys = Globals.inbounds_dict.keys()
            for key in inbounds_keys:
                options.append(f'{Globals.inbounds_dict[key]["remarks"]}|{key}')
        options.sort()

        with Globals.routing_used_inbounds_keys_lock:
            used_keys = Globals.routing_used_inbounds_keys.keys()

        for key in current_keys:
            if key in inbounds_keys:
                continue
            checkbox = QCheckBox(current_keys[key])
            checkbox.setChecked(True)
            checkbox.setStyleSheet("QCheckBox { background-color: red; }")
            checkbox.stateChanged.connect(lambda state, opt=current_keys[key]: _checkbox_changed(state, opt, row, column))
            menu_layout.addWidget(checkbox)

        for option in options:
            _, key = option.split('|')
            if key in used_keys and key not in current_keys:
                continue
            checkbox = QCheckBox(option)
            checkbox.setChecked(key in current_keys)
            checkbox.stateChanged.connect(lambda state, opt=option: _checkbox_changed(state, opt, row, column))
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

        def _button_clicked(button_text, menu, row, column):
            old_text = self.table.item(row, column).text()
            old_key = ''
            if old_text == button_text:
                menu.close()
                return
            if old_text:
                _, _, old_key = old_text.split('|')
                with Globals.routing_used_outbounds_keys_lock:
                    if len(Globals.routing_used_outbounds_keys[old_key]) == 1:
                        del Globals.routing_used_outbounds_keys[old_key]
                    else:
                        Globals.routing_used_outbounds_keys[old_key].remove((row, column))
            self.table.item(row, column).setText(button_text)
            if button_text:
                _, _, new_key = button_text.split('|')
                with Globals.routing_used_outbounds_keys_lock:
                    if new_key in Globals.routing_used_outbounds_keys:
                        Globals.routing_used_outbounds_keys[new_key].append((row, column))
                    else:
                        Globals.routing_used_outbounds_keys[new_key] = [(row, column)]
            self.update_outbounds_background_by_row(row, old_key)
            menu.close()

        def _make_options(current_text, row, column):
            with Globals.routing_used_outbounds_keys_lock:
                through_keys = Globals.routing_used_outbounds_through_keys.copy()
                used_keys = set(Globals.routing_used_outbounds_keys.keys())
                end_keys = used_keys - through_keys

            with Globals.outbounds_lock:
                data = Globals.outbounds_dict.copy()
            all_keys = set(data.keys())

            last_col = 0
            for col in range(2, len(self.columns)):
                opt = self.table.item(row, col).text()
                if not opt:
                    continue
                last_col = col

            if self.checkbox_unique_outbounds.isChecked():
                if column >= last_col:
                    keys = all_keys - used_keys
                else:
                    keys = all_keys - end_keys
            else:
                if column >= last_col:
                    keys = all_keys - through_keys
                else:
                    keys = all_keys - end_keys

            options = []
            for key in keys:
                source_tag = data.get(key, {}).get('source_tag', '')
                remarks = data.get(key, {}).get('remarks', '')
                options.append(f'{remarks}|{source_tag}|{key}')

            if current_text:
                if current_text not in options:
                    options.append(current_text)

            options.sort()
            return options


        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        custom_menu = QMenu(self)
        button = QPushButton('')
        button.clicked.connect(lambda _, opt='', menu=custom_menu: _button_clicked(opt, menu, row, column))
        menu_layout.addWidget(button)

        current_text = self.table.item(row, column).text()

        options = _make_options(current_text, row, column)

        if current_text and current_text not in options:
            button = QPushButton(current_text)
            button.setStyleSheet("QPushButton { background-color: red; }")
            button.clicked.connect(lambda _, opt=current_text, menu=custom_menu: _button_clicked(opt, menu, row, column))
            menu_layout.addWidget(button)

        for option in options:
            button = QPushButton(option)
            button.clicked.connect(lambda _, opt=option, menu=custom_menu: _button_clicked(opt, menu, row, column))
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

    def update_inbounds_background(self, keys):
        for key in keys:
            self.update_inbounds_background_signal.emit(key)

    def update_outbounds_background(self, keys):
        for key in keys:
            self.update_outbounds_background_signal.emit(key)

    def update_outbounds_background_by_row(self, row, old_key):
        keys = []
        for col in range(2, len(self.columns)):
            opt = self.table.item(row, col).text()
            if not opt:
                continue
            _, _, key = opt.split('|')
            keys.append(key)

        with Globals.routing_used_outbounds_keys_lock:
            outbounds_keys = Globals.routing_used_outbounds_keys.keys()
            if old_key and old_key not in outbounds_keys:
                if old_key in Globals.routing_used_outbounds_through_keys:
                    Globals.routing_used_outbounds_through_keys.discard(old_key)
            for idx, key in enumerate(keys):
                if idx < len(keys)-1:
                    if key in Globals.routing_used_outbounds_through_keys:
                        continue
                    Globals.routing_used_outbounds_through_keys.add(key)
                else:
                    if key not in Globals.routing_used_outbounds_through_keys:
                        continue
                    Globals.routing_used_outbounds_through_keys.discard(key)

        keys.append(old_key)
        self.update_outbounds_background(keys)
