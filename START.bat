@echo off
setlocal enabledelayedexpansion

echo.
echo ==================
echo    ChatBot RPG
echo ==================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo [INFO] Python found: 
python --version

pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available
    echo Please ensure pip is installed with Python
    echo.
    pause
    exit /b 1
)

echo [INFO] pip found:
pip --version

set "setup_complete=false"
if exist "config.json" (
    findstr /C:"setup_complete" config.json >nul 2>&1
    if not errorlevel 1 (
        echo [INFO] Setup already complete, checking dependencies...
        set "all_good=true"
        for %%p in (PyQt5 pygame markdown2 beautifulsoup4 requests numpy pyfiglet opencv-python google-genai) do (
            python -c "import %%p" >nul 2>&1
            if errorlevel 1 (
                set "all_good=false"
                echo [WARNING] %%p is missing, will reinstall...
            )
        )
        if "!all_good!"=="true" (
            echo [INFO] All dependencies verified, skipping installation...
            goto :launch
        ) else (
            echo [INFO] Some packages missing, reinstalling...
        )
    ) else (
        echo [INFO] First time setup - installing required packages...
    )
) else (
    echo [INFO] First time setup - installing required packages...
)

pip install PyQt5 pygame markdown2 beautifulsoup4 requests numpy pyfiglet opencv-python openai tiktoken google-genai

if exist "config.json" (
    echo [INFO] Setup complete! Future launches will be faster.
) else (
    echo [INFO] Creating config.json and marking setup complete...
)

:launch
if not exist "src\chatBotRPG.py" (
    echo [ERROR] Main application file src\chatBotRPG.py not found
    echo Please ensure the application files are in the correct location
    echo.
    pause
    exit /b 1
)

if not exist "config.json" (
    echo [WARNING] config.json not found
    echo Creating default config.json...
    echo {> config.json
    echo   "openrouter_api_key": "your_api_key_here",>> config.json
    echo   "openrouter_base_url": "https://openrouter.ai/api/v1",>> config.json
    echo   "default_model": "google/gemini-2.5-flash-lite-preview-06-17",>> config.json
    echo   "default_cot_model": "google/gemini-2.5-flash-lite-preview-06-17",>> config.json
    echo   "setup_complete": true>> config.json
    echo }>> config.json
    echo [INFO] Default config.json created
    echo [INFO] Please edit config.json to add your OpenRouter API key
) else (
    findstr /C:"setup_complete" config.json >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Adding setup status to config.json...
        powershell -Command "$content = Get-Content config.json -Raw; if ($content -notmatch '\"setup_complete\"') { $content = $content -replace '}$', ',\n  \"setup_complete\": true\n}'; Set-Content config.json $content -NoNewline}"
    )
)

if not exist "sounds" (
    echo [WARNING] sounds directory not found
    echo Creating sounds directory...
    mkdir sounds
)

echo [INFO] Launching ChatBotRPG...
start /min pythonw src\chatBotRPG.py
timeout /t 2 /nobreak >nul
