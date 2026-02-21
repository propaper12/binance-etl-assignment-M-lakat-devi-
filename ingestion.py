import requests
import pandas as pd
from sqlalchemy import create_engine, text
from tenacity import retry, wait_fixed, stop_after_attempt
import os

# 1. RETRY MEKANİZMASI: Hata alırsan 5 saniye bekle, en fazla 3 kere denemek için ekledim
@retry(wait=wait_fixed(5), stop=stop_after_attempt(3))
def fetch_binance_data(symbol="BTCUSDT", interval="1h", limit=720):
    """Binance API'den son 30 günlük veriyi çeker (Hata durumunda tekrar dener)."""
    print(f"[{symbol}] verileri Binance üzerinden çekiliyor...")
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status() # HTTP 429 (Too Many Requests) vs. olursa fırlat ve retry tetiklensin
    data = response.json()
    
    columns = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ]
    df = pd.DataFrame(data, columns=columns)
    
    df = df[["open_time", "open", "high", "low", "close", "volume"]]
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
        
    print(f"Başarılı: {len(df)} satır veri çekildi.")
    return df

def load_and_transform(df):
    """Veriyi UPSERT mantığı ile fiziksel tablolara kaydeder."""
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    user = os.environ.get("DB_USER", "postgres")
    password = os.environ.get("DB_PASS", "postgres")
    db_name = os.environ.get("DB_NAME", "cryptodb")
    
    engine_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(engine_url)
    
    try:
        with engine.begin() as conn:
            # 2. INGESTION: UPSERT MANTIĞI (Staging Table Kullanımı)
            print("Ham veri için UPSERT işlemi başlatılıyor...")
            
            # Ana tablomuzu Primary Key ile oluşturuyoruz (Yoksa)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS raw_crypto_prices (
                    open_time TIMESTAMP PRIMARY KEY,
                    open FLOAT,
                    high FLOAT,
                    low FLOAT,
                    close FLOAT,
                    volume FLOAT
                );
            """))
            
            # Gelen datayı önce geçici (staging) tabloya yazdım (replace burada güvenlidir çünkü tablo geçicidir)
            df.to_sql("staging_raw_crypto", engine, if_exists="replace", index=False)
            
            # Geçici tablodan ana tabloya UPSERT (On Conflict Do Nothing) yap
            conn.execute(text("""
                INSERT INTO raw_crypto_prices (open_time, open, high, low, close, volume)
                SELECT open_time, open, high, low, close, volume FROM staging_raw_crypto
                ON CONFLICT (open_time) DO NOTHING;
            """))
            print("Ham veri UPSERT başarılı!")

            # 3. TRANSFORMATION: Fiziksel tabloya yazma islemini yapıyoruz 
            print("Dönüşüm verileri fiziksel tabloya işleniyor...")
            
            # Transformed tablosunu PK ile oluşturuyoruz (Yoksa)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS transformed_crypto_metrics (
                    open_time TIMESTAMP PRIMARY KEY,
                    current_price FLOAT,
                    prev_hour_close_price FLOAT,
                    ma_3_hour FLOAT
                );
            """))
            
            # Window Function hesaplamalarını yapıp ve fiziksel tabloya UPSERT ediyoruz
            # Geçmiş veriler (hareketli ortalamalar vs) değişebileceği için DO UPDATE SET kullanıyoruz
            conn.execute(text("""
                INSERT INTO transformed_crypto_metrics (open_time, current_price, prev_hour_close_price, ma_3_hour)
                SELECT 
                    open_time,
                    close AS current_price,
                    LAG(close, 1) OVER(ORDER BY open_time ASC) AS prev_hour_close_price,
                    AVG(close) OVER(ORDER BY open_time ASC ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma_3_hour
                FROM raw_crypto_prices
                ON CONFLICT (open_time) DO UPDATE SET 
                    current_price = EXCLUDED.current_price,
                    prev_hour_close_price = EXCLUDED.prev_hour_close_price,
                    ma_3_hour = EXCLUDED.ma_3_hour;
            """))
            
            # Geçici tabloyu temizlemek için ekledim
            conn.execute(text("DROP TABLE IF EXISTS staging_raw_crypto;"))
            
            print("Fiziksel transformation ve UPSERT işlemi başarıyla tamamlandı!")

    except Exception as e:
        print(f"Veritabanı işlemi sırasında kritik hata: {e}")

if __name__ == "__main__":
    df = fetch_binance_data()
    if df is not None:
        load_and_transform(df)