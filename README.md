# Crypto ETL Pipeline 🚀

Bu proje, Binance API kullanarak bir kripto para biriminin (BTC/USDT) saatlik fiyat verilerini çeken, dönüştüren ve PostgreSQL veritabanına yükleyen **Dockerize edilmiş bir ETL (Extract, Transform, Load)** boru hattıdır.

Bir mülakat görevi olarak tasarlanmış olup, endüstri standartları (Best Practices) gözetilerek geliştirilmiştir.

## 🛠️ Teknolojiler
* **Python 3.10:** Veri çekme (Requests), işleme (Pandas) ve veritabanı iletişimi (SQLAlchemy).
* **PostgreSQL 15:** Ham (Raw) ve dönüştürülmüş (Transformed) verilerin saklandığı veri ambarı.
* **Adminer:** Veritabanını tarayıcı üzerinden yönetmek ve görselleştirmek için hafif bir arayüz.
* **Docker & Docker Compose:** Tüm altyapının tek tuşla izole bir şekilde ayağa kaldırılması.

## ⚙️ Nasıl Çalıştırılır?

Projeyi bilgisayarınızda çalıştırmak için Docker ve Docker Compose'un kurulu olması yeterlidir.

1. Repoyu klonlayın ve proje dizinine gidin.
2. Aşağıdaki komut ile tüm sistemi ayağa kaldırın:
   ```bash
   docker-compose up --build -d