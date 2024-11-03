@echo off
cd /d "%~dp0"

REM 仮想環境を有効化 (仮想環境が venv ディレクトリにある場合)
call myenv\Scripts\activate

REM Pythonスクリプトを実行
python tennis_book.py

REM スクリプト終了後のメッセージ表示
echo.
echo Pythonスクリプトが完了しました。
pause
