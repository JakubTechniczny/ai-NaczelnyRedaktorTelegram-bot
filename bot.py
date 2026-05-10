import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- KONFIGURACJA TWOICH SEKCJI ---
# Zmień te numery na poprawne ID od Rose bota
THREAD_GIELDA = 2  # ID, które już mamy
THREAD_AI = 3      # WPISZ TU ID sekcji Nowości AI od Rose bota

import yfinance as yf


def get_stock_data():
    # Pobieramy dane dla S&P500, Nvidii i Tesli
    tickers = {"S&P 500": "^GSPC", "Nvidia": "NVDA", "Tesla": "TSLA"}
    report = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            # Pobieramy historię z ostatniego dnia, aby obliczyć zmianę
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price_now = hist['Close'].iloc[-1]
                price_prev = hist['Close'].iloc[-2]
                change = ((price_now - price_prev) / price_prev) * 100
                report.append(f"• {name}: {price_now:.2f} USD ({change:+.2f}%)")
            else:
                # Jeśli rynek jest zamknięty lub brak danych
                price = ticker.fast_info['last_price']
                report.append(f"• {name}: {price:.2f} USD (0.00%)")
        except Exception as e:
            report.append(f"• {name}: Błąd danych")
    return report

def get_ai_news():
    try:
        url = "https://aioai.pl"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukamy konkretnie tytułów w tagach h2 lub h3, które są linkami
        articles = soup.select('h2 a, h3 a') 
        news = [a.get_text(strip=True) for a in articles if len(a.get_text()) > 10]
        return news[:3] # Weź 3 najświeższe
    except Exception as e:
        return [f"Błąd scrapowania: {e}"]


def send_to_telegram(text, thread_id):
    """Wysyła sformatowaną wiadomość do konkretnego wątku"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    
    payload = {
        "chat_id": chat_id,
        "message_thread_id": thread_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload)
    return r.status_code

if __name__ == "__main__":
    # 1. SEKCJA AI (To już Ci działa, upewnij się tylko że thread_id jest poprawne)
    ai_list = get_ai_news()
    ai_msg = "*🤖 NAJNOWSZE MODELE AI (via AI o AI)*\n\n" + "\n\n".join([f"• {n}" for n in ai_list])
    send_to_telegram(ai_msg, THREAD_AI)
    
    # 2. SEKCJA GIEŁDA (Tu była blokada - teraz wywołujemy nową funkcję)
    stocks_list = get_stock_data() # Wywołujemy funkcję, która pobiera ceny
    stock_msg = f"*📈 RAPORT GIEŁDOWY*\n_Aktualizacja: {datetime.now().strftime('%H:%M')}_\n\n" + "\n".join(stocks_list)
    send_to_telegram(stock_msg, THREAD_GIELDA)

