import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- KONFIGURACJA TWOICH SEKCJI ---
# Zmień te numery na poprawne ID od Rose bota
THREAD_GIELDA = 2  # ID, które już mamy
THREAD_AI = 3      # WPISZ TU ID sekcji Nowości AI od Rose bota

def get_ai_news():
    """Pobiera 3 najnowsze nagłówki z portalu aioai.pl"""
    try:
        url = "https://aioai.pl"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Selektor h2 zazwyczaj zawiera tytuły artykułów
        articles = soup.find_all('h2', limit=3)
        news = [a.get_text(strip=True) for a in articles]
        return news if news else ["Brak nowych wiadomości w tej chwili."]
    except Exception as e:
        return [f"Błąd połączenia z portalem: {e}"]

def send_to_telegram(text, thread_id):
    """Wysyła sformatowaną wiadomość do konkretnego wątku"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://telegram.org{token}/sendMessage"
    
    payload = {
        "chat_id": chat_id,
        "message_thread_id": thread_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    return r.status_code

if __name__ == "__main__":
    # 1. GENEROWANIE I WYSYŁKA NEWSÓW AI
    ai_list = get_ai_news()
    ai_msg = "*🤖 NAJNOWSZE MODELE AI (via AI o AI)*\n\n" + "\n\n".join([f"• {n}" for n in ai_list])
    send_to_telegram(ai_msg, THREAD_AI)
    
    # 2. GENEROWANIE I WYSYŁKA RAPORTU GIEŁDOWEGO
    # Tu w przyszłości dodamy pobieranie kursów (np. yfinance)
    stock_msg = f"*📈 RAPORT GIEŁDOWY*\n_Aktualizacja: {datetime.now().strftime('%H:%M')}_\n\nMonitorowanie trendów rynkowych w toku. Sprawdź sentyment na X."
    send_to_telegram(stock_msg, THREAD_GIELDA)
