import os
import requests
from google import genai
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf

# --- KONFIGURACJA ---
THREAD_GIELDA = 2
THREAD_AI = 3

# --- NOWA BIBLIOTEKA GEMINI (google-genai) ---
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def get_market_summary():
    summary = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 1. Waluty (NBP)
    try:
        nbp_url = "https://nbp.pl"
        rates = requests.get(nbp_url, timeout=10).json()['rates']
        val_map = {r['code']: r['mid'] for r in rates if r['code'] in ['USD', 'EUR', 'CHF', 'GBP']}
        summary.append("WALUTY (PLN): " + ", ".join([f"{k}: {v:.4f}" for k, v in val_map.items()]))
    except:
        summary.append("Waluty: Błąd pobierania")

    # 2. Surowce (Bankier)
    try:
        url = "https://bankier.pl"
        resp = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Przekazujemy tekst do AI, niech ono go oczyści
        summary.append("SUROWCE: " + soup.get_text()[:1000])
    except:
        summary.append("Surowce: Błąd scrapowania")

    return "\n".join(summary)

def summarize_with_gemini(raw_data, category):
    prompt = f"Jesteś analitykiem ({category}). Stwórz zwięzłe podsumowanie w punktach używając HTML (<b>, <i>). Nie używaj markdowna. Dane: {raw_data}"
    try:
        # Używamy najnowszego modelu 2.0 Flash
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"Błąd AI: {e}"

def send_to_telegram(text, thread_id):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    # POPRAWIONY ADRES URL:
    url = f"https://telegram.org{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "message_thread_id": thread_id,
        "text": text,
        "parse_mode": "HTML"
    }
    r = requests.post(url, json=payload)
    return r.status_code

if __name__ == "__main__":
    # Nowości AI (tutaj wstaw swoją funkcję scrapującą aioai.pl)
    ai_raw = "Tu wstaw wynik z Twojej funkcji get_ai_news()"
    ai_summary = summarize_with_gemini(ai_raw, "AI")
    send_to_telegram(f"<b>🤖 NOWOŚCI AI</b>\n\n{ai_summary}", THREAD_AI)

    # Giełda
    m_raw = get_market_summary()
    m_summary = summarize_with_gemini(m_raw, "Giełda")
    send_to_telegram(f"<b>📈 RAPORT RYNKOWY</b>\n\n{m_summary}", THREAD_GIELDA)
