import io
import os
import re
from paramiko import (
    AutoAddPolicy,
    RSAKey,
    SSHClient
)
from paramiko.util import log_to_file
from select import select
from threading import Event, Thread

from globals import Globals

class Openwrt(SSHClient):
    def __init__(self, connect_host_failed_signal, update_menu_signal, logger=False):
        super().__init__()

        self._is_connected = False
        self.connect_host_failed_signal = connect_host_failed_signal
        self.host = None
        self.realtime_thread = None
        self.stop_event = Event()
        self.update_menu_signal = update_menu_signal
        self.workPath = os.getcwd()
        self.keyPath = os.path.join(self.workPath, '.ssh')
        self.user = 'Openwrt'

        if not os.path.exists(self.keyPath):
            os.mkdir(self.keyPath)

        if logger:
            log_to_file(os.path.join(self.workPath, 'logs', 'openwrt.log'))

        self.set_missing_host_key_policy(AutoAddPolicy())

        Globals._Log.info(self.user, 'Openwrt successfully initialized.')

    def close(self):
        self.stop_realtime_threading()
        super().close()
        Globals._Log.info(self.user, 'Connection closed.')
        self.is_connected()

    def connect(self, hostname, username=None, password=None):
        if not username:
            username = self.get_username_for_host(hostname)

        if not username:
            Globals._Log.error(self.user, f'No username found for host {hostname}')
            self.connect_host_failed_signal.emit(hostname)
            return
        
        private_key_file = os.path.join(self.keyPath, f'id_rsa_{username}@{hostname}')
        try:
            if username and password:
                Globals._Log.info(self.user, f'Attempting to connect to {hostname} with username/password.')
                super().connect(hostname=hostname, username=username, password=password)
                Globals._Log.info(self.user, f'Connected to {hostname} using username/password.')
                self.generate_and_save_ssh_keys(username, hostname)
            elif os.path.exists(private_key_file):
                Globals._Log.info(self.user, f'Attempting to connect to {hostname} with SSH key.')
                super().connect(hostname=hostname, username=username, key_filename=private_key_file)
                Globals._Log.info(self.user, f'Connected to {hostname} using SSH key.')
            else:
                Globals._Log.error(self.user, f'No valid authentication method found for {hostname}')
                self.connect_host_failed_signal.emit(hostname)
                return

            self.is_connected()

        except Exception as e:
            Globals._Log.error(self.user, f'Connection failed for {hostname}: {e}')
            self.connect_host_failed_signal.emit(hostname)
            self.is_connected()

    def exec_command(self, command, bufsize=-1, timeout=None, get_pty=False):
        if not self.is_connected():
            stderr = io.StringIO("Attempt to execute command failed: Connection is not active.")
            stdin = io.StringIO("")
            stdout = io.StringIO("")
            return stdin, stdout, stderr

        return super().exec_command(command, bufsize, timeout, get_pty)

    def exec_command_with_realtime_output(self, command):
        
        if self.realtime_thread and self.realtime_thread.is_alive():
            Globals._Log.error(self.user, 'A command is already running. Please wait until it finishes.')
            return

        self.realtime_thread = Thread(target=self.realtime_threading, args=(command,))
        self.realtime_thread.daemon = True
        self.realtime_thread.start()

    def exec_ssh_command(self, command):
        try:
            stdin, stdout, stderr = self.exec_command(command)
            error_output = stderr.read().decode().strip()
            if error_output:
                Globals._Log.error(self.user, f'Command failed: {error_output}')
                return False
            return True
        except Exception as e:
            Globals._Log.error(self.user, f'Exception during command execution: {e}')
            return False
        
    def generate_and_save_ssh_keys(self, username, hostname):
        try:
            new_private_key = RSAKey.generate(bits=2048)
            public_key = f"{new_private_key.get_name()} {new_private_key.get_base64()}"

            self.exec_command(f'mkdir -p ~/.ssh && echo "{public_key}" >> /etc/dropbear/authorized_keys')

            private_key_file = os.path.join(self.keyPath, f'id_rsa_{username}@{hostname}')
            new_private_key.write_private_key_file(private_key_file)
            Globals._Log.info(self.user, f'SSH keys generated and saved for {hostname}.')

        except Exception as e:
            Globals._Log.error(self.user, f'Error generating and saving SSH keys: {e}')
    
    def get_known_hosts(self):
        known_hosts = []
        pattern = re.compile(r'id_rsa_(.+)@(.+)')
        for filename in os.listdir(self.keyPath):
            match = pattern.match(filename)
            if not match:
                continue
            username, hostname = match.groups()
            known_hosts.append(hostname)
        return known_hosts
    
    def get_username_for_host(self, hostname):
        pattern = re.compile(r'id_rsa_(.+)@' + re.escape(hostname))
        for filename in os.listdir(self.keyPath):
            match = pattern.match(filename)
            if not match:
                continue
            return match.group(1)
        return None
    
    def is_connected(self):
        transport = self.get_transport()
        current_state = transport and transport.is_active()

        if current_state == self._is_connected:
            return current_state
        
        if current_state:
            self.host = transport.getpeername()[0]
        else:
            self.host = None

        self._is_connected = current_state
        self.update_menu_signal.emit()

        return current_state
    
    def stop_process(self, process):
        if not self.exec_ssh_command(f'killall {process}'):
            return False
        Globals._Log.info(self.user, f'Process {process} stopped successfully.')
        return True
    
    def stop_realtime_threading(self):
        if self.realtime_thread and self.realtime_thread.is_alive():
            self.stop_event.set()
            self.realtime_thread.join()
            self.realtime_thread = None
            self.stop_event.clear()
            Globals._Log.info(self.user, 'Real-time thread stopped successfully.')

    def realtime_threading(self, command):
        if not self.is_connected():
            Globals._Log.error(self.user, 'Attempt to execute command failed: Connection is not active.')
            return

        stdin, stdout, stderr = super().exec_command(command)
        while not self.stop_event.is_set():
            ready, _, _ = select([stdout.channel], [], [], 0.5)
            if not ready:
                continue
            line = stdout.readline()
            if not line:
                break
            Globals._Log.info(self.user, line.strip())

        error_output = stderr.read().decode()
        if error_output:
            Globals._Log.error(self.user, f'Realtime thread error: {error_output}')

    
    def run_xray(self, config_json, nftables_conf):

        def _update_firewall(nftables_conf):
            if not self.exec_ssh_command(f"echo '{nftables_conf}' > /etc/nftables.conf"):
                return False
            Globals._Log.info('main', f'Successfully wrote nftables.conf.')

            if not self.exec_ssh_command('nft -f /etc/nftables.conf'):
                return False
            Globals._Log.info('main', 'Successfully reloaded nftables rules.')
            
            if not self.exec_ssh_command('/etc/init.d/firewall restart'):
                return False
            Globals._Log.info('main', 'Successfully restarted the firewall.')
            return True

        if not self.stop_realtime_threading():
            return
        
        if not self.stop_process('xray'):
            return

        if not self.exec_ssh_command(f"echo '{config_json}' > /etc/xray/config.json"):
            return
        Globals._Log.info('main', 'Successfully wrote Xray config.json.')

        if not _update_firewall(nftables_conf):
            return

        self.exec_command_with_realtime_output('xray run --config /etc/xray/config.json')