import os
import requests
import google.generativeai as genai
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf

# --- KONFIGURACJA TWOICH SEKCJI (ID WĄTKÓW) ---
THREAD_GIELDA = 2
THREAD_AI = 3

# --- KONFIGURACJA GEMINI ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def get_market_summary():
    """Pobiera dane z Bankier.pl i NBP (Waluty)"""
    summary = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # 1. WALUTY (NBP API - najstabilniejsze źródło PLN)
    try:
        nbp_url = "https://nbp.pl"
        rates = requests.get(nbp_url, timeout=10).json()[0]['rates']
        val_map = {r['code']: r['mid'] for r in rates if r['code'] in ['USD', 'EUR', 'CHF', 'GBP']}
        summary.append("WALUTY (PLN):")
        for code, val in val_map.items():
            summary.append(f"- {code}: {val:.4f} PLN")
    except Exception as e:
        summary.append(f"- Waluty: Błąd ({e})")

    # 2. SUROWCE I ROLNICTWO (Bankier.pl)
    summary.append("\nSUROWCE I ROLNICTWO:")
    try:
        url_bankier = "https://bankier.pl"
        resp = requests.get(url_bankier, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        targets = ["Złoto", "Ropa Brent", "Pszenica", "Kukurydza"]
        rows = soup.find_all('tr')
        for row in rows:
            for t in targets:
                if t in row.text:
                    tds = row.find_all('td')
                    if len(tds) > 1:
                        price = tds[1].text.strip()
                        change = tds[2].text.strip()
                        summary.append(f"- {t}: {price} ({change})")
    except Exception as e:
        summary.append(f"- Surowce: Błąd scrapowania")

    return "\n".join(summary)

def get_stock_data():
    """Pobiera dane z Yahoo Finance"""
    tickers = {"S&P 500": "^GSPC", "Nvidia": "NVDA", "Tesla": "TSLA"}
    report = []
    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                price_now = hist['Close'].iloc[-1]
                change = ((price_now - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                report.append(f"- {name}: {price_now:.2f} USD ({change:+.2f}%)")
        except:
            report.append(f"- {name}: Błąd danych")
    return report

def get_ai_news():
    """Pobiera newsy z aioai.pl"""
    try:
        url = "https://aioai.pl"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select('h2 a, h3 a') 
        news = [a.get_text(strip=True) for a in articles if len(a.get_text()) > 10]
        return news[:5]
    except Exception as e:
        return [f"Błąd scrapowania AI: {e}"]

def summarize_with_gemini(raw_data, type="market"):
    """Generuje inteligentne podsumowanie przez Gemini w formacie HTML"""
    role = "ekspertem giełdowym" if type == "market" else "analitykiem technologii AI"
    prompt = f"""
    Jesteś {role}. Na podstawie poniższych danych przygotuj krótkie, konkretne podsumowanie dla użytkownika Telegrama.
    WYMOGI:
    1. Używaj wyłącznie tagów HTML: <b>pogrubienie</b>, <i>kursywa</i>. 
    2. Nie używaj Markdowna (żadnych gwiazdek!).
    3. Pisz zwięźle, w punktach.
    DANE: {raw_data}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"<i>Błąd AI: {e}</i>\n\nSurowe dane:\n{raw_data}"

def send_to_telegram(text, thread_id):
    """Wysyła wiadomość do Telegrama z logowaniem błędów"""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f"https://telegram.org{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "message_thread_id": thread_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    r = requests.post(url, json=payload)
    print(f"DEBUG: Status {r.status_code} dla wątku {thread_id}. Response: {r.text}")
    return r.status_code

if __name__ == "__main__":
    # --- PRZETWARZANIE AI ---
    ai_raw = get_ai_news()
    ai_summary = summarize_with_gemini("\n".join(ai_raw), type="ai")
    final_ai_msg = f"<b>🤖 NOWOŚCI AI</b>\n\n{ai_summary}"
    send_to_telegram(final_ai_msg, THREAD_AI)
    
    # --- PRZETWARZANIE GIEŁDY ---
    market_raw = get_market_summary()
    stocks_raw = get_stock_data()
    combined_market = f"{market_raw}\n\nUSA:\n" + "\n".join(stocks_raw)
    
    market_summary = summarize_with_gemini(combined_market, type="market")
    final_market_msg = f"<b>📈 RAPORT RYNKOWY</b>\n<i>{datetime.now().strftime('%d.%m %H:%M')}</i>\n\n{market_summary}"
    send_to_telegram(final_market_msg, THREAD_GIELDA)
