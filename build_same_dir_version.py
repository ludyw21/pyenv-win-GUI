import os
import subprocess
import sys

print("Starting to build pyenv-win-GUI (same directory configuration)...")

# 确保依赖已安装
print("Installing dependencies...")
# 使用当前Python解释器的pip模块，避免找不到pip命令的问题
subprocess.run([sys.executable, "-m", "pip", "install", "ttkbootstrap", "requests", "pyinstaller", "-q"])

# 使用主程序文件进行打包，直接指定输出文件名
print("Building executable...")
result = subprocess.run([
    "pyinstaller", 
    "--onefile", 
    "--windowed", 
    "--add-data", "language_pack.py;." ,
    "--add-data", "assets;assets", 
    "--name", "pyenv-win-GUI",  # 直接指定输出文件名
    "pyenv-win-GUI.py"
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# 检查打包是否成功
dist_dir = os.path.join(os.getcwd(), "dist")
final_exe_path = os.path.join(dist_dir, "pyenv-win-GUI.exe")

if os.path.exists(final_exe_path):
    print(f"Build successful! Executable: {final_exe_path}")
    print("\n配置文件现在将保存在与可执行文件相同的目录中")
else:
    print("Build failed! Please check error messages above.")
    exit(1)

print("Build completed successfully!")