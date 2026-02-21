-- Bu sorgu, ingestion.py tarafından PostgreSQL içinde bir View olarak oluşturulmaktadır.

SELECT 
    open_time,
    close AS current_price,
    -- Bir önceki saatin kapanış fiyatı (LAG fonksiyonu ile 1 satır geriye gidilir)
    LAG(close, 1) OVER(ORDER BY open_time ASC) AS prev_hour_close_price,
    
    -- Son 3 saatin hareketli ortalaması (Mevcut satır ve önceki 2 satırın ortalaması)
    AVG(close) OVER(ORDER BY open_time ASC ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma_3_hour
FROM 
    raw_crypto_prices;