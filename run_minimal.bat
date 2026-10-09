@echo off
set "PYTHON_EXE=C:\Users\maxdv\AppData\Local\Programs\Python\Python39\python.exe"

echo === RUNNING MINIMAL TEST ===
"%PYTHON_EXE%" src/first.py --vfs ./vfs.zip --log ./log_minimal.xml --script ./start_minimal.txt
echo ============================
pause