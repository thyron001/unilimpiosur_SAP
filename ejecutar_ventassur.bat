@echo off
echo ==========================================
echo   CONFIGURANDO VENTASSUR2@UNILIMPIO.COM
echo ==========================================

set IMAP_HOST=imap.gmail.com
set IMAP_USER=ventassur2@unilimpio.com
set IMAP_PASS=hgczxskkszfkxwrj
set IMAP_MAILBOX=INBOX
set IMAP_IDLE_SECS=1740
set DEFAULT_CLIENTE=Roldan

echo Variables configuradas:
echo IMAP_USER=%IMAP_USER%
echo IMAP_HOST=%IMAP_HOST%
echo.

echo Ejecutando sistema...
py main.py

pause
