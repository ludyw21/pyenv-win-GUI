# 修复pyenv-win-GUI.py中与PyInstaller打包相关的问题，让文件存储在与exe同目录
import os

# 读取原始文件内容
with open('pyenv-win-GUI.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 修复subprocess调用，添加creationflags=subprocess.CREATE_NO_WINDOW参数
# 查找所有subprocess.check_output调用并添加参数
content = content.replace(
    "subprocess.check_output(['powershell', '-Command', 'pyenv --version'], stderr=subprocess.STDOUT)",
    "subprocess.check_output(['powershell', '-Command', 'pyenv --version'], stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)"
)

content = content.replace(
    "subprocess.check_output(['powershell', '-Command', 'pyenv global'], stderr=subprocess.STDOUT)",
    "subprocess.check_output(['powershell', '-Command', 'pyenv global'], stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)"
)

content = content.replace(
    "subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)",
    "subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)"
)

content = content.replace(
    "process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)",
    "process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)"
)

# 2. 修复文件路径处理，使用与exe文件相同的目录存储配置和缓存文件
# 替换文件路径定义部分
file_paths_code = '''# 配置文件路径 - 使用与可执行文件相同的目录存储文件
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
INSTALLED_VERSIONS_FILE = os.path.join(app_dir, 'installed_versions.txt')'''

# 替换原始的文件路径定义
content = content.replace(
    '''# 配置文件路径
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
# 可用版本缓存文件路径
AVAILABLE_VERSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'available_versions.txt')
# 已安装版本缓存文件路径
INSTALLED_VERSIONS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'installed_versions.txt')''',
    file_paths_code
)

# 保存修复后的文件
with open('pyenv-win-GUI_fixed_same_dir.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("修复完成！修复后的文件已保存为pyenv-win-GUI_fixed_same_dir.py")
print("\n修复的内容：")
print("1. 为所有subprocess调用添加了creationflags=subprocess.CREATE_NO_WINDOW参数，防止终端窗口弹出")
print("2. 修改了配置文件和缓存文件的存储路径，现在它们将保存在与可执行文件相同的目录中")
print("\n请使用修复后的文件进行重新打包")