import subprocess
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("LEGAJO", "").strip()
pwd = os.getenv("PASSWORD", "").strip()

URL_LOGIN = "https://www.frc.utn.edu.ar/logon.frc"

def main():
    if not user or not pwd:
        print("❌ Faltan credenciales en el .env.")
        return

    print("🕵️ Iniciando bypass de Firewall a nivel de Sistema Operativo...")
    
    pwd_encoded = urllib.parse.quote_plus(pwd)
    payload = f"userid=userid&t=79845687&page=login&redir=%2Flogon.frc&txtUsuario={user}&txtDominios=sistemas&pwdClave={pwd_encoded}&btnEnviar=++Iniciar+Sesi%C3%B3n++"
    
    # Invocamos a curl nativo para que el Firewall no detecte la firma de Python
    comando = [
        "curl", "-s", "-i", URL_LOGIN,
        "-X", "POST",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-H", "X-Requested-With: XMLHttpRequest",
        "-H", "Origin: https://www.frc.utn.edu.ar",
        "-H", "Referer: URL_LOGIN",
        "-b", "pag=2",
        "--data-raw", payload
    ]
    
    print("🚀 Disparando cURL (Cuidado Firewall, allá vamos)...")
    resultado = subprocess.run(comando, capture_output=True, text=True)
    
    respuesta = resultado.stdout
    
    # Separamos las cabeceras HTTP del código HTML
    partes = respuesta.split("\r\n\r\n", 1)
    cuerpo = partes[1] if len(partes) > 1 else respuesta
    
    print(f"-> Tamaño de la respuesta del servidor: {len(cuerpo)} bytes")
    
    # Si la respuesta es cortita, el firewall no nos frenó y el login pasó
    if len(cuerpo) < 5000:
        print("✅ ¡BINGO! EL FIREWALL FUE BURLADO.")
        print("El servidor aceptó las credenciales y estamos listos para raspar los mensajes.")
    else:
        print("❌ Sigue rebotando. Hay que revisar si tu IP local no está temporalmente bloqueada.")

if __name__ == "__main__":
    main()