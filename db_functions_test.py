import db_functions as db
import os
from dotenv import load_dotenv

load_dotenv()

PG_BASE_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 5432))
}

DB_CONFIG = PG_BASE_CONFIG.copy()
DB_CONFIG['dbname'] = os.getenv('DB_NAME')
DB_NAME = os.getenv('DB_NAME')

if __name__ == '__main__':
    db.create_database(DB_NAME, PG_BASE_CONFIG)
    db.create_tables(DB_CONFIG)
    db.create_tables(DB_CONFIG)
    products_list = [

    ("IPH-15-BLU", "iPhone 15 — Blue", "آيفون 15 أزرق", 3999, 80, "Mobile", "أحدث جيل من آيفون مع معالج A16"),
    ("IPH-15-PNK", "iPhone 15 — Pink", "آيفون 15 وردي", 3999, 70, "Mobile", "تصميم أنيق وكاميرا محسّنة"),
    ("IPH-15-PRM", "iPhone 15 Pro Max — Titanium", "آيفون 15 برو ماكس تيتانيوم", 5299, 50, "Mobile", "أقوى هاتف آيفون بأداء فائق ووزن خفيف"),
    ("IPH-14-RED", "iPhone 14 — Red", "آيفون 14 أحمر", 3399, 60, "Mobile", "جهاز مميز ببطارية أطول وشاشة Super Retina"),
    ("IPH-14-GRN", "iPhone 14 — Green", "آيفون 14 أخضر", 3399, 65, "Mobile", "ألوان جذابة مع أداء ممتاز"),

    ("SAM-S24-BLK", "Samsung Galaxy S24 — Black", "سامسونغ جالاكسي S24 أسود", 3799, 90, "Mobile", "هاتف رائد بمعالج قوي وكاميرا متقدمة"),
    ("SAM-S24-WHT", "Samsung Galaxy S24 — White", "سامسونغ جالاكسي S24 أبيض", 3799, 85, "Mobile", "أداء ممتاز وشاشة بجودة عالية"),

    ("SAM-A55-BLU", "Samsung Galaxy A55 — Blue", "سامسونغ جالاكسي A55 أزرق", 1799, 150, "Mobile", "هاتف متوسط الفئة مع بطارية قوية"),
    ("SAM-A55-GRN", "Samsung Galaxy A55 — Green", "سامسونغ جالاكسي A55 أخضر", 1799, 140, "Mobile", "شاشة رائعة وكاميرا بدقة جيدة")
    ]
    db.seed_products(DB_CONFIG, products_list)