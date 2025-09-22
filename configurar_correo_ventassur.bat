@echo off
echo Configurando variables de entorno para ventassur2@unilimpio.com...

set IMAP_HOST=imap.gmail.com
set IMAP_USER=ventassur2@unilimpio.com
set IMAP_PASS=hgczxskkszfkxwrj
set IMAP_MAILBOX=INBOX
set IMAP_IDLE_SECS=1740
set DEFAULT_CLIENTE=Roldan

echo Variables configuradas:
echo IMAP_HOST=%IMAP_HOST%
echo IMAP_USER=%IMAP_USER%
echo IMAP_PASS=%IMAP_PASS%
echo IMAP_MAILBOX=%IMAP_MAILBOX%
echo DEFAULT_CLIENTE=%DEFAULT_CLIENTE%

echo.
echo Ejecutando el sistema...
py main.py
