import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database(DB_NAME, PG_BASE_CONFIG):
    try:
        conn = psycopg2.connect(**PG_BASE_CONFIG, dbname='postgres')

        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cur:
            cur.execute('SELECT 1 FROM pg_database WHERE datname = %s', (DB_NAME,))

            if not cur.fetchone():
                cur.execute(f'CREATE DATABASE "{DB_NAME}"')
                print(f'تم إنشاء قاعدة البيانات: {DB_NAME}')

            else:
                print(f'قاعدة البيانات موجودة مسبقا: {DB_NAME}')

        conn.close()

    except Exception as e:
        print(f'فشل في إنشاء قاعدة البيانات: {e}')

def create_tables(DB_CONFIG):
    """إنشاء الجداول إذا لم تكن موجودة"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            
            with conn.cursor() as cur:
                
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS products (
                        id          SERIAL PRIMARY KEY, -- رقم تسلسلي المفتاح الرئيسي
                        sku         TEXT UNIQUE NOT NULL, -- معرف المنتج فريد
                        name        TEXT NOT NULL, -- اسم المنتج بالإنكليزية
                        aname        TEXT NOT NULL, -- اسم المنتج بالعربية
                        price       NUMERIC(10,2) NOT NULL CHECK (price >= 0), -- السعر
                        stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0), -- الكمية المتوفرة
                        category    TEXT, -- فئة المنتج
                        description TEXT -- وصف المنتج
                    );
                    CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
                    """
                )

                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS orders (
                        order_id    TEXT PRIMARY KEY,  -- معرف الطلبية
                        user_id     TEXT NOT NULL, -- معرف المستخدم
                        sku         TEXT NOT NULL, -- معرف المنتج
                        total       NUMERIC(12,2) NOT NULL CHECK (total >= 0), -- الإجمالي المترتب
                        status      TEXT NOT NULL,     -- created,   packed, shipped,   delivered, cancelled -- حالة الطلبية
                        created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW() -- تاريخ إنشاء الطلبية

                    );
                    """
                )

                cur.execute(
                    """
                CREATE SEQUENCE IF NOT EXISTS order_seq START 1;
                    """
                )
            conn.commit()
        print("تم إنشاء الجداول بنجاح (إن لم تكن موجودة).  ")
    except Exception as e:
        print(f"فشل في إنشاء الجداول: {e}")


def seed_products(DB_CONFIG, products):

    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO products (sku, name,aname, price, stock, category, description)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sku) DO NOTHING
                    """,
                    list(products),
                )
            conn.commit()
        print("تم إدخال بيانات المنتجات الأولية (إن لم تكن موجودة).")
    
    except Exception as e:
        print(f"فشل في إدخال البيانات الأولية: {e}" )
        raise
