import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf

# --- KONFIGURACJA TWOICH SEKCJI ---
THREAD_GIELDA = 2
THREAD_AI = 3

def get_market_summary():
    """Pobiera dane z Bankier.pl, Money.pl i Business Insider"""
    summary = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # 1. WALUTY (Money.pl / NBP)
    try:
        # Używamy API NBP dla pewności danych walutowych w PLN
        nbp_url = "https://nbp.pl"
        rates = requests.get(nbp_url, timeout=10).json()[0]['rates']
        val_map = {r['code']: r['mid'] for r in rates if r['code'] in ['USD', 'EUR', 'CHF', 'GBP']}
        summary.append("💱 *Waluty (PLN):*")
        for code, val in val_map.items():
            summary.append(f"• {code}: {val:.4f} PLN")
    except:
        summary.append("• Waluty: Błąd pobierania")

    # 2. SUROWCE I ROLNICTWO (Bankier.pl)
    summary.append("\n🌾 *Surowce i Rolnictwo (Bankier):*")
    try:
        url_bankier = "https://www.bankier.pl/surowce/notowania"
        resp = requests.get(url_bankier, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Szukamy wybranych surowców w tabeli
        targets = {"Złoto": "USD/uncja", "Ropa Brent": "USD", "Pszenica": "USc/buszel"}
        rows = soup.find_all('tr')
        for row in rows:
            text = row.text
            for name in targets.keys():
                if name in text:
                    tds = row.find_all('td')
                    price = tds[1].text.strip()
                    change = tds[2].text.strip()
                    summary.append(f"• {name}: {price} {targets[name]} ({change})")
                    break
    except:
        summary.append("• Surowce: Błąd scrapowania")

    # 3. INDEKSY (Business Insider)
    summary.append("\n📈 *Rynek (Business Insider):*")
    try:
        url_bi = "https://businessinsider.com.pl/gielda"
        resp = requests.get(url_bi, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Wyciągamy WIG20 (często pierwszy w tabelach BI)
        wig20 = soup.find(text="WIG20")
        if wig20:
            parent = wig20.find_parent('tr')
            val = parent.find_all('td')[1].text.strip()
            summary.append(f"• WIG20: {val} pkt")
    except:
        summary.append("• Indeksy: Brak danych")

    return "\n".join(summary)

def get_stock_data():
    # Twoja oryginalna funkcja yfinance
    tickers = {"S&P 500": "^GSPC", "Nvidia": "NVDA", "Tesla": "TSLA"}
    report = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price_now = hist['Close'].iloc[-1]
                change = ((price_now - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                report.append(f"• {name}: {price_now:.2f} USD ({change:+.2f}%)")
        except:
            report.append(f"• {name}: Błąd danych")
    return report

def get_ai_news():
    # Twoja oryginalna funkcja AI
    try:
        url = "https://aioai.pl"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select('h2 a, h3 a') 
        news = [a.get_text(strip=True) for a in articles if len(a.get_text()) > 10]
        return news[:3]
    except Exception as e:
        return [f"Błąd scrapowania AI: {e}"]

def send_to_telegram(text, thread_id):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    # PONIŻEJ POPRAWNY ADRES:
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
    # 1. SEKCJA AI
    ai_list = get_ai_news()
    ai_msg = "*🤖 NOWOŚCI AI*\n\n" + "\n\n".join([f"• {n}" for n in ai_list])
    send_to_telegram(ai_msg, THREAD_AI)
    
    # 2. SEKCJA GIEŁDA + NOWE ŹRÓDŁA
    market_data = get_market_summary()
    stock_data = get_stock_data()
    
    full_stock_msg = (
        f"*🌍 RAPORT RYNKOWY*\n_{datetime.now().strftime('%d.%m.%Y %H:%M')}_\n\n"
        f"{market_data}\n\n"
        f"🇺🇸 *USA (Yahoo Finance):*\n" + "\n".join(stock_data)
    )
    send_to_telegram(full_stock_msg, THREAD_GIELDA)
