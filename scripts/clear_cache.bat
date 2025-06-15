@echo off
chcp 65001 >nul
echo Clearing Python cache files...

:: Delete all __pycache__ folders
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo Deleting: %%d
        rmdir /s /q "%%d"
    )
)

:: Delete all .pyc files
for /r . %%f in (*.pyc) do (
    if exist "%%f" (
        echo Deleting: %%f
        del /q "%%f"
    )
)

:: Delete all .pyo files
for /r . %%f in (*.pyo) do (
    if exist "%%f" (
        echo Deleting: %%f
        del /q "%%f"
    )
)

:: Delete log files
for /r . %%f in (*.log) do (
    if exist "%%f" (
        echo Deleting: %%f
        del /q "%%f"
    )
)

:: Delete PyInstaller spec files
for /r . %%f in (*.spec) do (
    if exist "%%f" (
        echo Deleting: %%f
        del /q "%%f"
    )
)

echo Cache cleanup completed!
pause