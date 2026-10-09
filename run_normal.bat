@echo off
set "PYTHON_EXE=C:\Users\maxdv\AppData\Local\Programs\Python\Python39\python.exe"

echo === RUNNING NORMAL TEST ===
"%PYTHON_EXE%" src/first.py --vfs ./vfs.zip --log ./log_normal.xml --script ./start_normal.txt
echo ===========================
pause