from mcp.server.fastmcp import FastMCP
import psycopg2
import db_functions as db
import os, sys
from dotenv import load_dotenv
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

mcp = FastMCP('mcp-ecommerce')

@mcp.resource("resource://pg_config_resource")
def pg_config_resource():
    return {
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432))
    }

@mcp.resource("resource://db_name_resource")
def db_name_resource():
    return os.getenv("DB_NAME")

@mcp.resource("resource://db_config_resource")
def db_config_resource():
    DB_CONFIG = pg_config_resource().copy()
    DB_CONFIG["dbname"] = os.getenv("DB_NAME")
    return DB_CONFIG

@mcp.resource("resource://custom_data_snippet_resource")
def custom_data_snippet_resource():
    with open("ecommerce_data.txt", encoding="utf-8") as f:
        return f.read()

@mcp.resource("resource://telegram_token_resource")
def telegram_token_resource():
    return os.getenv("TELEGRAM_TOKEN", "")   

def normalize_arabic(text):
    text=text.replace("آ", "ا")
    text=text.replace("أ", "ا")
    text=text.replace("إ", "ا")
    text=text.replace("ؤ", "و")
    text=text.replace("ئ", "ي")
    text=text.replace("ـ", "")
    return text

def _sql_norm(field):
    f = field
    f = f"REPLACE({f}, 'آ', 'ا')"
    f = f"REPLACE({f}, 'أ', 'ا')"
    f = f"REPLACE({f}, 'إ', 'ا')"
    f = f"REPLACE({f}, 'ؤ', 'و')"
    f = f"REPLACE({f}, 'ئ', 'ي')"
    f = f"REPLACE({f}, 'ـ', '')"
    return f

def _connect():
    DB_CONFIG = db_config_resource()
    return psycopg2.connect(**DB_CONFIG)

@mcp.tool(name='search_products')
def search_products(product="", limit = 10):
    aname_expr = _sql_norm('aname')
    cat_expr = _sql_norm('category')
    description_expr = _sql_norm('description')

    params=[]

    if product:
        nproduct = normalize_arabic(product.lower())
        sql = f"""
            SELECT id, sku, name, aname, price, stock, category, description
            FROM products
            WHERE  
        """

        sql += f"""
            LOWER(name)    LIKE %s OR
            LOWER(sku)    LIKE %s OR
            LOWER({aname_expr})   LIKE %s OR
            LOWER({cat_expr})     LIKE %s OR
            LOWER({description_expr})   LIKE %s 
        """

        like = f'%{nproduct}%'

        params.extend([like, like, like, like, like])

        try:
            with _connect() as cn, cn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                if rows:
                    found=True
        except Exception as e:
            return f'خطأ في قاعدة البيانات: {e}'

        if not rows:
            return 'لا توجد منتجات متاحة حاليا.'

    if found:
        result="  هذه بعض المنتجات الموافقة لطلبك:   \n"
    
    else:
        result="لم يتم العثور على منتجات توافقك طلبك هذه بعض المنتجات المتوفرة لدينا\n"

    lines=[]

    for r in rows:
        lines.append(
            f"   • اسم المنتج: {r[3]}\n"
            f"   • اسم المنتج الانكليزي: {r[2]}\n"
            f"   • رمز المنتج: {r[1]}\n"
            f"   • السعر: {r[4]} \n"
            f"   • الكمية المتوفرة: {r[5]}\n"
            f"   • الفئة: {r[6]}\n"
            f"   • الوصف: {r[7]}\n"
        )

    result = result + '\n'.join(lines)
    result = result + "\n\nلطلب أي منتج يرجى كتابة رمز المنتج في الطلب"
    result = result + '\n'+ custom_data_snippet_resource()

    return result


@mcp.tool(name='add order')
def add_order(sku='', user_id='GUEST'):
    if not sku:
        return " يجب إدخال رمز المنتج (SKU)."
    if not user_id:
        return " يجب إدخال رقم المستخدم "

    try:
        with _connect as cn , cn.cursor() as cur:

            cur.execute(
                """
                SELECT aname, name, price, stock, category, description
                FROM products
                WHERE sku = %s
                """,
                (sku,),
            )

            row = cur.fetchone()
            if not row:
                return f"⚠️ لم يتم العثور على المنتج برمز: {sku}"

            aname, name, price, stock, category, description = row
            if stock is None or stock <= 0:
                return f"⚠️ المنتج {aname or name} غير متوفر حالياً."

            cur.execute("SELECT nextval('oreder_seq')")
            seq = cur.fetchone()[0]
            year = datetime.now().year
            order_id = f'ORD-{year}-{seq:05d}'

            cur.execute(
                """
                INSERT INTO orders (order_id, user_id, sku, total, status)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (order_id, user_id, sku, price, "created"),
            )

            cur.execute(
                "UPDATE products SET stock = stock - 1 WHERE sku = %s",
                (sku,),
            )

            cn.commit()

        msg = (
            f"تم إنشاء طلبية جديدة\n\n"
            f"• رقم الطلبية: {order_id}\n"
            f"• المستخدم: {user_id}\n"
            f"• المنتج: {aname or name}\n"
            f"• رمز المنتج (SKU): {sku}\n"
            f"• الإجمالي: {price} ريال\n"
            f"• الفئة: {category or '-'}\n"
            f"• الوصف: {description or '-'}\n"
            f"• الحالة: created\n\n"
            f"إحتفظ برقم الطلبية لأي استفسار لاحق عنها"
        )
        msg= msg + "\n"+ custom_data_snippet_resource()
        return msg

    except Exception as e:
        return f'خطأ في قاعدة البيانات: {e}'    


mcp.tool(name='track_order')
def track_order(order_id: str) -> str:
    if not order_id:
        return "الرجاء إدخال رقم الطلبية."
    try:
        with _connect as cn, cn.cursor() as cur:
            cur.execute("SELECT status FROM orders WHERE order_id = %s", (order_id,))
            row = cur.fetchone()
            if not row:
                return f"لم يتم العثور على طلبية بهذا الرقم: {order_id}"

            status = row[0]

        msg = ( 
            "حالة الطلبية"
            f"• رقم الطلبية: {order_id}"
            f"• الحالة الحالية: {status}"
        )
        msg= msg + "\n"+ custom_data_snippet_resource()
        return msg

    except Exception as e:
        return f"حدث خطأ أثناء الاستعلام عن الطلبية: {e}"


mcp.tool(name='cancel_order')
def cancel_order(order_id):
    if not order_id:
        return "⚠️ الرجاء إدخال رقم الطلبية."
    try:
        with _connect as cn, cn.cursor() as cur:


            cur.execute(
                    "SELECT status, sku FROM orders WHERE order_id = %s",
                    (order_id,),
            )
            row = cur.fetchone()
            if not row:
                return f"⚠️ لم يتم العثور على طلبية بهذا الرقم: {order_id}"

            status = row[0]
            sku = row[1]

            if status in ("cancelled", "shipped", "delivered"):
                return f"⚠️ لا يمكن إلغاء الطلبية، الحالة الحالية: {status}"

            cur.execute(
                "UPDATE orders SET status = %s WHERE order_id = %s",
                    ("cancelled", order_id),
            )

            cur.execute(
                    "UPDATE products SET stock = stock + 1 WHERE sku = %s",
                    (sku,),
                )

            cn.commit()

        return (
            "تم إلغاء الطلبية بنجاح\n"
            f"• رقم الطلبية: {order_id}\n"
            f"• الحالة الجديدة: cancelled\n"
            f"• رمز المنتج  : {sku}\n"
        )

    except Exception as e:
        return f"حدث خطأ أثناء إلغاء الطلبية: {e}"

mcp.tool(name='list_user_orders')
def list_user_orders(user_id='GUEST'):

    if not user_id:
        return 'الرجاء إدخال معرف المستخدم (user_id).'

    sql = """
        SELECT
            o.order_id,          -- رقم الطلبية
            o.status,            -- الحالة
            o.total,             -- الإجمالي
            o.sku,               -- رمز المنتج
            p.aname,             -- الاسم العربي للمنتج
            p.name,              -- الاسم الإنجليزي للمنتج
            p.price,             -- السعر الحالي للمنتج (للمعلومة)
            p.category           -- الفئة
        FROM orders o
        LEFT JOIN products p ON p.sku = o.sku
        WHERE o.user_id = %s
    """

    sql += " ORDER BY o.order_id DESC"

    params = [user_id]

    try:
        with _connect() as cn, cn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        if not rows:
            base = f"لا توجد أي طلبات مسجّلة للمستخدم: {user_id}"
            base += "\n" + custom_data_snippet_resource()
            return base

        lines = []
        grand_total = 0
        for (order_id, st, total, sku, aname, name, price, category) in rows:
            grand_total += float(total or 0)
            lines.append(
                "———————————————\n"
                f"رقم الطلبية: {order_id}\n"
                f"• الحالة: {st}\n"
                f"• المنتج: {aname or name or '-'}\n"
                f"• SKU: {sku}\n"
                f"• الفئة: {category or '-'}\n"
                f"• سعر المنتج  {price if price is not None else '-'}\n"
                f"• إجمالي الطلبية: {total if total is not None else '-'}\n"
            )

        summary = (
            f"\nإجمالي عدد الطلبيات المعروضة: {len(rows)}"
            f"\nمجموع الإجماليات: {grand_total:.2f}"
        )

        result = "\n".join(lines) + summary

        return result

    except Exception as e:
        return f"حدث خطأ أثناء جلب الطلبيات: {e}"

@mcp.tool(name="default_response")
def default_response():
    msg= "يمكنك البحث وطلب المنتجات   "
    msg= msg + "\n"+ custom_data_snippet_resource()
    return msg

@mcp.prompt(
    name="ecommerce_prompt",
    description="تصنيف رسالة المستخدم واستدعاء الأداة المناسبة بصيغة JSON."
)
def appointment_prompt(user_input: str):
    return f"""
    أنت مساعد ذكي باللغة العربية. مهمتك فهم رسالة المستخدم بدقة، ثم إرجاع كائن JSON واحد فقط
    لاستدعاء الأداة المناسبة من بين الأدوات المتاحة أدناه.

    🧭 الأوامر المتاحة:

    1) **الاستعلام عن منتج**
       الأداة: search_products
       المتطلبات:
        - product : المنتج   

    2) **طلب شراء منتج (طلبية)**
       الأداة: add_order
       المتطلبات:
        - sku     : معرف المنتج (SKU)
        - user_id : معرف المستخدم

    3) **الاستعلام عن حالة طلبية**
       الأداة: track_order
       المتطلبات:
        - order_id : معرف الطلبية

    4) **إلغاء طلبية**
       الأداة: cancel_order
       المتطلبات:
        - order_id : معرف الطلبية

    5) **الاستعلام عن جميع الطلبيات لعميل **
       الأداة: list_user_orders
       المتطلبات:
    - user_id : رقم/معرف المستخدم

    6) **سؤال غير مفهوم     **
       الأداة: default_response


     التعليمات:
    - حلّل رسالة المستخدم وحدد أداة واحدة فقط من القائمة أعلاه.
    - أرجِع كائن JSON واحد صحيح البنية دون أي شروحات إضافية.
    - لا تفترض معلومات غير مذكورة صراحة.
    - إذا كانت الرسالة ترحيب/سلام/وداع أو غير مفهومة، استخدم default_response فقط.

     رسالة المستخدم:
    {user_input}

     الإخراج المطلوب (أحد الأمثلة التالية فقط، وبلا أي تعليق):

    مثال للاستعلام عن منتج:
    {{
    "tool": "search_products",
    "args": {{
        "product": "أيفون"
    }}
    }}

    مثال لطلبية منتج:
    {{
    "tool": "add_order",
    "args": {{
        "sku": "",
        "user_id": ""
    }}
    }}

    مثال للاستعلام عن طلبية:
    {{
    "tool": "track_order",
    "args": {{
        "order_id": "ORD-2025-000001"
    }}
    }}

    مثال لإلغاء طلبية:
    {{
    "tool": "cancel_order",
    "args": {{
        "order_id": "ORD-2025-000001"
    }}
    }}

    مثال للاستعلام عن جميع طلبيات مستخدم:
    {{
    "tool": "list_user_orders",
    "args": {{
        "user_id": "123456789"
    }}
    }}

     إذا لم تكن الرسالة واضحة، استخدم:
    {{
    "tool": "default_response",
    "args": {{}}
    }}

     تذكير: يجب أن يكون الإخراج دائمًا كائن JSON واحد صحيح فقط، بلا أي نص آخر.
"""


if __name__ == '__main__':

    try:
        # إعدادات PostgreSQL
        PG_BASE_CONFIG = pg_config_resource()
        # إعدادات قاعدة البيانات
        DB_CONFIG = db_config_resource()
        # اسم قاعدة البيانات
        DB_NAME = db_name_resource()

        # إنشاء قاعدة البيانات إن لم تكن موجودة
        db.create_database(DB_NAME, PG_BASE_CONFIG)
        # إنشاء الجداول
        db.create_tables(DB_CONFIG)
        # إدخال بعض المنتجات
        products_list = [
            # آيفون 
            ("IPH-15-BLU", "iPhone 15 — Blue", "آيفون 15 أزرق", 3999, 80, "Mobile", "أحدث جيل من آيفون مع معالج A16"),
            ("IPH-15-PNK", "iPhone 15 — Pink", "آيفون 15 وردي", 3999, 70, "Mobile", "تصميم أنيق وكاميرا محسّنة"),
            ("IPH-15-PRM", "iPhone 15 Pro Max — Titanium", "آيفون 15 برو ماكس تيتانيوم", 5299, 50, "Mobile", "أقوى هاتف آيفون بأداء فائق ووزن خفيف"),
            ("IPH-14-RED", "iPhone 14 — Red", "آيفون 14 أحمر", 3399, 60, "Mobile", "جهاز مميز ببطارية أطول وشاشة Super Retina"),
            ("IPH-14-GRN", "iPhone 14 — Green", "آيفون 14 أخضر", 3399, 65, "Mobile", "ألوان جذابة مع أداء ممتاز"),
            # سامسونغ S24
            ("SAM-S24-BLK", "Samsung Galaxy S24 — Black", "سامسونغ جالاكسي S24 أسود", 3799, 90, "Mobile", "هاتف رائد بمعالج قوي وكاميرا متقدمة"),
            ("SAM-S24-WHT", "Samsung Galaxy S24 — White", "سامسونغ جالاكسي S24 أبيض", 3799, 85, "Mobile", "أداء ممتاز وشاشة بجودة عالية"),
            # سامسونغ A55
            ("SAM-A55-BLU", "Samsung Galaxy A55 — Blue", "سامسونغ جالاكسي A55 أزرق", 1799, 150, "Mobile", "هاتف متوسط الفئة مع بطارية قوية"),
            ("SAM-A55-GRN", "Samsung Galaxy A55 — Green", "سامسونغ جالاكسي A55 أخضر", 1799, 140, "Mobile", "شاشة رائعة وكاميرا بدقة جيدة")
        ]

        db.seed_products(DB_CONFIG, products_list)

        mcp.run(transport="stdio")

    except KeyboardInterrupt:
        print("\n🛑 MCP server stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"⚠️ حدث خطأ: {e}")