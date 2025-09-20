import logging
from config import engine
from sqlalchemy import text

# Loglama ayarları
logging.basicConfig(
    filename='index_maintenance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def maintain_indexes():
    logging.info("Index bakımı başlatıldı.")

    try:
        with engine.begin() as conn:  # begin() → otomatik transaction
            # Fragmentasyon sorgusu
            result = conn.execute(text("""
                SELECT 
                    OBJECT_NAME(ips.object_id) AS TableName,
                    i.name AS IndexName,
                    ips.index_id,
                    ips.avg_fragmentation_in_percent
                FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') AS ips
                JOIN sys.indexes AS i
                    ON ips.object_id = i.object_id
                    AND ips.index_id = i.index_id
                WHERE i.type_desc <> 'HEAP'
                ORDER BY ips.avg_fragmentation_in_percent DESC
            """))

            indexes = result.fetchall()

            for table_name, index_name, index_id, frag in indexes:
                if frag > 40:
                    sql = f"ALTER INDEX [{index_name}] ON [{table_name}] REBUILD"
                    logging.info(f"REBUILD: {table_name}.{index_name} (%{frag:.2f})")
                    conn.execute(text(sql))
                elif frag > 10:
                    sql = f"ALTER INDEX [{index_name}] ON [{table_name}] REORGANIZE"
                    logging.info(f"REORGANIZE: {table_name}.{index_name} (%{frag:.2f})")
                    conn.execute(text(sql))

        logging.info("Index bakımı tamamlandı ve commit edildi!")

    except Exception as e:
        logging.error(f"Index bakımı sırasında hata oluştu: {e}")
        print(f"Hata oluştu, detaylar log dosyasında: {e}")

if __name__ == "__main__":
    maintain_indexes()
