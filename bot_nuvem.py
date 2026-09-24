import os
import requests
import time
from datetime import datetime

# As chaves são lidas de forma segura diretamente da nuvem do Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def falar_com_gemini(texto_usuario):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Responda de forma concisa, comercial e útil em português para um assistente de dropshipping: {texto_usuario}"}
                ]
            }
        ]
    }
    
    # Sistema robusto com até 5 tentativas e pausa progressiva para contornar picos de tráfego (503)
    for tentativa in range(1, 6):
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            elif resp.status_code == 503:
                time.sleep(tentativa * 2)
                continue
            else:
                return f"⚠️ Erro temporário na API (Código {resp.status_code})."
        except Exception:
            time.sleep(3)
            
    return "⚠️ Sistema a operar com alta carga. Por favor, repita a mensagem."

def iniciar_bot():
    print("🤖 Bot de Dropshipping iniciado na nuvem...")
    offset = 0
    while True:
        try:
            url_updates = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=20"
            resp = requests.get(url_updates, timeout=25).json()
            
            if resp.get("ok"):
                for resultado in resp.get("result", []):
                    offset = resultado["update_id"] + 1
                    if "message" in resultado and "text" in resultado["message"]:
                        chat_id = resultado["message"]["chat"]["id"]
                        texto_usuario = resultado["message"]["text"].strip()
                        
                        texto_lower = texto_usuario.lower()
                        if "dia é hoje" in texto_lower or "data" in texto_lower:
                            resposta_ia = f"📅 Hoje é dia {datetime.now().strftime('%d/%m/%Y')}."
                        elif "olá" in texto_lower or "oi" in texto_lower:
                            resposta_ia = "Olá! Sou o seu assistente virtual de dropshipping 24/7. Como posso ajudar na operação hoje?"
                        else:
                            resposta_ia = falar_com_gemini(texto_usuario)
                        
                        url_envio = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                        requests.post(url_envio, json={"chat_id": chat_id, "text": resposta_ia, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Erro de conexão na nuvem: {e}")
            time.sleep(5)

if __name__ == '__main__':
    iniciar_bot()