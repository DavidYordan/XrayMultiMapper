import os
import shutil
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import filedialog

def create_directory(path):
    final_path = os.path.join(path, 'V2XrayMultiMapper')
    if not os.path.exists(final_path):
        os.makedirs(final_path)
    return final_path

def create_shortcut_with_vbscript(target, shortcut_name):
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    vbscript = f"""
    Set oWS = WScript.CreateObject("WScript.Shell")
    sLinkFile = "{desktop_path}\\{shortcut_name}.lnk"
    Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = "{target}"
    oLink.Save
    """
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.vbs') as vbs:
        vbs.write(vbscript)
        vbs_path = vbs.name
    subprocess.run(["cscript", vbs_path], shell=True)
    os.remove(vbs_path)

def choose_directory():
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(title="Select Working Directory")
    return path

def extract_resources(source_dir, target_dir):
    resource_paths = ['json_model', 'v2ray', 'xray', 'img', 'dist']
    for resource_path in resource_paths:
        full_source_path = os.path.join(source_dir, resource_path)
        full_target_path = os.path.join(target_dir, resource_path)
        if not os.path.exists(full_source_path):
            continue
        if resource_path == 'dist':
            shutil.copy(
                os.path.join(full_source_path, 'V2XrayMultiMapper.exe'),
                os.path.join(target_dir, 'V2XrayMultiMapper.exe')
            )
        else:
            shutil.copytree(full_source_path, full_target_path)

def main():
    chosen_dir = choose_directory()
    if not chosen_dir:
        print("No directory chosen. Exiting...")
        return

    working_dir = create_directory(chosen_dir)
    print(f"Extracting resources to: {working_dir}")

    try:
        base_path = sys._MEIPASS
    except Exception as e:
        print(f'{e}')
        return

    extract_resources(base_path, working_dir)

    exe_path = os.path.join(working_dir, 'V2XrayMultiMapper.exe')
    create_shortcut_with_vbscript(exe_path, 'V2XrayMultiMapper')

    subprocess.Popen([exe_path])

if __name__ == '__main__':
    main()
