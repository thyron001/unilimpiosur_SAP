# Script para ejecutar el sistema con ventassur2@unilimpio.com
Write-Host "🔧 Configurando variables de entorno..." -ForegroundColor Green

# Configurar variables de entorno en el proceso actual
$env:IMAP_HOST = "imap.gmail.com"
$env:IMAP_USER = "ventassur2@unilimpio.com"
$env:IMAP_PASS = "hgczxskkszfkxwrj"
$env:IMAP_MAILBOX = "INBOX"
$env:IMAP_IDLE_SECS = "1740"
$env:DEFAULT_CLIENTE = "Roldan"

Write-Host "✅ Variables configuradas:" -ForegroundColor Green
Write-Host "   📧 IMAP_USER: $env:IMAP_USER" -ForegroundColor Cyan
Write-Host "   🌐 IMAP_HOST: $env:IMAP_HOST" -ForegroundColor Cyan

Write-Host "`n🚀 Iniciando sistema..." -ForegroundColor Yellow

# Ejecutar Python con las variables heredadas
Start-Process -FilePath "py" -ArgumentList "main.py" -NoNewWindow -Wait
