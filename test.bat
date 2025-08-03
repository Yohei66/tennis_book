@echo off
REM =========================================
REM  run_tennis_book_debug.bat
REM =========================================

cd /d "%~dp0"
echo [STEP1] カレントフォルダを %CD% に変更しました。
echo.

REM ---- 仮想環境を探す ----------------------
set "VENV_DIR=%~dp0myenv"
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [ERROR] 仮想環境 "%VENV_DIR%" が見つかりません。
    pause
    goto :eof
)

echo [STEP2] 仮想環境が見つかりました: "%VENV_DIR%"
echo.

REM ---- 仮想環境を有効化 --------------------
echo [STEP3] activate.bat を呼び出します…
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] activate.bat の実行に失敗しました (ERRORLEVEL=%ERRORLEVEL%)
    pause
    goto :eof
)
echo [STEP3] 仮想環境を有効化しました。
echo  python コマンドの場所: %~$PATH:python%
echo  python --version: 
python --version
echo.

REM ---- Python スクリプトを実行 -------------
echo [STEP4] tennis_book.py を実行します…
"%VENV_DIR%\Scripts\python.exe" -u "%~dp0tennis_book.py"
echo [STEP4] Python 終了コード: %ERRORLEVEL%
echo.

echo [STEP5] Python スクリプトが完了しました。
pause
