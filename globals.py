from threading import Lock

local_original_cell_values = {}
local_original_cell_values_lock = Lock()
proxy_original_cell_values = {}
proxy_original_cell_values_lock = Lock()
routing_original_cell_values = {}
routing_original_cell_values_lock = Lock()
routing_used_inbound_options = set()
routing_used_inbound_options_lock = Lock()