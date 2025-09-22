# Configuración de variables de entorno para ventassur2@unilimpio.com
Write-Host "Configurando variables de entorno para ventassur2@unilimpio.com..." -ForegroundColor Green

$env:IMAP_HOST = "imap.gmail.com"
$env:IMAP_USER = "ventassur2@unilimpio.com"
$env:IMAP_PASS = "hgczxskkszfkxwrj"
$env:IMAP_MAILBOX = "INBOX"
$env:IMAP_IDLE_SECS = "1740"
$env:DEFAULT_CLIENTE = "Roldan"

Write-Host "`nVariables configuradas:" -ForegroundColor Yellow
Write-Host "IMAP_HOST: $env:IMAP_HOST"
Write-Host "IMAP_USER: $env:IMAP_USER"
Write-Host "IMAP_PASS: $env:IMAP_PASS"
Write-Host "IMAP_MAILBOX: $env:IMAP_MAILBOX"
Write-Host "DEFAULT_CLIENTE: $env:DEFAULT_CLIENTE"

Write-Host "`nEjecutando el sistema..." -ForegroundColor Green
py main.py
