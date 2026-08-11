@echo off
setlocal

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="pre-requisites" goto prerequisites
if "%1"=="install" goto install
if "%1"=="run" goto run
if "%1"=="chat" goto chat
if "%1"=="clean" goto clean

echo Unknown target: %1
goto help

:help
echo Available commands:
echo   make.bat install         - Install dependencies
echo   make.bat run             - Run one-shot health check
echo   make.bat chat            - Interactive chat with the agent
echo   make.bat clean           - Remove __pycache__ folders
echo   make.bat pre-requisites  - Install uv
goto end

:prerequisites
powershell -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
goto end

:install
uv sync
goto end

:run
uv run python main.py
goto end

:chat
uv run python main.py --chat
goto end

:clean
for /d /r %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
goto end

:end
endlocal
