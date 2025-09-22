# Script para configurar SOLO las variables de entorno del correo ventassur2@unilimpio.com
# Sin ejecutar el sistema automáticamente

Write-Host "Configurando variables de entorno para ventassur2@unilimpio.com..." -ForegroundColor Yellow

# Configurar variables de entorno para IMAP
$env:IMAP_HOST = "imap.gmail.com"
$env:IMAP_USER = "ventassur2@unilimpio.com"
$env:IMAP_PASS = "hgczxskkszfkxwrj"
$env:IMAP_MAILBOX = "INBOX"
$env:IMAP_IDLE_SECS = "1740"
$env:DEFAULT_CLIENTE = "Roldan"

Write-Host "`nVariables de entorno configuradas:" -ForegroundColor Green
Write-Host "IMAP_HOST: $env:IMAP_HOST" -ForegroundColor Cyan
Write-Host "IMAP_USER: $env:IMAP_USER" -ForegroundColor Cyan
Write-Host "IMAP_MAILBOX: $env:IMAP_MAILBOX" -ForegroundColor Cyan
Write-Host "IMAP_IDLE_SECS: $env:IMAP_IDLE_SECS" -ForegroundColor Cyan
Write-Host "DEFAULT_CLIENTE: $env:DEFAULT_CLIENTE" -ForegroundColor Cyan

# Verificar que IMAP_PASS esté configurado (sin mostrar el valor)
if ($env:IMAP_PASS) {
    Write-Host "IMAP_PASS: Configurado correctamente" -ForegroundColor Green
} else {
    Write-Host "IMAP_PASS: No configurado" -ForegroundColor Red
}

Write-Host "`nEjecutando test de variables..." -ForegroundColor Yellow
py test_variables.py