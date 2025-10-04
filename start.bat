@echo off
:: Make sure the current directory is the same
:: as where the script is located.
cd /d %~dp0

call E:\AI_liuyao\.venv\Scripts\activate.bat
python main.py

pause