@echo off
set "PYTHON_EXE=C:\Users\maxdv\AppData\Local\Programs\Python\Python39\python.exe"

echo === RUNNING HIGH TEST ===
"%PYTHON_EXE%" src/first.py --vfs ./vfs_deep.xml --log ./log_deep.xml --script ./start_deep.txt
echo =========================
pause