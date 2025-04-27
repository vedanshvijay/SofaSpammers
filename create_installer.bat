@echo off
echo Creating OfficeIPMess Installer...
echo.

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate

REM Install required packages
pip install -r requirements.txt
pip install cx_Freeze

REM Create the executable
python setup.py build

echo.
echo Installer created successfully!
echo You can find the executable in the build folder.
pause 