from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import requests
import sqlite3
import os
import re
import hashlib
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN ---
TELEGRAM_TOKEN = os.getenv("API_KEY")
CHAT_ID = os.getenv("CHAT_ID")
USER = os.getenv("LEGAJO", "").strip()
PWD = os.getenv("PASSWORD", "").strip()

URL_LOGIN = "https://www.frc.utn.edu.ar/logon.frc"
URL_DASHBOARD_A3 = "https://www.frc.utn.edu.ar/academico3/defaultreduced.frc"
URL_NOTAS = "https://www.frc.utn.edu.ar/academico3/mensajes.frc?tipo=NOTAS"

def enviar_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    mensaje_con_firma = f"{mensaje}\n\n🤖 <i>Desarrollado por Pato (y un poco bastante de IA)</i>"
    data = {"chat_id": CHAT_ID, "text": mensaje_con_firma, "parse_mode": "HTML"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

def inicializar_db():
    conn = sqlite3.connect('avisos_utn.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS estado (id INTEGER PRIMARY KEY, cantidad_mensajes INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS avisos_enviados (id_aviso TEXT PRIMARY KEY)''')
    cursor.execute("INSERT OR IGNORE INTO estado (id, cantidad_mensajes) VALUES (1, 0)")
    conn.commit()
    return conn

def generar_id_unico(fecha, curso, profesor, texto):
    string_base = f"{fecha}-{curso}-{profesor}-{texto[:50]}"
    return hashlib.md5(string_base.encode('utf-8')).hexdigest()

def main():
    if not USER or not PWD:
        print("❌ Faltan credenciales en el .env.")
        return

    conn = inicializar_db()
    cursor = conn.cursor()

    print("🚀 Arrancando el motor de Playwright...")
    
    with sync_playwright() as p:
        # ATENCIÓN: Cuando lo subas a tu servidor, cambiá headless=False a headless=True
        browser = p.chromium.launch(headless=True, slow_mo=50) 
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/146.0.0.0"
        )
        page = context.new_page()

        print("1. Entrando a la web de la UTN y logueando...")
        page.goto(URL_LOGIN)
        page.fill('input[name="txtUsuario"]', USER)
        page.fill('input[name="pwdClave"]', PWD)
        page.select_option('select[name="txtDominios"]', 'sistemas')
        page.check('input[name="chk2"]') # Checkbox Autogestión
        
        page.click('input[name="btnEnviar"]')
        page.wait_for_load_state("networkidle")

        print("2. Saltando a Autogestión 3...")
        page.goto(URL_DASHBOARD_A3)

        try:
            page.wait_for_selector("text=MIS MENSAJES", timeout=15000)
            texto_pagina = page.inner_text("body")
            busqueda = re.search(r'MIS MENSAJES\s*\(*(\d+)\)*', texto_pagina, re.IGNORECASE)
            
            if busqueda:
                cantidad_actual = int(busqueda.group(1))
                print(f"✅ ¡Adentro! Mensajes detectados: {cantidad_actual}")
                
                cursor.execute("SELECT cantidad_mensajes FROM estado WHERE id=1")
                cantidad_guardada = cursor.fetchone()[0]
                
                # TIP: Si querés que te lleguen los 11 mensajes a tu Telegram AHORA MISMO para probar,
                # cambiá el ">" por ">=" en la siguiente línea.
                if cantidad_actual > cantidad_guardada: 
                    print("¡Nuevos mensajes! Haciendo clic en la pestaña 'NOTAS'...")
                    
                    # 1. Hacemos clic exacto en la pestaña que dice "NOTAS"
                    page.locator("text=NOTAS").click()
                    
                    print("Esperando que el servidor cargue los avisos en el iframe (puede tardar)...")
                    
                    # 2. Le damos extra de gracia para que termine de dibujar todo el texto
                    page.wait_for_timeout(12000) 
                    
                    # Buscamos el iframe con las notas
                    frame_notas = None
                    for f in page.frames:
                        if "mensajes.frc?tipo=NOTAS" in f.url:
                            frame_notas = f
                            break
                    
                    if not frame_notas:
                        print("⚠️ No se encontró el iframe de NOTAS, intentando con page...")
                        html_notas = page.content()
                    else:
                        print("✅ Iframe de NOTAS encontrado.")
                        html_notas = frame_notas.content()

                    soup_notas = BeautifulSoup(html_notas, 'html.parser')
                    
                    flechas = soup_notas.find_all('strong', class_='dikdor')
                    
                    for flecha in reversed(flechas):
                        strongs = flecha.find_next_siblings('strong', limit=3)
                        
                        if len(strongs) >= 2:
                            curso = strongs[0].get_text(strip=True)
                            fecha = strongs[1].get_text(strip=True)
                            profesor = strongs[2].get_text(strip=True) if len(strongs) >= 3 else "Sistema"
                            
                            bq = flecha.find_next_sibling('blockquote')
                            texto_mensaje = bq.get_text(strip=True) if bq else "Sin texto"
                            
                            id_aviso = generar_id_unico(fecha, curso, profesor, texto_mensaje)
                            
                            cursor.execute("SELECT * FROM avisos_enviados WHERE id_aviso=?", (id_aviso,))
                            if not cursor.fetchone():
                                if curso:
                                    msj_tg = f"🚨 <b>NUEVO AVISO: {curso}</b>\n👨‍🏫 <b>Prof:</b> {profesor}\n📅 <b>Fecha:</b> {fecha}\n\n💬 <i>{texto_mensaje}</i>"
                                else:
                                    msj_tg = f"⚙️ <b>AVISO DEL SISTEMA</b>\n📅 <b>Fecha:</b> {fecha}\n\n💬 <i>{texto_mensaje}</i>"
                                    
                                enviar_telegram(msj_tg)
                                print(f"-> Enviado a Telegram: Aviso de {curso if curso else 'Sistema'}")
                                
                                cursor.execute("INSERT INTO avisos_enviados VALUES (?)", (id_aviso,))
                    
                    cursor.execute("UPDATE estado SET cantidad_mensajes=? WHERE id=1", (cantidad_actual,))
                    conn.commit()
                    print("Base de datos actualizada.")
                else:
                    print("No hay mensajes nuevos. Todo al día.")
            else:
                print("⚠️ No se pudo leer el número de mensajes.")
                
        except Exception as e:
            print("❌ Hubo un error de lectura en el Dashboard.")
            print(e)

        print("Cerrando navegador...")
        browser.close()
    conn.close()

if __name__ == "__main__":
    main()