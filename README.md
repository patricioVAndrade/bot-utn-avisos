# Bot Avisos UTN FRC 🤖🎓

Un bot automatizado que revisa regularmente la plataforma de la UTN FRC (Universidad Tecnológica Nacional, Facultad Regional Córdoba) para buscar nuevos avisos, notas o mensajes, y te notifica directamente vía **Telegram**.

## 🚀 Requisitos Previos

Asegúrate de tener instalado [Python 3.x](https://www.python.org/downloads/) en tu sistema.

El bot utiliza algunas librerías externas que deberás instalar:
- `playwright` (para automatizar el navegador y saltar protecciones)
- `beautifulsoup4` (para extraer datos del HTML)
- `requests` (para enviar las peticiones a la API de Telegram)
- `python-dotenv` (para manejar las variables de entorno de forma segura)

## ⚙️ Configuración del Entorno

1. Clona el repositorio a tu máquina o servidor.
2. Crea un archivo `.env` en la raíz del proyecto (junto a `avisos_utn.py`) con la siguiente estructura:

```env
API_KEY=tu_token_del_bot_de_telegram
CHAT_ID=tu_id_de_chat_de_telegram
LEGAJO=tu_legajo_utn
PASSWORD=tu_contraseña_del_sistema_academico
```

---

## 💻 Opción 1: Ejecución en un Servidor Tradicional (VPS / Local)

Ideal si tienes una máquina corriendo 24/7 (como una Raspberry Pi, un servidor VPS en DigitalOcean, AWS EC2, etc.).

### Paso a paso:

1. **Crear y activar un entorno virtual (Recomendado):**
   ```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En Linux/Mac:
   source venv/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install playwright beautifulsoup4 requests python-dotenv
   ```

3. **Instalar los navegadores de Playwright:**
   ```bash
   playwright install chromium
   ```

4. **Ejecutar el bot manualmentente:**
   ```bash
   python avisos_utn.py
   ```

5. **Automatización con Cron:**
   Para que el script se ejecute automáticamente cada cierto tiempo (ej. cada hora), añade una regla a tu `crontab` en Linux:
   ```bash
   crontab -e
   ```
   Añade esta línea (ajustando la ruta a tu proyecto):
   ```bash
   0 * * * * cd /ruta/absoluta/a/botAvisos && /ruta/absoluta/a/botAvisos/venv/bin/python avisos_utn.py
   ```

---

## ⚡ Opción 2: Ejecución en Modo Serverless / Cloud Functions

Esta opción es ideal si no quieres mantener un servidor encendido y prefieres usar servicios que cobran por ejecución (AWS Lambda, Google Cloud Functions, GitHub Actions).

> **⚠️ Importante sobre el estado:**
> Este script utiliza una base de datos local SQLite (`avisos_utn.db`) y un archivo `cookies_utn.txt` para mantener el estado (saber qué avisos ya envió y no repetir). Los entornos Serverless **son efímeros**, lo que significa que después de cada ejecución borran los archivos temporales.

Para que esto funcione en modo Serverless, te recomendamos uno de estos dos enfoques:

### Alternativa A: Usar GitHub Actions (Recomendado y Gratis)

Puedes configurar un workflow que corra cada hora, ejecute el script y haga _commit_ de vuelta del archivo SQLite (`avisos_utn.db`) para guardar qué avisos ya se mandaron.

1. Añade tus variables del `.env` como **Secrets** en tu repositorio de GitHub (`Settings` > `Secrets and variables` > `Actions`).
2. Crea un archivo `.github/workflows/bot.yml`:

```yaml
name: Ejecutar Bot UTN

on:
  schedule:
    - cron: '0 * * * *' # Corre cada hora
  workflow_dispatch: # Permite ejecutarlo manualmente

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Instalar dependencias
        run: |
          pip install playwright beautifulsoup4 requests python-dotenv
          playwright install chromium
          
      - name: Ejecutar el script
        env:
          API_KEY: ${{ secrets.API_KEY }}
          CHAT_ID: ${{ secrets.CHAT_ID }}
          LEGAJO: ${{ secrets.LEGAJO }}
          PASSWORD: ${{ secrets.PASSWORD }}
        run: python avisos_utn.py
        
      - name: Commitear base de datos para persistir el estado (Opcional)
        run: |
          git config --global user.name "BotAvisos Actions"
          git config --global user.email "bot@actions.com"
          git add avisos_utn.db cookies_utn.txt
          git commit -m "Actualizando estado de la base de datos" || exit 0
          git push
```

### Alternativa B: AWS Lambda / Google Cloud / Vercel
Para correrlo en verdaderos Serverless como AWS Lambda o Cloud Functions:
1. Necesitarás cambiar el código de `avisos_utn.py` para usar una base de datos remota (como [Supabase](https://supabase.com/), [Firebase](https://firebase.google.com/) o AWS DynamoDB) en lugar del archivo local SQLite (`avisos_utn.db`), o guardar el `.db` en un Bucket S3 al finalizar.
2. Deberás incluir Chromium empaquetado (como `playwright-aws-lambda`) ya que los entornos serverless tienen límites estrictos de tamaño.
3. Se invoca usando CloudWatch Events para ejecutarlo periódicamente.

## 🤝 Contribuciones
Si tienes alguna mejora para el scraper, pull requests son bienvenidos!
