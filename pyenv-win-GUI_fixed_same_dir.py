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

# 配置文件路径 - 使用与可执行文件相同的目录存储文件
# 处理PyInstaller打包后的情况
if getattr(sys, 'frozen', False):
    # 已打包为exe文件
    app_dir = os.path.dirname(sys.executable)
else:
    # 直接运行Python脚本
    app_dir = os.path.dirname(os.path.abspath(__file__))

# 文件路径定义
config_file = os.path.join(app_dir, 'config.json')
AVAILABLE_VERSIONS_FILE = os.path.join(app_dir, 'available_versions.txt')
INSTALLED_VERSIONS_FILE = os.path.join(app_dir, 'installed_versions.txt')

# pyenv版本信息
local_version = None
latest_version = None
global_version = None

# 读取配置文件
def load_config():
    global current_language, local_version, global_version
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'language' in config:
                    current_language = config['language']
                if 'local_version' in config:
                    local_version = config['local_version']
                if 'global_version' in config:
                    global_version = config['global_version']
    except Exception as e:
        print(f"Error loading config: {e}")

# 保存配置文件
def save_config():
    try:
        config = {'language': current_language}
        if local_version:
            config['local_version'] = local_version
        if global_version:
            config['global_version'] = global_version
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
    # 更新命令列表
    update_commands_list()
    # 更新版本信息显示（包括语言切换）
    update_version_display()

# 检查本地pyenv版本
def check_local_version():
    global local_version
    # 首先检查是否已从配置文件加载了版本信息
    if local_version:
        return f"v{local_version}"
    
    # 如果配置文件中没有版本信息，则执行命令获取
    try:
        version_output = subprocess.check_output(['powershell', '-Command', 'pyenv --version'], stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
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

# 检查全局Python版本
def check_global_version():
    global global_version
    # 首先检查是否已从配置文件加载了版本信息
    if global_version:
        return f"v{global_version}"
    
    # 如果配置文件中没有版本信息，则执行命令获取
    try:
        version_output = subprocess.check_output(['powershell', '-Command', 'pyenv global'], stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
        # 如果输出不为空且不是错误信息
        if version_output and not version_output.startswith(('Error', '错误')):
            # 移除可能的前导/尾随空格和换行符
            global_version = version_output.strip()
            # 获取到版本后保存到配置文件
            save_config()
            return f"v{global_version}"
        return "未设置"
    except subprocess.CalledProcessError:
        # 如果执行失败，清除全局版本信息
        global_version = None
        save_config()
        return "未设置"
    except Exception as e:
        print(f"Error checking global version: {e}")
        return "未设置"

# 从GitHub获取最新版本 - 异步版本
def get_latest_version_async():
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
                # 在主线程中更新UI
                root.after(0, lambda: update_latest_version_display())
                # 保存到配置文件
                save_config()
    except Exception as e:
        print(f"Error getting latest version: {e}")

# 同步获取最新版本（有缓存机制）
def get_latest_version():
    global latest_version
    # 如果已有缓存的版本信息，直接返回
    if latest_version:
        return f"v{latest_version}"
    # 没有缓存时返回None，异步获取将在后台进行
    # 启动异步线程获取最新版本
    threading.Thread(target=get_latest_version_async, daemon=True).start()
    return None

# 更新最新版本显示
def update_latest_version_display():
    # 查找所有显示最新版本的标签并更新它们
    for widget in version_frame.winfo_children():
        if isinstance(widget, ttk.Frame):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Label):
                    # 检查标签文本是否包含最新版本的前缀
                    text = child.cget("text")
                    if language_pack[current_language]['latest_version'] in text and "github" not in text.lower():
                        # 更新标签文本
                        child.config(text=f"{language_pack[current_language]['latest_version']} v{latest_version}")

# 全局版本标签变量
version_label = None

# 创建版本信息标签

def open_github_link(event):
    # 在点击时打开浏览器访问GitHub链接
    import webbrowser
    webbrowser.open('https://github.com/pyenv-win/pyenv-win/tags')

def create_version_info_label(parent_frame):
    global version_label
    
    # 检查本地版本
    local_version_text = check_local_version()
    
    # 获取最新版本
    latest_version_text = get_latest_version()
    
    # 检查全局Python版本
    global_version_text = check_global_version()
    
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
    
    # 创建主版本信息标签，所有信息将显示在同一行
    main_info_frame = ttk.Frame(parent_frame)
    main_info_frame.pack(anchor=W)
    
    # 首先添加当前版本信息
    if local_version_text:
        current_label = ttk.Label(main_info_frame, text=f"{language_pack[current_language]['current_version']} {local_version_text}", font=("Arial", 10), padding=(10, 2))
        current_label.pack(side=LEFT)
    else:
        not_installed_label = ttk.Label(main_info_frame, text=language_pack[current_language]['not_installed_pyenv'], font=("Arial", 10), padding=(10, 2))
        not_installed_label.pack(side=LEFT)
    
    # 如果有本地版本，继续添加其他信息
    if local_version_text:
        # 添加分隔符
        separator1_label = ttk.Label(main_info_frame, text=" | ", font=("Arial", 10), padding=(0, 2))
        separator1_label.pack(side=LEFT)
        
        # 添加最新版本信息
        if latest_version_text:
            latest_label = ttk.Label(main_info_frame, text=f"{language_pack[current_language]['latest_version']} {latest_version_text}", font=("Arial", 10), padding=(0, 2))
            latest_label.pack(side=LEFT)
        else:
            # 无法获取最新版本时，在"最新:"后面显示GitHub访问提示
            latest_prefix_label = ttk.Label(main_info_frame, text=f"{language_pack[current_language]['latest_version']} ", font=("Arial", 10), padding=(0, 2))
            latest_prefix_label.pack(side=LEFT)
            
            # 添加前缀文本
            prefix_label = ttk.Label(main_info_frame, text=language_pack[current_language]['ensure_github_access'], font=("Arial", 10), padding=(0, 2))
            prefix_label.pack(side=LEFT)
            
            # 添加github超链接标签
            github_label = ttk.Label(main_info_frame, text=language_pack[current_language]['github_text'], font=("Arial", 10, "underline"), foreground="blue", padding=(0, 2))
            github_label.pack(side=LEFT)
            # 绑定点击事件
            github_label.bind("<Button-1>", open_github_link)
        
        # 添加分隔符
        separator2_label = ttk.Label(main_info_frame, text=" | ", font=("Arial", 10), padding=(0, 2))
        separator2_label.pack(side=LEFT)
        
        # 添加全局版本信息
        global_version_label = ttk.Label(main_info_frame, text=f"{language_pack[current_language]['py_global_version']} {global_version_text}", font=("Arial", 10), padding=(0, 2))
        global_version_label.pack(side=LEFT)
    
    # 保存标签引用
    version_label = main_info_frame

# 更新版本信息显示
def update_version_display():
    global version_label
    
    # 强制销毁version_frame中的所有控件，确保完全清除旧标签
    for widget in version_frame.winfo_children():
        widget.destroy()
    
    # 语言切换时不需要重新获取版本信息，只需要重新显示UI
    # 但如果是首次显示或版本信息未获取，需要确保有版本数据
    if local_version is None:
        check_local_version()
    if global_version is None:
        check_global_version()
    
    # 异步获取最新版本（如果尚未获取）
    if latest_version is None:
        get_latest_version()
    
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
    except Exception as e:
        print(f"Error updating buttons: {e}")
    
    # 强制更新GUI以确保显示最新内容
    root.update_idletasks()

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
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

    # Prepare and execute the installation or uninstallation command
    if uninstall:
        output_text.insert(END, language_pack[current_language]['starting_uninstallation'] + "\n")
        command = ['powershell', '-Command', '&"./install-pyenv-win.ps1" -Uninstall']
    else:
        output_text.insert(END, language_pack[current_language]['starting_installation'] + "\n")
        command = ['powershell', '-Command', '&"./install-pyenv-win.ps1"']

    output_text.see(END)

    # Run the command in a subprocess and capture the output
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

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
            version_output = subprocess.check_output(['powershell', '-Command', 'pyenv --version'], stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
            match = re.search(r'pyenv\s+([0-9.]+)', version_output)
            if match:
                local_version = match.group(1)
                save_config()
                output_text.insert(END, f"\n{language_pack[current_language]['successfully_installed_updated']} v{local_version}\n")
                # 更新界面版本显示
                root.after(0, update_version_display)
        except Exception as e:
            output_text.insert(END, f"\n{language_pack[current_language]['error_getting_version']} {e}\n")
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
    selected_command_text = command_var.get()
    # 使用get_command_name函数提取命令部分
    selected_command = get_command_name(selected_command_text)
    params = params_var.get()  # 从params_var获取参数
    
    # 检查是否是install -l命令
    is_install_list = (selected_command == 'install' and params == '-l')
    
    # 检查是否是global命令（无参数）来获取已安装版本
    is_global_no_params = (selected_command == 'global' and (not params or params == language_pack[current_language]['run_global_first']))
    
    # 对于global命令，如果参数是提示信息，则使用空参数
    if selected_command == 'global' and params == language_pack[current_language]['run_global_first']:
        command = ['powershell', '-Command', f'pyenv {selected_command}']
    else:
        command = ['powershell', '-Command', f'pyenv {selected_command} {params}']
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)

    # Read and display the output from the subprocess
    output_lines = []
    for line in iter(process.stdout.readline, b''):
        line_text = line.decode()
        output_text.insert(END, line_text)
        output_text.see(END)
        output_lines.append(line_text)
    process.stdout.close()
    process.wait()
    
    # 处理install -l命令的特殊情况
    if is_install_list:
        if handle_install_list(output_lines):
            output_text.insert(END, f"\n{language_pack[current_language]['updated_available_versions']}\n")
    # 处理global命令（无参数）的特殊情况，用于获取已安装版本
    elif is_global_no_params:
        # 解析输出获取已安装版本
        installed_versions = []
        for line in output_lines:
            line = line.strip()
            # 跳过空行和错误信息行
            if line and not any(err_msg in line.lower() for err_msg in ['error', '错误', 'failed']):
                # 尝试匹配版本号格式（简单判断，假设版本号包含数字和点）
                if any(char.isdigit() for char in line) and '.' in line:
                    installed_versions.append(line)
        
        # 如果找到了版本信息，更新文件和下拉框
        if installed_versions:
            if update_installed_versions_file(installed_versions):
                output_text.insert(END, f"\n{language_pack[current_language]['updated_installed_versions']}\n")
                # 更新下拉框
                update_global_params_combobox()
        else:
            # 如果没有找到有效版本，尝试直接运行pyenv versions命令
            output_text.insert(END, f"\n{language_pack[current_language]['trying_get_installed_versions']}\n")
            versions_command = ['powershell', '-Command', 'pyenv versions']
            versions_process = subprocess.Popen(versions_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
            
            versions_output = []
            for line in iter(versions_process.stdout.readline, b''):
                line_text = line.decode()
                versions_output.append(line_text)
                output_text.insert(END, line_text)
                output_text.see(END)
            versions_process.stdout.close()
            versions_process.wait()
            
            # 解析pyenv versions的输出
            installed_versions = []
            for line in versions_output:
                line = line.strip()
                # 跳过空行和错误信息行
                if line and not any(err_msg in line.lower() for err_msg in ['error', '错误', 'failed']):
                    # 移除版本号前面的*（如果存在）和空格
                    if line.startswith('*'):
                        line = line[1:].strip()
                    # 假设版本号是行的第一个部分（直到空格为止）
                    if ' ' in line:
                        version = line.split(' ', 1)[0]
                    else:
                        version = line
                    # 简单验证是否为版本号格式
                    if any(char.isdigit() for char in version) and '.' in version:
                        installed_versions.append(version)
            
            # 如果找到了版本信息，更新文件和下拉框
            if installed_versions:
                if update_installed_versions_file(installed_versions):
                    output_text.insert(END, f"\n{language_pack[current_language]['updated_installed_versions']}\n")
                    # 更新下拉框
                    update_global_params_combobox()
    
    # 检测是否执行了pyenv global命令并成功设置了版本
    if selected_command == 'global' and params.strip() and params != language_pack[current_language]['run_global_first']:
        # 尝试更新全局版本信息
        global global_version
        # 直接使用命令中设置的版本号
        global_version = params.strip()
        save_config()
        # 更新界面显示
        update_version_display()

# Create the main window with ttkbootstrap theme
root = ttk.Window(themename="cosmo")
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

# 创建命令列表，从语言包获取命令描述
def create_commands_list():
    commands_list = []
    # 获取当前语言的命令描述
    descriptions = language_pack[current_language]['command_descriptions']
    # 遍历所有命令，构建命令-描述对
    for cmd in descriptions:
        commands_list.append(f"{cmd} - {descriptions[cmd]}")
    return commands_list

# 初始创建命令列表
commands = create_commands_list()

# 更新命令列表（语言切换时调用）
def update_commands_list():
    global commands
    commands = create_commands_list()
    # 更新命令下拉框
    command_menu['values'] = commands
    # 确保当前选中项有效
    if command_var.get():
        # 尝试保持当前命令选择不变（仅保留命令部分）
        current_cmd = get_command_name(command_var.get())
        for cmd_desc in commands:
            if get_command_name(cmd_desc) == current_cmd:
                command_var.set(cmd_desc)
                break

# 获取命令名称（只提取命令部分，不包括描述）
def get_command_name(command_text):
    # 提取命令部分（第一个空格前的内容）
    if ' - ' in command_text:
        return command_text.split(' - ')[0].strip()
    return command_text.strip()

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
command_menu = ttk.Combobox(commands_frame, textvariable=command_var, values=commands, width=50)
command_menu.pack(side=LEFT, padx=(0, 10))

# 参数变量
params_var = ttk.StringVar(root)

# Create a frame for the parameters input
params_frame = ttk.Frame(root)
params_frame.grid(row=3, column=0, sticky='w', pady=(0, 10), padx=(10, 0))  # Place the frame in the grid, aligned with commands

# 创建参数下拉框（用于install命令）
# 使用简单可靠的方法解决Windows上的焦点问题
params_combobox = ttk.Combobox(params_frame, textvariable=params_var, width=47, state='disabled')

# 搜索过滤函数 - 专注于保持焦点的实时过滤
def on_combobox_search(event):
    # 忽略导航键和特殊按键，只处理实际字符输入
    if event.keysym in ('Left', 'Right', 'Home', 'End', 'Up', 'Down', 'PageUp', 'PageDown', 
                       'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Delete', 'BackSpace',
                       'Return', 'Tab', 'Escape'):
        return
    
    # 获取当前输入内容和光标位置
    search_text = params_combobox.get().lower()
    cursor_pos = params_combobox.index(INSERT)
    
    # 加载所有可用版本
    all_versions = load_available_versions()
    
    # 构建过滤后的选项列表
    filtered_options = ['-l']  # 始终保留'-l'选项
    
    if not all_versions:
        # 如果没有版本信息，添加提示
        if not search_text or language_pack[current_language]['run_l_first'] in search_text:
            filtered_options.append(language_pack[current_language]['run_l_first'])
    else:
        # 过滤匹配的版本
        for version in all_versions:
            if search_text in version.lower():
                filtered_options.append(version)
    
    # 更新下拉框的值，但不自动显示下拉（这是导致焦点问题的主要原因）
    params_combobox['values'] = filtered_options
    
    # 强制保持输入焦点 - 这是关键！
    # 在Windows上，Combobox组件在更新values后有时会失去焦点
    root.after(5, lambda: params_combobox.focus_set())
    # 恢复光标位置
    root.after(10, lambda pos=cursor_pos: params_combobox.icursor(pos))

# 处理用户主动查看下拉的情况
def on_down_arrow(event):
    # 只有当用户明确按向下箭头时才触发下拉显示
    # 这样可以避免在输入过程中自动显示下拉导致的焦点问题
    # 让Combobox正常处理向下箭头事件
    return None

# 绑定输入事件 - 专注于实时过滤和保持焦点
# 使用 <KeyRelease> 事件来实现实时过滤，但不自动显示下拉
params_combobox.bind('<KeyRelease>', on_combobox_search)

# 绑定向下箭头事件，让用户可以主动查看过滤结果
params_combobox.bind('<Down>', on_down_arrow)

# 这种实现方式优先保证：
# 1. 连续输入多个字符时绝对不会失去焦点
# 2. 输入内容实时过滤匹配项
# 3. 用户可以通过点击下拉按钮或按向下箭头主动查看过滤后的结果
# 4. 提供稳定可靠的搜索体验，避免Windows平台上的焦点问题

# Create a label for the parameters input
params_label = ttk.Label(params_frame, text=language_pack[current_language]['params_label'])
params_label.pack(side=LEFT, padx=(0, 5))  # Place the label in the frame

# Create the parameters input box
params_entry = ttk.Entry(params_frame, textvariable=params_var, width=50)
params_entry.pack(side=LEFT)  # Place the input box in the frame

# 加载可用版本的函数
def load_available_versions():
    versions = []
    if os.path.exists(AVAILABLE_VERSIONS_FILE):
        try:
            with open(AVAILABLE_VERSIONS_FILE, 'r', encoding='utf-8') as f:
                versions = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        except Exception as e:
            print(f"Error loading available versions: {e}")
    return versions

# 加载已安装版本的函数
def load_installed_versions():
    versions = []
    if os.path.exists(INSTALLED_VERSIONS_FILE):
        try:
            with open(INSTALLED_VERSIONS_FILE, 'r', encoding='utf-8') as f:
                versions = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        except Exception as e:
            print(f"Error loading installed versions: {e}")
    return versions

# 更新已安装版本文件
def update_installed_versions_file(versions):
    try:
        with open(INSTALLED_VERSIONS_FILE, 'w', encoding='utf-8') as f:
            f.write("# Installed Python versions cache\n")
            for version in versions:
                f.write(f"{version}\n")
        return True
    except Exception as e:
        print(f"Error writing installed versions: {e}")
        return False

# 更新global参数下拉框
def update_global_params_combobox():
    # 加载已安装版本
    versions = load_installed_versions()
    
    # 如果没有已安装版本，显示提示信息但不作为选项
    if not versions:
        # 清除选项
        params_combobox['values'] = []
        # 设置状态为禁用，这样用户不能下拉选择
        params_combobox['state'] = 'disabled'
        # 显示提示信息
        params_var.set(language_pack[current_language]['run_global_first'])
    else:
        # 设置下拉框的值为已安装版本
        params_combobox['values'] = versions
        # 设置状态为只读，用户可以选择但不能编辑
        params_combobox['state'] = 'readonly'
        # 不设置默认值，让用户选择
        params_var.set('')

# 更新install参数下拉框
def update_install_params_combobox():
    # 清除现有的值
    params_combobox['values'] = []
    
    # 首先添加'-l'选项
    options = ['-l']
    
    # 加载可用版本
    versions = load_available_versions()
    
    # 如果没有可用版本，添加提示信息
    if not versions:
        options.append(language_pack[current_language]['run_l_first'])
    else:
        # 添加所有版本
        options.extend(versions)
    
    # 设置下拉框的值
    params_combobox['values'] = options
    
    # 清除参数值，使其默认为空
    params_var.set('')

# 切换参数组件（输入框或下拉框）
def toggle_params_widget(event=None):
    selected_command_text = command_var.get()
    # 使用get_command_name函数提取命令部分
    selected_command = get_command_name(selected_command_text)
    
    if selected_command == 'install':
        # 隐藏输入框，显示下拉框
        params_entry.pack_forget()
        params_combobox.pack(side=LEFT)
        params_combobox['state'] = 'normal'  # 设置为可编辑以支持搜索
        # 更新下拉框内容
        update_install_params_combobox()
    elif selected_command == 'global':
        # 隐藏输入框，显示下拉框
        params_entry.pack_forget()
        params_combobox.pack(side=LEFT)
        # 状态将在update_global_params_combobox中根据是否有已安装版本设置
        # 更新下拉框内容
        update_global_params_combobox()
    else:
        # 隐藏下拉框，显示输入框
        params_combobox.pack_forget()
        params_entry.pack(side=LEFT)
        params_entry['state'] = 'normal'

# 绑定命令选择变更事件
command_menu.bind('<<ComboboxSelected>>', toggle_params_widget)

# 处理install -l命令的结果
def handle_install_list(output_lines):
    versions = []
    # 过滤掉以::开头的信息行，只保留版本信息
    for line in output_lines:
        line = line.strip()
        # 跳过空行和以::开头的行
        if line and not line.startswith('::'):
            versions.append(line)
    
    # 将版本信息写入文件
    try:
        with open(AVAILABLE_VERSIONS_FILE, 'w', encoding='utf-8') as f:
            f.write("# Available Python versions cache\n")
            for version in versions:
                f.write(f"{version}\n")
        # 更新下拉框
        update_install_params_combobox()
        return True
    except Exception as e:
        print(f"Error writing available versions: {e}")
        return False

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
