@echo off
setlocal

cd /d D:\EnglishLearning
if errorlevel 1 (
    echo Failed to enter D:\EnglishLearning
    pause
    exit /b 1
)

echo Updating local repository...
git pull
if errorlevel 1 (
    echo Git pull failed. Starting the local app with current files...
) else (
    echo Git pull succeeded.
)

echo Starting local web app...
start "EnglishLearning Server" cmd /k "cd /d D:\EnglishLearning && uv run python -m src.web_entrypoint"

timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8031

echo Browser opened at http://127.0.0.1:8031
pause
