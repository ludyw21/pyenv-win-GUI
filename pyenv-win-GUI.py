# Author: primetime43
# GitHub: https://github.com/primetime43
# Version of the script
__version__ = '1.0.1'

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import subprocess
import os
import threading
import json
import requests
import re
import sys

# 从独立文件导入语言包
from language_pack import language_pack

# 当前语言设置
current_language = 'en'

# 配置文件路径
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# pyenv版本信息
local_version = None
latest_version = None

# 读取配置文件
def load_config():
    global current_language, local_version
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'language' in config:
                    current_language = config['language']
                if 'local_version' in config:
                    local_version = config['local_version']
    except Exception as e:
        print(f"Error loading config: {e}")

# 保存配置文件
def save_config():
    try:
        config = {'language': current_language}
        if local_version:
            config['local_version'] = local_version
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving config: {e}")

# 切换语言函数
def change_language(event=None):
    global current_language
    current_language = language_var.get()
    save_config()
    update_ui_language()

# 更新UI语言
def update_ui_language():
    # 更新按钮文本
    install_button.config(text=language_pack[current_language]['install_button'])
    update_button.config(text=language_pack[current_language]['update_button'])
    uninstall_button.config(text=language_pack[current_language]['uninstall_button'])
    command_label.config(text=language_pack[current_language]['command_label'])
    params_label.config(text=language_pack[current_language]['params_label'])
    run_button.config(text=language_pack[current_language]['run_button'])
    clear_button.config(text=language_pack[current_language]['clear_button'])
    # 更新命令描述
    update_description()

# 检查本地pyenv版本
def check_local_version():
    global local_version
    # 首先检查是否已从配置文件加载了版本信息
    if local_version:
        return f"v{local_version}"
    
    # 如果配置文件中没有版本信息，则执行命令获取
    try:
        version_output = subprocess.check_output(['powershell', '-Command', 'pyenv --version'], stderr=subprocess.STDOUT).decode().strip()
        # 匹配类似 "pyenv 3.1.1" 的输出
        match = re.search(r'pyenv\s+([0-9.]+)', version_output)
        if match:
            local_version = match.group(1)
            # 获取到版本后保存到配置文件
            save_config()
            return f"v{local_version}"
        return None
    except subprocess.CalledProcessError:
        # 如果未安装pyenv，清除本地版本信息
        local_version = None
        save_config()
        return None
    except Exception as e:
        print(f"Error checking local version: {e}")
        return None

# 从GitHub获取最新版本
def get_latest_version():
    global latest_version
    try:
        # 使用GitHub API获取最新tag
        response = requests.get('https://api.github.com/repos/pyenv-win/pyenv-win/tags', timeout=5)
        if response.status_code == 200:
            tags = response.json()
            if tags:
                # 获取第一个tag（通常是最新的）
                latest_tag = tags[0]['name']
                # 提取版本号，移除可能的v前缀
                latest_version = latest_tag.lstrip('v')
                return f"v{latest_version}"
        return None
    except Exception as e:
        print(f"Error getting latest version: {e}")
        return None

# 全局版本标签变量
version_label = None

# 创建版本信息标签
def create_version_info_label(parent_frame):
    global version_label
    
    # 检查本地版本
    local_version_text = check_local_version()
    
    # 获取最新版本
    latest_version_text = get_latest_version()
    
    # 检查是否需要隐藏按钮
    if local_version_text:
        # 如果已安装，隐藏安装按钮
        try:
            install_button.pack_forget()
        except:
            pass
    else:
        # 如果未安装，隐藏更新按钮
        try:
            update_button.pack_forget()
        except:
            pass
    
    # 创建版本信息文本
    version_info = []
    if local_version_text:
        version_info.append(f"当前: {local_version_text}")
    else:
        version_info.append("未安装pyenv")
    
    if latest_version_text:
        version_info.append(f"最新: {latest_version_text}")
    else:
        version_info.append("请确保能访问github，大陆地区建议开启TUN")
    
    # 创建并显示版本标签
    version_label = ttk.Label(parent_frame, text=" | ".join(version_info), font=("Arial", 10), padding=(10, 5))
    version_label.pack(anchor=W)

# 更新版本信息显示
def update_version_display():
    global version_label
    
    if version_label:
        # 销毁现有标签
        version_label.destroy()
    
    # 重新创建版本信息标签
    create_version_info_label(version_frame)
    
    # 重新调整按钮显示
    try:
        # 先重新显示所有按钮
        install_button.pack(side=LEFT, padx=(0, 5))
        update_button.pack(side=LEFT, padx=(0, 5))
        
        # 然后根据安装状态隐藏相应按钮
        if local_version:
            install_button.pack_forget()
        else:
            update_button.pack_forget()
    except:
        pass

# 加载配置
load_config()

def run_ps1(uninstall=False):
    # This function handles the installation and uninstallation of pyenv
    global local_version

    # Skip the check if pyenv is installed when uninstalling
    if not uninstall:
        # Check if pyenv is installed by running a PowerShell command
        try:
            version = subprocess.check_output(['powershell', '-Command', 'pyenv --version'])
            output_text.insert(END, language_pack[current_language]['already_installed'] + "\n")
            output_text.insert(END, version.decode() + "\n")
            output_text.see(END)
            # 更新版本信息并保存到配置文件
            version_str = version.decode().strip()
            match = re.search(r'pyenv\s+([0-9.]+)', version_str)
            if match:
                local_version = match.group(1)
                save_config()
                # 更新界面版本显示
                update_version_display()
            return  # Return immediately if pyenv is already installed
        except subprocess.CalledProcessError:
            pass  # If pyenv is not installed, continue with the installation

    # If pyenv is not installed and uninstall is requested, display message
    if uninstall:
        try:
            subprocess.check_output(['powershell', '-Command', 'pyenv --version'])
        except subprocess.CalledProcessError:
            output_text.insert(END, language_pack[current_language]['not_installed'] + "\n")
            output_text.see(END)
            return

    # Check if the installation script is present, if not, download it
    if not os.path.exists("./install-pyenv-win.ps1"):
        ps_command = 'Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"'
        command = ['powershell', '-Command', ps_command]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Prepare and execute the installation or uninstallation command
    if uninstall:
        output_text.insert(END, language_pack[current_language]['starting_uninstallation'] + "\n")
        command = ['powershell', '-Command', '&"./install-pyenv-win.ps1" -Uninstall']
    else:
        output_text.insert(END, language_pack[current_language]['starting_installation'] + "\n")
        command = ['powershell', '-Command', '&"./install-pyenv-win.ps1"']

    output_text.see(END)

    # Run the command in a subprocess and capture the output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # Read and display the output from the subprocess
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            output_text.insert(END, output.decode())
            output_text.see(END)
    rc = process.poll()
    
    # 安装或更新完成后，获取版本并更新配置文件
    if not uninstall:
        # 等待一会儿让环境变量生效
        import time
        time.sleep(2)
        # 获取新安装/更新的版本
        try:
            # 使用新的PowerShell进程来获取版本信息
            version_output = subprocess.check_output(['powershell', '-Command', 'pyenv --version'], stderr=subprocess.STDOUT).decode().strip()
            match = re.search(r'pyenv\s+([0-9.]+)', version_output)
            if match:
                local_version = match.group(1)
                save_config()
                output_text.insert(END, f"\npyenv 已成功安装/更新到版本: v{local_version}\n")
                # 更新界面版本显示
                root.after(0, update_version_display)
        except Exception as e:
            output_text.insert(END, f"\n获取版本信息时出错: {e}\n")
    else:
        # 卸载完成后清除版本信息
        local_version = None
        save_config()
        # 更新界面版本显示
        root.after(0, update_version_display)

def install():
    # Start a new thread for installing pyenv
    threading.Thread(target=run_ps1, args=(False,)).start()

def update():
    # Start a new thread for updating pyenv
    threading.Thread(target=run_ps1, args=(False,)).start()

def uninstall():
    # Start a new thread for uninstalling pyenv
    threading.Thread(target=run_ps1, args=(True,)).start()
    
def clear_output():
    # Clear the output text area
    output_text.delete('1.0', END)

def run_command():
    # Run a pyenv command using PowerShell and display the output
    command = ['powershell', '-Command', f'pyenv {command_var.get()} {params_entry.get()}']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

    # Read and display the output from the subprocess
    for line in iter(process.stdout.readline, b''):
        output_text.insert(END, line.decode())
        output_text.see(END)
    process.stdout.close()
    process.wait()

# Create the main window with ttkbootstrap theme
root = ttk.Window(themename="flatly")
root.title(f"pyenv-win GUI - Version {__version__}")  # Set the title of the window

# Configure grid weights
root.grid_columnconfigure(0, weight=1)

# Create a frame for version info (first row)
version_frame = ttk.Frame(root)
version_frame.grid(row=0, column=0, sticky='ew', pady=(10, 0), padx=(10, 0))

# Create a frame for the action buttons and language (second row)
action_frame = ttk.Frame(root)
action_frame.grid(row=1, column=0, sticky='ew', pady=(0, 10), padx=(10, 0))

# Create a subframe for buttons to keep them left-aligned
action_buttons_frame = ttk.Frame(action_frame)
action_buttons_frame.pack(side=LEFT)

# Create the Install button with ttkbootstrap style
install_button = ttk.Button(action_buttons_frame, text=language_pack[current_language]['install_button'], command=install, bootstyle=SUCCESS)
install_button.pack(side=LEFT, padx=(0, 5))

# Create the Update button with ttkbootstrap style
update_button = ttk.Button(action_buttons_frame, text=language_pack[current_language]['update_button'], command=update, bootstyle=PRIMARY)
update_button.pack(side=LEFT, padx=(0, 5))

# Create the Uninstall button with ttkbootstrap style
uninstall_button = ttk.Button(action_buttons_frame, text=language_pack[current_language]['uninstall_button'], command=uninstall, bootstyle=DANGER)
uninstall_button.pack(side=LEFT)

# 创建版本信息标签
create_version_info_label(version_frame)

# Create language selection frame
language_frame = ttk.Frame(action_frame)
language_frame.pack(side=RIGHT, padx=(10, 0))

# Language label
language_label = ttk.Label(language_frame, text="Language / 语言:")
language_label.pack(side=LEFT, padx=(0, 5))

# Language variable
language_var = ttk.StringVar(value=current_language)

# Language combobox
language_menu = ttk.Combobox(language_frame, textvariable=language_var, values=['en', 'zh'], width=8)
language_menu.pack(side=LEFT)

# Bind language change event
language_menu.bind('<<ComboboxSelected>>', change_language)

# List of commands for the dropdown menu
commands = ['commands', 'duplicate', 'local', 'global', 'shell', 'install', 'uninstall', 'update', 'rehash', 'vname', 'version', 'version-name', 'versions', 'exec', 'which', 'whence']

# Create a frame for the commands section
commands_frame = ttk.Frame(root)
commands_frame.grid(row=2, column=0, sticky='w', pady=(0, 10), padx=(10, 0))

# Create a label for the commands dropdown
command_label = ttk.Label(commands_frame, text=language_pack[current_language]['command_label'])
command_label.pack(side=LEFT, padx=(0, 5))

# Create a variable for the selected command
command_var = ttk.StringVar(root)
command_var.set(commands[0])  # Set the default option

# Create the dropdown menu for the commands
command_menu = ttk.Combobox(commands_frame, textvariable=command_var, values=commands, width=15)
command_menu.pack(side=LEFT, padx=(0, 10))

# Create a description label that shows the selected command's description
description_label = ttk.Label(commands_frame, text="", wraplength=700, justify=LEFT)
description_label.pack(side=LEFT, fill=X, expand=True)

# Function to update description when command is selected
def update_description(event=None):
    selected_command = command_var.get()
    if selected_command in language_pack[current_language]['command_descriptions']:
        description_label.config(text=language_pack[current_language]['command_descriptions'][selected_command])

# Bind the update function to the combobox selection
command_menu.bind('<<ComboboxSelected>>', update_description)

# Initialize the description
update_description()

# Create a frame for the parameters input
params_frame = ttk.Frame(root)
params_frame.grid(row=3, column=0, sticky='w', pady=(0, 10), padx=(10, 0))  # Place the frame in the grid, aligned with commands

# Create a label for the parameters input
params_label = ttk.Label(params_frame, text=language_pack[current_language]['params_label'])
params_label.pack(side=LEFT, padx=(0, 5))  # Place the label in the frame

# Create the parameters input box
params_entry = ttk.Entry(params_frame, width=50)
params_entry.pack(side=LEFT)  # Place the input box in the frame

# Create the Run Command button with ttkbootstrap style
run_button = ttk.Button(root, text=language_pack[current_language]['run_button'], command=run_command, bootstyle=PRIMARY)
run_button.grid(row=4, column=0, sticky='w', pady=(0, 5), padx=(10, 0))  # Place the button in the grid

# Create the output text box with ttkbootstrap style
output_text = ttk.Text(root)
output_text.grid(row=5, column=0, sticky='nsew', pady=5, padx=(10, 0))  # Place the text box in the grid

# Create the scrollbar for the output text box with ttkbootstrap style
scrollbar = ttk.Scrollbar(root, command=output_text.yview, bootstyle=SECONDARY)
scrollbar.grid(row=5, column=1, sticky='ns', pady=5)  # Place the scrollbar in the grid

# Link the scrollbar to the output text box
output_text['yscrollcommand'] = scrollbar.set

# Configure grid weights to make the output text box expandable
root.grid_rowconfigure(5, weight=1)
root.grid_columnconfigure(0, weight=1)

# Create the Clear Output button with ttkbootstrap style
clear_button = ttk.Button(root, text=language_pack[current_language]['clear_button'], command=clear_output, bootstyle=WARNING)
clear_button.grid(row=6, column=0, sticky='w', pady=(5, 10), padx=(10, 0))  # Place the button in the grid

# Start the main event loop
root.mainloop()
