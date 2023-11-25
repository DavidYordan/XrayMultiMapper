@echo off
echo Checking for existing instances of v2ray.exe...
tasklist /FI "IMAGENAME eq v2ray.exe" 2>NUL | find /I /N "v2ray.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Found running v2ray.exe, terminating...
    taskkill /F /IM v2ray.exe
)

echo Checking for existing instances of xray.exe...
tasklist /FI "IMAGENAME eq xray.exe" 2>NUL | find /I /N "xray.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Found running xray.exe, terminating...
    taskkill /F /IM xray.exe
)

echo Starting v2ray...
cd v2ray
start v2ray.exe run --config config.json

echo Done.