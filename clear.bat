@echo off
:: ============================================================
::  CleanMyPC.bat - Malware Cleanup + System Junk Cleaner
::  Double-click to run (requires Admin privileges)
:: ============================================================

:: --- Request Admin privileges ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting Administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

title CleanMyPC - Scanning and Cleaning...
color 0A
cls

echo ============================================================
echo   CleanMyPC - Malware Cleanup + System Optimizer
echo   Date: %date% %time%
echo ============================================================
echo.

:: ============================================================
:: PHASE 1: MALWARE ARTIFACT REMOVAL (Akatsuki)
:: ============================================================
echo [PHASE 1] Malware Artifact Removal
echo ------------------------------------------------------------

echo [1/6] Removing suspicious scheduled task...
schtasks /delete /tn "Microsoft\Windows\Wininet\CacheTask" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo       [!] Deleted malicious scheduled task
) else (
    echo       [OK] No malicious scheduled task found
)

echo [2/6] Removing hidden malware directory...
if exist "C:\ProgramData\Windows NT" (
    rd /s /q "C:\ProgramData\Windows NT" >nul 2>&1
    echo       [!] Deleted: C:\ProgramData\Windows NT
) else (
    echo       [OK] Clean - directory not found
)

echo [3/6] Removing debug log...
if exist "%TEMP%\akatsuki_debug.log" (
    del /f /q "%TEMP%\akatsuki_debug.log" >nul 2>&1
    echo       [!] Deleted: akatsuki_debug.log
) else (
    echo       [OK] Clean - no debug log
)

echo [4/6] Killing fake RuntimeBroker process...
powershell -NoProfile -Command "Get-Process | Where-Object { $_.Path -like '*Windows NT*RuntimeBroker*' } | Stop-Process -Force -ErrorAction SilentlyContinue" >nul 2>&1
echo       [OK] Process check complete

echo [5/6] Scanning Registry Run keys for suspicious entries...
powershell -NoProfile -Command ^
  "$paths = @('HKCU:\Software\Microsoft\Windows\CurrentVersion\Run','HKCU:\Software\Microsoft\Windows\CurrentVersion\RunOnce','HKLM:\Software\Microsoft\Windows\CurrentVersion\Run','HKLM:\Software\Microsoft\Windows\CurrentVersion\RunOnce'); $found=$false; foreach($p in $paths){try{$items=Get-ItemProperty $p -ErrorAction SilentlyContinue; $items.PSObject.Properties | Where-Object { $_.Value -like '*Windows NT*RuntimeBroker*' -or $_.Value -like '*akatsuki*' } | ForEach-Object { Write-Host ('      [!] FOUND: {0} => {1}' -f $_.Name,$_.Value); Remove-ItemProperty -Path $p -Name $_.Name -Force -ErrorAction SilentlyContinue; $found=$true }}catch{}}; if(-not $found){Write-Host '      [OK] Registry Run keys are clean'}"

echo [6/6] Checking for suspicious services...
powershell -NoProfile -Command ^
  "$svcs = Get-WmiObject Win32_Service -ErrorAction SilentlyContinue | Where-Object { $_.PathName -like '*Windows NT*RuntimeBroker*' -or $_.PathName -like '*akatsuki*' }; if($svcs){ $svcs | ForEach-Object { Write-Host ('      [!] Removing service: {0}' -f $_.Name); Stop-Service $_.Name -Force -ErrorAction SilentlyContinue; sc.exe delete $_.Name >$null 2>&1 }} else { Write-Host '      [OK] No suspicious services found' }"

echo.

:: ============================================================
:: PHASE 2: TEMP FILES + JUNK CLEANUP
:: ============================================================
echo [PHASE 2] Cleaning Temp Files and Junk
echo ------------------------------------------------------------

echo [1/8] Cleaning User Temp folder...
del /f /s /q "%TEMP%\*" >nul 2>&1
for /d %%D in ("%TEMP%\*") do rd /s /q "%%D" >nul 2>&1
echo       [OK] User Temp cleaned

echo [2/8] Cleaning Windows Temp folder...
del /f /s /q "%SystemRoot%\Temp\*" >nul 2>&1
for /d %%D in ("%SystemRoot%\Temp\*") do rd /s /q "%%D" >nul 2>&1
echo       [OK] Windows Temp cleaned

echo [3/8] Cleaning Prefetch cache...
del /f /s /q "%SystemRoot%\Prefetch\*" >nul 2>&1
echo       [OK] Prefetch cleaned

echo [4/8] Cleaning Windows Update cache...
net stop wuauserv >nul 2>&1
del /f /s /q "%SystemRoot%\SoftwareDistribution\Download\*" >nul 2>&1
net start wuauserv >nul 2>&1
echo       [OK] Windows Update cache cleaned

echo [5/8] Cleaning Thumbnail cache...
del /f /s /q /a:h "%LocalAppData%\Microsoft\Windows\Explorer\thumbcache_*.db" >nul 2>&1
echo       [OK] Thumbnail cache cleaned

echo [6/8] Cleaning Recent files list...
del /f /q "%AppData%\Microsoft\Windows\Recent\*" >nul 2>&1
echo       [OK] Recent files list cleaned

echo [7/8] Cleaning DNS cache...
ipconfig /flushdns >nul 2>&1
echo       [OK] DNS cache flushed

echo [8/8] Emptying Recycle Bin...
powershell -NoProfile -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue" >nul 2>&1
echo       [OK] Recycle Bin emptied

echo.

:: ============================================================
:: PHASE 3: SYSTEM OPTIMIZATION
:: ============================================================
echo [PHASE 3] System Optimization
echo ------------------------------------------------------------

echo [1/4] Cleaning browser caches (Edge, Chrome, Firefox)...

:: Edge
if exist "%LocalAppData%\Microsoft\Edge\User Data\Default\Cache" (
    rd /s /q "%LocalAppData%\Microsoft\Edge\User Data\Default\Cache" >nul 2>&1
)
:: Chrome
if exist "%LocalAppData%\Google\Chrome\User Data\Default\Cache" (
    rd /s /q "%LocalAppData%\Google\Chrome\User Data\Default\Cache" >nul 2>&1
)
:: Firefox
powershell -NoProfile -Command ^
  "Get-ChildItem \"$env:LocalAppData\Mozilla\Firefox\Profiles\" -Directory -ErrorAction SilentlyContinue | ForEach-Object { $cache = Join-Path $_.FullName 'cache2'; if(Test-Path $cache){ Remove-Item $cache -Recurse -Force -ErrorAction SilentlyContinue }}" >nul 2>&1
echo       [OK] Browser caches cleaned

echo [2/4] Cleaning Windows error reports...
del /f /s /q "%LocalAppData%\Microsoft\Windows\WER\*" >nul 2>&1
del /f /s /q "%ProgramData%\Microsoft\Windows\WER\*" >nul 2>&1
echo       [OK] Error reports cleaned

echo [3/4] Cleaning old Windows log files...
del /f /s /q "%SystemRoot%\Logs\CBS\*.log" >nul 2>&1
del /f /s /q "%SystemRoot%\Logs\DISM\*.log" >nul 2>&1
del /f /s /q "%SystemRoot%\*.log" >nul 2>&1
echo       [OK] Old logs cleaned

echo [4/4] Running Disk Cleanup (silent mode)...
cleanmgr /sagerun:1 >nul 2>&1
echo       [OK] Disk Cleanup triggered

echo.

:: ============================================================
:: SUMMARY
:: ============================================================
echo ============================================================
echo   [DONE] All tasks completed!
echo.
echo   - Malware artifacts scanned and removed
echo   - Temp files and junk cleaned
echo   - Browser caches cleared
echo   - System optimized
echo.
echo   TIP: Restart your PC for best results.
echo ============================================================
echo.

pause