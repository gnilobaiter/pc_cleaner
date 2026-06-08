@echo off

if not exist ".venv" (
    echo Creating venv...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Installing requirements...
python -m pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt

echo Building EXE...
pyinstaller --name PC_CLEANER ^
    --noconfirm ^
    --clean ^
    --onefile ^
    --uac-admin ^
    --collect-submodules colorama ^
    main.py

echo Build ready! Press enter to leave builder
pause