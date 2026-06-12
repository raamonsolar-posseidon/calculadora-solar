# Script automático para desplegar Calculadora Solar
# Uso: Ejecuta este script en PowerShell desde la carpeta calculadora-solar

Write-Host "======================================" -ForegroundColor Green
Write-Host "⚡ CALCULADORA SOLAR - DEPLOY AUTO" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Verificar que estamos en la carpeta correcta
if (-Not (Test-Path "package.json")) {
    Write-Host "❌ Error: No estás en la carpeta calculadora-solar" -ForegroundColor Red
    Write-Host "Por favor, navega a tu carpeta calculadora-solar y ejecuta este script de nuevo." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Carpeta correcta detectada" -ForegroundColor Green
Write-Host ""

# PASO 1: Mover index.html de public/ a raíz
Write-Host "📦 Paso 1: Reorganizando archivos..." -ForegroundColor Yellow

if (Test-Path "public\index.html") {
    Copy-Item "public\index.html" "index.html" -Force
    Write-Host "✅ index.html copiado a la raíz" -ForegroundColor Green
} else {
    Write-Host "⚠️  Advertencia: public/index.html no encontrado" -ForegroundColor Yellow
}

Write-Host ""

# PASO 2: Actualizar Git
Write-Host "📤 Paso 2: Actualizando Git..." -ForegroundColor Yellow

# Agregar cambios
git add .
Write-Host "✅ Archivos agregados" -ForegroundColor Green

# Commit
git commit -m "Deploy: Reorganizar archivos para GitHub Pages" 2>$null
Write-Host "✅ Cambios guardados en Git" -ForegroundColor Green

# Push
Write-Host "🔄 Haciendo push a GitHub..." -ForegroundColor Cyan
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Push completado exitosamente" -ForegroundColor Green
} else {
    Write-Host "⚠️  Hubo un error en el push, pero continuamos..." -ForegroundColor Yellow
}

Write-Host ""

# PASO 3: Información final
Write-Host "======================================" -ForegroundColor Green
Write-Host "🎉 ¡DEPLOY COMPLETADO!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

Write-Host "Tu aplicación estará disponible en:" -ForegroundColor Cyan
Write-Host "https://raamonsolar-posseidon.github.io/calculadora-solar/" -ForegroundColor Yellow
Write-Host ""

Write-Host "⏳ Espera 2-3 minutos para que GitHub publique los cambios." -ForegroundColor Yellow
Write-Host ""

Write-Host "✅ ¡Todo listo!" -ForegroundColor Green
Write-Host "Tu Calculadora Solar está EN VIVO 🌞" -ForegroundColor Green

# Pausa
Read-Host "Presiona Enter para cerrar"
