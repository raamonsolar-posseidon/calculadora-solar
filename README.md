# 🌍 Calculadora Solar Profesional - Guía de Deploy en Railway

## 📋 Requisitos previos

1. Cuenta en GitHub (https://github.com)
2. Cuenta en Railway (https://railway.app)

## 🚀 Pasos para desplegar

### 1. Crear repositorio en GitHub

```bash
# En tu computadora, abre terminal/PowerShell y ejecuta:
git init
git add .
git commit -m "Initial commit"
```

Luego en GitHub:
- Ve a https://github.com/new
- Crea un nuevo repositorio llamado "calculadora-solar"
- Copia el URL

### 2. Subir código a GitHub

```bash
git remote add origin https://github.com/TU_USUARIO/calculadora-solar.git
git branch -M main
git push -u origin main
```

### 3. Conectar con Railway

1. Ve a https://railway.app/dashboard
2. Haz clic en "+ New Project"
3. Selecciona "Deploy from GitHub"
4. Autoriza Railway con tu cuenta GitHub
5. Selecciona el repositorio "calculadora-solar"
6. Railway detectará automáticamente que es una app Node.js
7. Espera a que se compile (2-5 minutos)
8. ¡Listo! Tu aplicación estará en vivo

### 4. Acceder a la aplicación

Una vez deployada, Railway te dará una URL como:
```
https://calculadora-solar-production-xxxx.up.railway.app
```

## 📱 Características de la versión web

✅ **Responsive Design**
- Optimizada para desktop (monitor 1920px+)
- Optimizada para tablet (768px-1024px)
- Optimizada para móvil (320px-480px)

✅ **Rendimiento**
- Carga rápida (< 2 segundos)
- Sin dependencias externas pesadas
- Funciona offline después de cargar

✅ **Compatibilidad**
- Chrome, Firefox, Safari, Edge
- iOS, Android
- Navegadores antiguos (IE 11+)

## 🔄 Actualizar después de cambios

```bash
git add .
git commit -m "Descripción de cambios"
git push origin main
```

Railway se actualizará automáticamente en ~1-2 minutos.

## 🛠️ Solucionar problemas

### La app no carga
- Verifica que todos los archivos estén en `public/`
- Revisa los logs en Railway: Dashboard → Logs

### Canvas no funciona en móvil
- Actualiza el navegador
- Cierra otras pestañas/apps

### Las imágenes se ven pixeladas
- Aumenta el zoom del navegador
- Usa una imagen de mayor resolución

## 📊 Estructura de archivos

```
calculadora-solar/
├── server.js          # Servidor Express
├── package.json       # Dependencias
├── Procfile           # Configuración Railway
├── .gitignore         # Archivos a no subir
└── public/
    └── index.html     # Aplicación web
```

## 🌐 Variables de entorno (opcional)

Si necesitas configurar cosas dinámicamente, usa:

```javascript
const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || 'http://localhost:3000';
```

## 💡 Tips

- **Dominio personalizado**: En Railway → Project Settings → Domains
- **Historial de deployments**: En Railway → Deployments
- **Logs en tiempo real**: En Railway → Logs → Live
- **Redeploy manual**: En Railway → Deployments → Redeploy

## 📞 Soporte

- Railway Docs: https://docs.railway.app
- GitHub Pages alternative: https://pages.github.com (archivos estáticos)
- Vercel alternative: https://vercel.com (también soporta Node.js)

---

**¡Tu Calculadora Solar está ahora en la nube! 🌞**
