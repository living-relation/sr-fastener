@echo off
rem Fast-forward only pull of this clone. One repo; path-independent.
cd /d "%~dp0"
echo.
echo Pulling %CD% ...
echo.
git pull --ff-only
echo.
echo Restart the add-in to load new code: Shift+S, Add-Ins, Stop then Run (or restart Fusion).
echo.
pause
