import socket
import os
import logging
import psycopg2
import urllib.parse
from datetime import datetime
import pytz
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Import the keep_alive script
from keep_alive import keep_alive  

# ---------------- CONFIG ----------------
BOT_TOKEN = os.getenv("BOT_TOKEN") 
ADMIN_ID_STR = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR and ADMIN_ID_STR.isdigit() else 0
DATABASE_URL = os.getenv("DATABASE_URL") 

WELCOME_VIDEO = "pos 1.jpg" 

# --- GLOBAL CACHE FOR WELCOME MEDIA ---
WELCOME_MEDIA_CACHE = {"id": None, "type": None} 

# --- TIERED COMMISSION CONFIGURATION ---
TIERED_COMMISSION = {
    50000.01: 0.020,
    36000.00: 0.030,
    26000.00: 0.035,
    14000.00: 0.040,
    6000.00: 0.045,
    0.00: 0.050,
}

# --- PAYMENT INFO ---
PAYMENT_INFO = {
    "telebirr": "+251955974297",
    "cbe": "CBE 1000726676422",
    "awash": "Awash 013201266613100",
    "abyssinia": "Abyssinia 167170668",
}

# --- SERVICES CONFIGURATION ---
SERVICES = {
    "tiktok": {
        "label_am": "ቲክቶክ 🎵", "label_en": "TikTok 🎵",
        "sub": {
            "likes": {"label_am": "ላይክ", "label_en": "Likes", "packages": [{"title_en": "500 Likes", "title_am": "500 ላይክ", "price": 110.00}, {"title_en": "1000 Likes", "title_am": "1000 ላይክ", "price": 224.00}, {"title_en": "3000 Likes", "title_am": "3000 ላይክ", "price": 314.00}, {"title_en": "5000 Likes", "title_am": "5000 ላይክ", "price": 566.25}, {"title_en": "10000 Likes", "title_am": "10000 ላይክ", "price": 924.00}, {"title_en": "20000 Likes", "title_am": "20000 ላይክ", "price": 1467.00}, {"title_en": "50000 Likes", "title_am": "50000 ላይክ", "price": 2674.00}]},
            "followers": {"label_am": "ፎሎወር", "label_en": "Followers", "packages": [{"title_en": "100 Followers", "title_am": "100 የቲክቶክ ፎሎወር", "price": 188.75}, {"title_en": "350 Followers", "title_am": "350 የቲክቶክ ፎሎወር", "price": 397.0}, {"title_en": "1000 Followers", "title_am": "1000 የቲክቶክ ፎሎወር", "price": 969.0}, {"title_en": "1500 Followers", "title_am": "1500 የቲክቶክ ፎሎወር", "price": 1393.75}, {"title_en": "2000 Followers", "title_am": "2000 የቲክቶክ ፎሎወር", "price": 1843.75}, {"title_en": "5000 Followers", "title_am": "5000 የቲክቶክ ፎሎወር", "price": 4366.25}, {"title_en": "10000 Followers", "title_am": "10000 የቲክቶክ ፎሎወር", "price": 8300.0}, {"title_en": "20000 Followers", "title_am": "20000 የቲክቶክ ፎሎወር", "price": 16062.5}, {"title_en": "40000 Followers", "title_am": "40000 የቲክቶክ ፎሎወር", "price": 29100.0}]},
            "views": {"label_am": "እይታ", "label_en": "Views", "packages": [{"title_en": "500 Views", "title_am": "500 እይታ", "price": 89.00}, {"title_en": "1000 Views", "title_am": "1000 እይታ", "price": 131.00}, {"title_en": "3000 Views", "title_am": "3000 እይታ", "price": 393.00}, {"title_en": "5000 Views", "title_am": "5000 እይታ", "price": 465.00}, {"title_en": "10000 Views", "title_am": "10000 እይታ", "price": 810.00}, {"title_en": "20000 Views", "title_am": "20000 እይታ", "price": 1420.00}, {"title_en": "50000 Views", "title_am": "50000 እይታ", "price": 2110.00}]},
            "saves": {"label_am": "ሴቭ", "label_en": "Saves", "packages": [{"title_en": "300 Saves", "title_am": "300 ሴቭ", "price": 89.00}, {"title_en": "500 Saves", "title_am": "500 ሴቭ", "price": 163.00}, {"title_en": "1000 Saves", "title_am": "1000 ሴቭ", "price": 230.00}, {"title_en": "1500 Saves", "title_am": "1500 ሴቭ", "price": 370.00}, {"title_en": "2000 Saves", "title_am": "2000 ሴቭ", "price": 510.00}, {"title_en": "5000 Saves", "title_am": "5000 ሴቭ", "price": 790.00}, {"title_en": "10000 Saves", "title_am": "10000 ሴቭ", "price": 980.00}]},
            "shares": {"label_am": "ሼር", "label_en": "Shares", "packages": [{"title_en": "300 Shares", "title_am": "300 ሼር", "price": 72.00}, {"title_en": "500 Shares", "title_am": "500 ሼር", "price": 98.00}, {"title_en": "1000 Shares", "title_am": "1000 ሼር", "price": 142.00}, {"title_en": "2000 Shares", "title_am": "2000 ሼር", "price": 290.00}, {"title_en": "5000 Shares", "title_am": "5000 ሼር", "price": 470.00}, {"title_en": "10000 Shares", "title_am": "10000 ሼር", "price": 920.00}, {"title_en": "20000 Shares", "title_am": "20000 ሼር", "price": 1290.50}]}
        }
    },
    "youtube": {
        "label_am": "YouTube ❤️", "label_en": "YouTube ❤️",
        "sub": {
            "views": {"label_am": "እይታ", "label_en": "Views", "packages": [{"title_en": "1000 Views", "title_am": "1000 እይታ", "price": 350.00}, {"title_en": "2000 Views", "title_am": "2000 እይታ", "price": 698.00}, {"title_en": "3000 Views", "title_am": "3000 እይታ", "price": 1050.00}, {"title_en": "5000 Views", "title_am": "5000 እይታ", "price": 1486.25}, {"title_en": "10000 Views", "title_am": "10000 እይታ", "price": 2515.00}, {"title_en": "20000 Views", "title_am": "20000 እይታ", "price": 4975.00}]},
            "subs": {"label_am": "ሰብስክራይበር", "label_en": "Subscribers", "packages": [{"title_en": "100 Subscribers", "title_am": "100 ሰብስክራይበር", "price": 499.00}, {"title_en": "500 Subscribers", "title_am": "500 ሰብስክራይበር", "price": 2399.00}, {"title_en": "1000 Subscribers", "title_am": "1000 ሰብስክራይበር", "price": 4749.00}, {"title_en": "2000 Subscribers", "title_am": "2000 ሰብስክራይበር", "price": 9399.00}, {"title_en": "10000 Subscribers", "title_am": "10000 ሰብስክራይበር", "price": 39999.00}, {"title_en": "20000 Subscribers", "title_am": "20000 ሰብስክራይበር", "price": 77999.00}]},
            "shares": {"label_am": "ሼር", "label_en": "Shares", "packages": [{"title_en": "1000 Shares", "title_am": "1000 ሼር", "price": 370.00}, {"title_en": "2000 Shares", "title_am": "2000 ሼር", "price": 741.00}, {"title_en": "3000 Shares", "title_am": "3000 ሼር", "price": 998.00}, {"title_en": "5000 Shares", "title_am": "5000 ሼር", "price": 1572.00}, {"title_en": "10,000 Shares", "title_am": "10,000 ሼር", "price": 2965.00}, {"title_en": "20,000 Shares", "title_am": "20,000 ሼር", "price": 5925.00}]},
            "likes": {"label_am": "ላይክ", "label_en": "Likes", "packages": [{"title_en": "500 Likes", "title_am": "500 ላይክ", "price": 211.00}, {"title_en": "1,000 Likes", "title_am": "1,000 ላይክ", "price": 389.00}, {"title_en": "3,000 Likes", "title_am": "3,000 ላይክ", "price": 1025.00}, {"title_en": "5,000 Likes", "title_am": "5,000 ላይክ", "price": 1623.00}, {"title_en": "10,000 Likes", "title_am": "10,000 ላይክ", "price": 2998.00}, {"title_en": "20,000 Likes", "title_am": "20,000 ላይክ", "price": 5811.00}]}
        }
    },
    "instagram": {
        "label_am": "Instagram 💜", "label_en": "Instagram 💜",
        "sub": {
            "followers": {"label_am": "ፎሎወር", "label_en": "Followers", "packages": [{"title_en": "500 Followers", "title_am": "500 ፎሎወር", "price": 549.00}, {"title_en": "1000 Followers", "title_am": "1000 ፎሎወር", "price": 1049.00}, {"title_en": "2000 Followers", "title_am": "2000 ፎሎወር", "price": 2049.00}, {"title_en": "10000 Followers", "title_am": "10000 ፎሎወር", "price": 8499.00}, {"title_en": "20000 Followers", "title_am": "20000 ፎሎወር", "price": 15999.00}]},
            "likes": {"label_am": "ላይክ", "label_en": "Likes", "packages": [{"title_en": "300 Likes", "title_am": "300 ላይክ", "price": 116.25}, {"title_en": "500 Likes", "title_am": "500 ላይክ", "price": 155.12}, {"title_en": "1000 Likes", "title_am": "1000 ላይክ", "price": 289.00}, {"title_en": "3000 Likes", "title_am": "3000 ላይክ", "price": 388.12}, {"title_en": "5000 Likes", "title_am": "5000 ላይክ", "price": 555.00}, {"title_en": "10000 Likes", "title_am": "10000 ላይክ", "price": 1010.00}, {"title_en": "20000 Likes", "title_am": "20000 ላይክ", "price": 1622.50}, {"title_en": "30000 Likes", "title_am": "30000 ላይክ", "price": 2272.50}]},
            "views": {"label_am": "እይታ", "label_en": "Views", "packages": [{"title_en": "1000 Views", "title_am": "1000 እይታ", "price": 87.88}, {"title_en": "5000 Views", "title_am": "5000 እይታ", "price": 342.50}, {"title_en": "10000 Views", "title_am": "10000 እይታ", "price": 592.50}, {"title_en": "15000 Views", "title_am": "15000 እይታ", "price": 802.50}, {"title_en": "20000 Views", "title_am": "20000 እይታ", "price": 1010.00}, {"title_en": "30000 Views", "title_am": "30000 እይታ", "price": 1381.25}, {"title_en": "50000 Views", "title_am": "50000 እይታ", "price": 2110.00}]}
        }
    },
    "facebook": {
        "label_am": "Facebook 👍", "label_en": "Facebook 👍",
        "sub": {
            "post_likes": {"label_am": "የፖስት ላይክ", "label_en": "Post Likes", "packages": [{"title_en": "500 Post Likes", "title_am": "500 ፖስት ላይክ", "price": 175.00}, {"title_en": "1000 Post Likes", "title_am": "1000 ፖስት ላይክ", "price": 338.00}, {"title_en": "3000 Post Likes", "title_am": "3000 ፖስት ላይክ", "price": 670.00}, {"title_en": "5000 Post Likes", "title_am": "5000 ፖስት ላይክ", "price": 1260.00}, {"title_en": "10000 Post Likes", "title_am": "10000 ፖስት ላይክ", "price": 2350.00}, {"title_en": "20000 Post Likes", "title_am": "20000 ፖስት ላይክ", "price": 4100.00}, {"title_en": "1001 Post Likes", "title_am": "1001 ፖስት ላይክ", "price": 252.00}]},
            "page_likes_and_followers": {"label_am": "የገጽ ላይክ + ፎሎወር", "label_en": "Page Likes + Follower's", "packages": [{"title_en": "500 Page Likes + Follower's", "title_am": "500 የገጽ ላይክ + ፎሎወር", "price": 731.25}, {"title_en": "1000 Page Likes + Follower's", "title_am": "1000 የገጽ ላይክ + ፎሎወር", "price": 903.75}, {"title_en": "3000 Page Likes + Follower's", "title_am": "3000 የገጽ ላይክ + ፎሎወር", "price": 2572.50}, {"title_en": "5000 Page Likes + Follower's", "title_am": "5000 የገጽ ላይክ + ፎሎወር", "price": 3980.00}, {"title_en": "10000 Page Likes + Follower's", "title_am": "10000 የገጽ ላይክ + ፎሎወር", "price": 8825.25}, {"title_en": "20000 Page Likes + Follower's", "title_am": "20000 የገጽ ላይክ + ፎሎወር", "price": 15351.25}]},
            "followers": {"label_am": "ፎሎወር", "label_en": "Followers", "packages": [{"title_en": "500 Followers", "title_am": "500 ፎሎወር", "price": 635.00}, {"title_en": "1000 Followers", "title_am": "1000 ፎሎወር", "price": 887.50}, {"title_en": "3000 Followers", "title_am": "3000 ፎሎወር", "price": 2237.50}, {"title_en": "5000 Followers", "title_am": "5000 ፎሎወር", "price": 4120.75}, {"title_en": "10000 Followers", "title_am": "10000 ፎሎወር", "price": 7960.00}, {"title_en": "15000 Followers", "title_am": "15000 ፎሎወር", "price": 11100.00}, {"title_en": "20000 Followers", "title_am": "20000 ፎሎወር", "price": 14800.00}, {"title_en": "55000 Followers", "title_am": "55000 ፎሎወር", "price": 36609.00}]}
        }
    },
    "telegram": {
        "label_am": "Telegram ✈️", "label_en": "Telegram ✈️",
        "sub": {
            "reactions": {"label_am": "የፖስት ላይክ", "label_en": "Reactions", "packages": [{"title_en": "500 Reactions", "title_am": "500 ምላሾች", "price": 48.00}, {"title_en": "1000 Reactions", "title_am": "1000 ምላሾች", "price": 75.00}, {"title_en": "3000 Reactions", "title_am": "3000 ምላሾች", "price": 206.25}, {"title_en": "5000 Reactions", "title_am": "5000 ምላሾች", "price": 308.75}, {"title_en": "10000 Reactions", "title_am": "10000 ምላሾች", "price": 561.25}]},
            "members": {"label_am": "አባላት ልመጨመር", "label_en": "Members", "packages": [{"title_en": "500 Members", "title_am": "500 አባላት", "price": 506.25}, {"title_en": "1000 Members", "title_am": "1000 አባላት", "price": 890.00}, {"title_en": "3000 Members", "title_am": "3000 አባላት", "price": 2082.50}, {"title_en": "10000 Members", "title_am": "10000 አባላት", "price": 5847.50}, {"title_en": "20000 Members", "title_am": "20000 አባላት", "price": 10237.50}]},
            "post_views": {"label_am": "የፖስት እይታ", "label_en": "Post Views", "packages": [{"title_en": "1000 Post Views", "title_am": "1000 የፖስት እይታ", "price": 31.00}, {"title_en": "5000 Post Views", "title_am": "5000 የፖስት እይታ", "price": 125.00}, {"title_en": "10000 Post Views", "title_am": "10000 የፖስት እይታ", "price": 237.50}, {"title_en": "20000 Post Views", "title_am": "20000 የፖስት እይታ", "price": 435.00}, {"title_en": "30000 Post Views", "title_am": "30000 የፖስት እይታ", "price": 622.50}, {"title_en": "50000 Post Views", "title_am": "50000 የፖስት እይታ", "price": 997.50}, {"title_en": "100000 Post Views", "title_am": "100000 የፖስት እይታ", "price": 1817.50}]}
        }
    },
}

# ---------------- logging ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- Database setup (Hybrid DNS Resolution for IPv4/IPv6 Issues) ----------------
# This method connects by telling the driver:
# 1. "Use this IPv4 address" (hostaddr) -> Fixes Render's missing IPv6 support
# 2. "Use this Domain Name" (host) -> Fixes Supabase's SSL Certificate check

def get_db_connection():
    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set!")
        return None
    try:
        # 1. Parse the DATABASE_URL to extract credentials
        url = urllib.parse.urlparse(DATABASE_URL)
        username = url.username
        password = url.password
        database = url.path[1:] # Remove leading '/'
        port = url.port or 5432
        hostname = url.hostname

        # 2. Manually resolve the hostname to an IPv4 address
        try:
            # Forces IPv4 resolution
            ip_address = socket.gethostbyname(hostname)
            logger.info(f"Resolved {hostname} to {ip_address}")
        except Exception as dns_err:
            logger.error(f"DNS Resolution failed for {hostname}: {dns_err}")
            return None

        # 3. Connect using explicit hostaddr
        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,       # Keep the original hostname for SSL verification
            hostaddr=ip_address, # Force connection to the IPv4 address
            port=port,
            sslmode='require'
        )
        return conn
    except Exception as e:
        logger.error(f"DB Connection failed: {e}")
        return None

def init_db():
    conn = get_db_connection()
    if not conn: return
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        balance REAL DEFAULT 0,
        lang TEXT DEFAULT 'am',
        affiliate_balance REAL DEFAULT 0,
        referrer_id BIGINT DEFAULT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invited_users (
        inviter_id BIGINT,
        invited_id BIGINT UNIQUE,
        invited_username TEXT,
        invited_firstname TEXT,
        registered_at TEXT,
        PRIMARY KEY (inviter_id, invited_id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        service_key TEXT,
        subkey TEXT,
        package_title TEXT,
        price REAL,
        target TEXT,
        payment_method TEXT,
        status TEXT,
        created_at TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recharges (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount REAL,
        payment_method TEXT,
        status TEXT,
        admin_message_id BIGINT,
        created_at TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS affiliate_withdrawals (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        amount REAL,
        method TEXT,
        account_detail TEXT,
        status TEXT,
        admin_message_id BIGINT,
        created_at TEXT
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()

# Run init on startup
try:
    init_db()
except Exception as e:
    logger.error(f"Failed to init DB: {e}")


# ---------------- DB helper functions ----------------
def get_balance(user_id: int) -> float:
    conn = get_db_connection()
    if not conn: return 0.0
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=%s", (user_id, ))
    r = cursor.fetchone()
    if r: 
        bal = r[0]
        cursor.close()
        conn.close()
        return bal
    
    cursor.execute("INSERT INTO users (user_id, balance, lang) VALUES (%s, 0, 'am') ON CONFLICT (user_id) DO NOTHING", (user_id, ))
    conn.commit()
    cursor.close()
    conn.close()
    return 0.0

def add_balance(user_id: int, amount: float) -> float:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, balance) VALUES (%s, %s) 
        ON CONFLICT(user_id) 
        DO UPDATE SET balance = users.balance + EXCLUDED.balance
    """, (user_id, amount))
    conn.commit()
    cursor.close()
    conn.close()
    return get_balance(user_id)

def deduct_balance(user_id: int, amount: float) -> (bool, float):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = balance - %s WHERE user_id = %s AND balance >= %s", (amount, user_id, amount))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()
    if affected == 1: return True, get_balance(user_id)
    return False, get_balance(user_id)

def create_order(user_id: int, service_key: str, subkey: str, package_title: str, price: float, target: str, payment_method: str, status: str = "pending"):
    now = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, service_key, subkey, package_title, price, target, payment_method, status, created_at) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", (user_id, service_key, subkey, package_title, price, target, payment_method, status, now))
    oid = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return oid

def update_order_status(order_id: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
    conn.commit()
    cursor.close()
    conn.close()
    
def get_order_details(order_id: int) -> dict or None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, price, service_key, package_title, payment_method FROM orders WHERE id=%s", (order_id,))
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    if r: return {"user_id": r[0], "price": r[1], "service_key": r[2], "package_title": r[3], "payment_method": r[4]}
    return None

def create_recharge(user_id: int, amount: float, payment_method: str, status: str = "pending", admin_message_id: int = None):
    now = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO recharges (user_id, amount, payment_method, status, admin_message_id, created_at) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id", (user_id, amount, payment_method, status, admin_message_id, now))
    rid = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return rid

def update_recharge_status(recharge_id: int, status: str, admin_message_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if admin_message_id is None: cursor.execute("UPDATE recharges SET status=%s WHERE id=%s", (status, recharge_id))
    else: cursor.execute("UPDATE recharges SET status=%s, admin_message_id=%s WHERE id=%s", (status, admin_message_id, recharge_id))
    conn.commit()
    cursor.close()
    conn.close()

def _get_user_language(user_id: int) -> str:
    conn = get_db_connection()
    if not conn: return 'am'
    cursor = conn.cursor()
    cursor.execute("SELECT lang FROM users WHERE user_id=%s", (user_id,))
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    return r[0] if r else 'am'

def _set_user_language(user_id: int, lang: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET lang=%s WHERE user_id=%s", (lang, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_affiliate_balance(user_id: int) -> float:
    conn = get_db_connection()
    if not conn: return 0.0
    cursor = conn.cursor()
    cursor.execute("SELECT affiliate_balance FROM users WHERE user_id=%s", (user_id, ))
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    return r[0] if r else 0.0

def add_affiliate_balance(user_id: int, amount: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, affiliate_balance) VALUES (%s, %s) 
        ON CONFLICT(user_id) 
        DO UPDATE SET affiliate_balance = users.affiliate_balance + EXCLUDED.affiliate_balance
    """, (user_id, amount))
    conn.commit()
    cursor.close()
    conn.close()

def deduct_affiliate_balance(user_id: int, amount: float) -> (bool, float):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET affiliate_balance = affiliate_balance - %s WHERE user_id = %s AND affiliate_balance >= %s", (amount, user_id, amount))
    conn.commit()
    rows = cursor.rowcount
    cursor.close()
    conn.close()
    if rows == 1: return True, get_affiliate_balance(user_id)
    return False, get_affiliate_balance(user_id)

def get_referrer_id(user_id: int) -> int or None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT referrer_id FROM users WHERE user_id=%s", (user_id, ))
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    return r[0] if r and r[0] else None

def set_referrer_id(user_id: int, referrer_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET referrer_id=%s WHERE user_id=%s AND referrer_id IS NULL", (referrer_id, user_id))
    conn.commit()
    rows = cursor.rowcount
    cursor.close()
    return rows == 1

def record_invited_user(inviter_id: int, invited_id: int, username: str, firstname: str):
    now = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO invited_users (inviter_id, invited_id, invited_username, invited_firstname, registered_at) VALUES (%s, %s, %s, %s, %s)", (inviter_id, invited_id, username, firstname, now))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except psycopg2.IntegrityError: 
        cursor.close()
        conn.close()
        return False

def get_invited_users(user_id: int) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT invited_id, invited_username, invited_firstname FROM invited_users WHERE inviter_id=%s", (user_id,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

def get_all_user_ids() -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    res = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return res

def create_withdrawal_request(user_id: int, amount: float, method: str, account_detail: str) -> int:
    now = datetime.utcnow().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO affiliate_withdrawals (user_id, amount, method, account_detail, status, created_at) VALUES (%s, %s, %s, %s, 'pending', %s) RETURNING id", (user_id, amount, method, account_detail, now))
    wid = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    conn.close()
    return wid

def update_withdrawal_status_and_admin_msg(withdrawal_id: int, status: str, admin_message_id: int = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if admin_message_id is None: cursor.execute("UPDATE affiliate_withdrawals SET status=%s WHERE id=%s", (status, withdrawal_id))
    else: cursor.execute("UPDATE affiliate_withdrawals SET status=%s, admin_message_id=%s WHERE id=%s", (status, admin_message_id, withdrawal_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_withdrawal_details(withdrawal_id: int) -> dict or None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, method, account_detail, status FROM affiliate_withdrawals WHERE id=%s", (withdrawal_id,))
    r = cursor.fetchone()
    cursor.close()
    conn.close()
    if r: return {"user_id": r[0], "amount": r[1], "method": r[2], "account_detail": r[3], "status": r[4]}
    return None

def get_withdrawal_history(user_id: int) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount, method, account_detail, status, created_at FROM affiliate_withdrawals WHERE user_id=%s ORDER BY id DESC", (user_id,))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

def get_last_orders(user_id: int, limit: int = 10) -> list:
    conn = get_db_connection()
    if not conn: return []
    cursor = conn.cursor()
    cursor.execute("SELECT id, package_title, price, status, created_at FROM orders WHERE user_id=%s ORDER BY id DESC LIMIT %s", (user_id, limit))
    res = cursor.fetchall()
    cursor.close()
    conn.close()
    return res

def _get_commission_rate(price: float) -> float:
    sorted_tiers = sorted(TIERED_COMMISSION.keys(), reverse=True)
    for floor_price in sorted_tiers:
        if price >= floor_price: return TIERED_COMMISSION[floor_price]
    return 0.0

def t(lang, en_text, am_text):
    return am_text if lang == "am" else en_text

# ---------------- Global state and Helper Functions ----------------
async def _send_or_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup: InlineKeyboardMarkup = None, is_main_menu: bool = False, is_video_menu: bool = False, photo: str = None, disable_web_preview: bool = False):
    chat_id = update.effective_chat.id
    last_bot_message_id = context.user_data.get('last_bot_message_id')
    
    async def _clear_keyboard(update, context, message_id=None):
        if message_id is None: message_id = context.user_data.get('last_bot_message_id')
        if message_id:
            try:
                await context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
                if context.user_data.get('last_bot_message_id') == message_id: context.user_data.pop('last_bot_message_id', None)
            except Exception: pass

    if is_main_menu or not last_bot_message_id or update.callback_query is None:
        await _clear_keyboard(update, context) 
        sent_message = None
        should_send_text_fallback = True 

        if is_video_menu and WELCOME_VIDEO:
            if WELCOME_MEDIA_CACHE["id"]:
                try:
                    if WELCOME_MEDIA_CACHE["type"] == "video": sent_message = await context.bot.send_video(chat_id=chat_id, video=WELCOME_MEDIA_CACHE["id"], caption=text, reply_markup=reply_markup)
                    else: sent_message = await context.bot.send_photo(chat_id=chat_id, photo=WELCOME_MEDIA_CACHE["id"], caption=text, reply_markup=reply_markup)
                    should_send_text_fallback = False
                except Exception: WELCOME_MEDIA_CACHE["id"] = None

            if should_send_text_fallback and os.path.isfile(WELCOME_VIDEO):
                should_send_text_fallback = False 
                try:
                    file_ext = os.path.splitext(WELCOME_VIDEO)[1].lower()
                    media = open(WELCOME_VIDEO, "rb")
                    if file_ext in ('.mp4', '.mov', '.avi'): 
                        sent_message = await context.bot.send_video(chat_id=chat_id, video=media, caption=text, reply_markup=reply_markup)
                        if sent_message and sent_message.video: WELCOME_MEDIA_CACHE.update({"id": sent_message.video.file_id, "type": "video"})
                    elif file_ext in ('.jpg', '.jpeg', '.png'): 
                        sent_message = await context.bot.send_photo(chat_id=chat_id, photo=media, caption=text, reply_markup=reply_markup)
                        if sent_message and sent_message.photo: WELCOME_MEDIA_CACHE.update({"id": sent_message.photo[-1].file_id, "type": "photo"})
                    media.close()
                except Exception: pass
            elif should_send_text_fallback and not os.path.isfile(WELCOME_VIDEO): should_send_text_fallback = True
        elif photo: 
             try:
                sent_message = await context.bot.send_photo(chat_id=chat_id, photo=photo, caption=text, reply_markup=reply_markup)
                should_send_text_fallback = False
             except Exception: pass

        if should_send_text_fallback:
            try:
                sent_message = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, disable_web_page_preview=disable_web_preview)
            except Exception: pass
        if sent_message: context.user_data['last_bot_message_id'] = sent_message.message_id
            
    else: 
        if update.callback_query and update.callback_query.message.message_id == last_bot_message_id:
            try:
                if update.callback_query.message.video or update.callback_query.message.photo: await update.callback_query.edit_message_caption(caption=text, reply_markup=reply_markup)
                else: await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, disable_web_page_preview=disable_web_preview)
            except Exception: await _send_or_edit_message(update, context, text, reply_markup, is_main_menu=True, is_video_menu=is_video_menu)
        else:
            if update.callback_query: await _clear_keyboard(update, context, update.callback_query.message.message_id)
            await _send_or_edit_message(update, context, text, reply_markup, is_main_menu=True, is_video_menu=is_video_menu)

async def _get_balance_and_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    lang = _get_user_language(user_id)
    context.user_data['lang'] = lang
    return balance, lang

# ---------------- START handler ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance, lang = await _get_balance_and_lang(update, context)

    if context.args:
        try:
            arg = context.args[0]
            if arg.startswith("r_"):
                referrer_id = int(arg[2:])
                if referrer_id != user.id:
                    if set_referrer_id(user.id, referrer_id):
                        if record_invited_user(referrer_id, user.id, user.username or "N/A", user.first_name):
                            try: await context.bot.send_message(chat_id=referrer_id, text=t(_get_user_language(referrer_id), f"🎉 New referral! @{user.username or user.first_name} (ID: {user.id}) joined using your link.", f"🎉 አዲስ ተጋባዥ! @{user.username or user.first_name} (ID: {user.id}) የእርስዎን ሊንክ ተጠቅሞ ተመዝግቧል::"))
                            except Exception: pass
        except (ValueError, IndexError): pass

    caption = t(lang, f"""Hello 👋 Welcome to Elevate Promotion advertising agency! Increase your recognition by using Elevate's advertising technology to buy followers, likes, views on YouTube, Facebook, Instagram, TikTok, 
and by using other services! For more information, call 0955974297 or send a message to @Elevatesupport.

Your balance: {balance:.2f} ETB
Choose a service below.""", f"""ሰላም 👋  እንኳን ወደ ኢሊቬት ፕሮሞሽን  የ ማስታወቅያ ድርጅት በ ሰላም መጡ ! የ ኢሊቫትን የማስተወቅያ ቴክኖሎጂ በመጠቀም በ Youtube, Facebook , Instagram , Tiktok  ላይ ተከታይ ፣ ላይክ ፣ ቪው በመግዛት 
 እና ሌሎች አገልግሎቶችን በመጠቀም እውቅናዎን ያሳድጉ! ለበለጠ መረጃ በ 0955974297 ይደውሉ ወይም  @Elevatesupport ላይ መልክት ይላኩልን።

ቀሪ ብር: {balance:.2f}
እባክዎን ከዚህ አገልግሎት ይምረጡ።""")

    buttons = []
    row = []
    for key, data in SERVICES.items():
        label = data["label_am"] if lang == "am" else data["label_en"]
        row.append(InlineKeyboardButton(label, callback_data=f"svc|{key}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    
    buttons.append([InlineKeyboardButton(t(lang, "Balance", "ቀሪ ሂሳብ"), callback_data="cmd|balance"), InlineKeyboardButton(t(lang, "Recharge", "ገንዘብ ማስገቢያ"), callback_data="cmd|recharge")])
    buttons.append([InlineKeyboardButton(t(lang, "Affiliate Program", "ሰው በመጋበዝ ገንዘብ ይስሩ"), callback_data="cmd|referral")])
    buttons.append([InlineKeyboardButton(t(lang, "Language", "ቋንቋ"), callback_data="cmd|language")])

    await _send_or_edit_message(update, context, caption, InlineKeyboardMarkup(buttons), is_main_menu=True, is_video_menu=True)

# ---------------- Callback handler ----------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = query.from_user
    lang = _get_user_language(user.id)
    context.user_data['lang'] = lang
    parts = data.split("|")
    prefix = parts[0]

    if prefix == "recharge_amt":
        amount = float(parts[1])
        context.application.bot_data[f"recharge_pending:{user.id}"] = {"amount": amount, "method": None}
        kb = []
        for m in PAYMENT_INFO.keys():
            kb.append([InlineKeyboardButton(m.capitalize(), callback_data=f"recharge_pay|{m}")])
        kb.append([InlineKeyboardButton(t(lang, "Cancel", "ሰርዝ"), callback_data="cmd|recharge")])
        await _send_or_edit_message(update, context, t(lang, f"Recharging {amount:.2f} ETB.\nChoose payment method:", f"{amount:.2f} ብር ለመሙላት።\nየክፍያ መንገድ ይምረጡ:"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
        return

    if prefix == "recharge_custom":
        context.user_data["awaiting_custom_recharge_amount"] = True
        await _send_or_edit_message(update, context, t(lang, "Please enter the amount you want to recharge (Numbers only):", "እባክዎ መሙላት የሚፈልጉትን መጠን ያስገቡ (ቁጥር ብቻ):"), is_main_menu=True)
        return

    if prefix == "recharge_pay":
        method = parts[1]
        acc = PAYMENT_INFO.get(method, "Not available")
        pending = context.application.bot_data.get(f"recharge_pending:{user.id}")
        if pending:
            pending["method"] = method
            amount = pending["amount"]
            await _send_or_edit_message(update, context, t(lang, f"Please send {amount:.2f} ETB to: {acc}\nThen send a photo screenshot.", f"እባክዎ {amount:.2f} ብር ወደ {acc} ይላኩ።\nከዚያ ስክሪንሾት ይላኩ።"), is_main_menu=True)
        return

    if prefix == "svc":
        if len(parts) < 2: return
        service_key = parts[1]
        context.user_data["current_service"] = service_key
        sub = SERVICES[service_key]["sub"]
        buttons = []
        row = []
        for subkey, subdata in sub.items():
            lbl = subdata["label_am"] if lang == "am" else subdata["label_en"]
            row.append(InlineKeyboardButton(lbl, callback_data=f"sub|{service_key}|{subkey}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row: buttons.append(row)
        buttons.append([InlineKeyboardButton(t(lang, "Back", "ተመለስ"), callback_data="back|")])
        await _send_or_edit_message(update, context, t(lang, "Choose a service:", "እባክዎ አገልግሎት ይምረጡ።"), reply_markup=InlineKeyboardMarkup(buttons))
        return

    if prefix == "sub":
        _, service_key, subkey = parts
        context.user_data["current_sub"] = subkey
        packages = SERVICES[service_key]["sub"][subkey]["packages"]
        buttons = []
        for idx, pkg in enumerate(packages):
            if isinstance(pkg, dict):
                title = pkg["title_am"] if lang == "am" else pkg["title_en"]
                price = pkg["price"]
            else: title, price = pkg
            btn_text = f"{title} — {price:.2f} ETB"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"pkg|{service_key}|{subkey}|{idx}")])
        buttons.append([InlineKeyboardButton(t(lang, "Back", "ተመለስ"), callback_data=f"svc|{service_key}")])
        await _send_or_edit_message(update, context, t(lang, "Choose a package:", "እባክዎ ጥንካሬ ይምረጡ።"), reply_markup=InlineKeyboardMarkup(buttons))
        return

    if prefix == "pkg":
        _, service_key, subkey, idx_str = parts
        idx = int(idx_str)
        packages = SERVICES[service_key]["sub"][subkey]["packages"]
        if idx < 0 or idx >= len(packages): return
        pkg = packages[idx]
        title = pkg["title_am"] if lang == "am" else pkg["title_en"]
        price = pkg["price"]
        
        order = {"user_id": user.id, "service_key": service_key, "subkey": subkey, "package_title": title, "price": price, "lang": lang}
        context.user_data.pop("awaiting_order_confirmation", None)
        context.user_data.pop("awaiting_link_for_order", None)
        context.application.bot_data[f"order:{user.id}"] = order
        
        prompt_en, prompt_am = "", ""
        if service_key == "tiktok":
            if subkey in ("likes", "views", "saves", "shares"): prompt_en, prompt_am = "Send your TikTok video/post link (URL):", "እባክዎ የእርሶን የቲክቶክ ቪድዮ/ፖስት ሊንክ Copy በማረግ ያስገቡ:"
            elif subkey == "followers": prompt_en, prompt_am = "Send your TikTok username (e.g., @Elevate):", "እባክዎ የ ቲክቶኮን username ይላኩ ( ለምሳሌ ፡ @Elevate )"
        elif service_key == "youtube":
            if subkey in ("views", "shares", "likes"): prompt_en, prompt_am = "Send your YouTube video link (URL):", "እባክዎ የእርሶን የዩቲዩብ ቪድዮ ሊንክ Copy በማረግ ያስገቡ:"
            elif subkey == "subs": prompt_en, prompt_am = "Send your YouTube channel link (URL):", "እባክዎ የዩቲዩብ ቻናል ሊንክዎን ይላኩ።"
        elif service_key == "instagram":
            if subkey in ("likes", "views"): prompt_en, prompt_am = "Send your Instagram post/reel link (URL):", "እባክዎ የእርሶን የኢንስታግራም ፖስት/ሪል ሊንክ Copy በማረግ ያስገቡ:"
            elif subkey == "followers": prompt_en, prompt_am = "Send your Instagram username or profile link (e.g., @Elevate):", "እባክዎ የ Instagram username or profile link (e.g., @Elevate) ይላኩ።"
        elif service_key == "facebook":
            if subkey == "post_likes": prompt_en, prompt_am = "Send your Facebook post link (URL):", "እባክዎ የእርሶን የፌስቡክ ፖስት ሊንክ Copy በማረግ ያስገቡ:"
            elif subkey in ("page_likes_and_followers", "followers"): prompt_en, prompt_am = "Send your Facebook Page/Profile username or link (URL):", "እባክዎ የፌስቡክ ገጽ/ፕሮፋይል ዩዘርኔም ወይም ሊንክ ይላኩ።"
        elif service_key == "telegram":
            if subkey in ("reactions", "post_views"): prompt_en, prompt_am = "Send your Telegram post link (URL):", "እባክዎ የእርሶን የቴሌግራም ፖስት ሊንክ Copy በማረግ ያስገቡ:"
            elif subkey == "members": prompt_en, prompt_am = "Send your Telegram channel/group username (without @):", "እባክዎ የቴሌግራም ቻናል/ግሩፕ ዩዘርኔም ይላኩ (without @)።"
        else: prompt_en, prompt_am = "Send the link (URL) or username for your selected service:", "እባክዎ ለተመረጠው አገልግሎት ሊንኩን (URL) ወይም ዩዘርኔም ይላኩ።"

        await _send_or_edit_message(update, context, t(lang, f"You selected: {title} — {price:.2f} ETB\n\n{prompt_en}", f"የተመረጠ፦ {title} — {price:.2f} ብር\n\n{prompt_am}"), is_main_menu=True)
        context.user_data["awaiting_link_for_order"] = True
        return

    if prefix == "confirm_order":
        action = parts[1]
        order = context.application.bot_data.get(f"order:{user.id}")
        if not order:
            await _send_or_edit_message(update, context, t(lang, "No order data found. Please start over.", "የተመረጠ ትዕዛዝ የለም። እባክዎ እንደገና ይጀምሩ።"), is_main_menu=True)
            return
        if action == "change":
            context.user_data["awaiting_link_for_order"] = True
            await _send_or_edit_message(update, context, t(lang, f"You chose to change the link. Please send the correct link/username for '{order['package_title']}' — {order['price']:.2f} ETB.", f"ሊንኩን ለመቀየር መርጠዋል። እባክዎ ትክክለኛውን ሊንክ/ዩዘርኔም ለ '{order['package_title']}' — {order['price']:.2f} ብር እንደገና ይላኩ።"), is_main_menu=True)
            return
        kb = [[InlineKeyboardButton(t(lang, "Pay with balance", "በቀሪ ሂሳብ ይክፈሉ"), callback_data="pay|balance")]]
        for m in PAYMENT_INFO.keys(): kb.append([InlineKeyboardButton(m.capitalize(), callback_data=f"pay|{m}")])
        kb.append([InlineKeyboardButton(t(lang, "Cancel Order", "ትዕዛዙን ሰርዝ"), callback_data="back|")])
        await _send_or_edit_message(update, context, t(lang, f"You are ordering '{order['package_title']}' for {order['price']:.2f} ETB to the target: *{order['target']}*.\n\nChoose payment method:", f"'{order['package_title']}' አገልግሎት በ {order['price']:.2f} ብር ለ *{order['target']}* እያዘዙ ነው።\n\nእባክዎ የክፍያ ዘዴ ይምረጡ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
        return

    if prefix == "pay":
        if len(parts) < 2: return
        method = parts[1]
        user_id = user.id
        order = context.application.bot_data.get(f"order:{user.id}")
        if not order:
            await _send_or_edit_message(update, context, t(lang, "No order found. Use /start to begin.", "ትዕዛዝ አልተገኘም። /start ይግቡም።"), is_main_menu=True)
            return
        
        if method == "balance":
            price = order["price"]
            ok, new_bal = deduct_balance(user_id, price)
            if ok:
                order_id = create_order(user_id, order["service_key"], order["subkey"], order["package_title"], price, order.get("target", ""), "balance", status="pending_approval") 
                context.application.bot_data.pop(f"order:{user_id}", None)
                caption = f"🔔 Order payment (Balance)\nUser: @{user.username or user.first_name} (ID: {user_id})\nOrder ID: {order_id}\nService: {SERVICES[order['service_key']]['label_en']} - {order['package_title']}\nTarget: {order.get('target','N/A')}\nPrice: {order['price']:.2f} ETB\nMethod: BALANCE"
                admin_kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"admin|approve_order|{order_id}|{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin|reject_order|{order_id}|{user_id}")]])
                try: await context.bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=admin_kb)
                except Exception: pass
                await _send_or_edit_message(update, context, t(lang, f"✅ Payment successful. {price:.2f} ETB deducted from your balance.\nRemaining: {new_bal:.2f} ETB\nYour order id: {order_id}\n\nYour order is now waiting for admin approval.", f"✅ ክፍያ ተከፍሏል። {price:.2f} ብር ከቀሪ ሂሳብዎ ተቀናቷል።\nቀሪ: {new_bal:.2f} ብር\nትዕዛዝ መለያ: {order_id}\n\nትዕዛዝዎ የአስተዳዳሪ ማረጋገጫ በመጠበቅ ላይ ነው።"), is_main_menu=True)
            else:
                await _send_or_edit_message(update, context, t(lang, f"❌ Insufficient balance ({new_bal:.2f} ETB). Please recharge or choose another payment method.", f"❌ በቂ ቀሪ ሂሳብ የለም ({new_bal:.2f} ብር). እባክዎ ይክፈሉ ወይም ሌላ ዘዴ ይምረጡ።"), is_main_menu=True)
            return
        else:
            acc = PAYMENT_INFO.get(method, "Not available")
            context.application.bot_data[f"order:{user.id}"]["payment_method"] = method
            ord = context.application.bot_data.get(f"order:{user_id}")
            order_id = create_order(user_id, ord["service_key"], ord["subkey"], ord["package_title"], ord["price"], ord.get("target", ""), method, status="pending_payment")
            context.application.bot_data[f"order:{user_id}"]["order_id"] = order_id
            await _send_or_edit_message(update, context, t(lang, f"Please send payment to: {acc}\nAfter payment, upload your screenshot (photo) here.\nOrder ID: {order_id}", f"እባክዎ ክፍያዎን ወደ፦ {acc} ይከፍሉ።\nከዚያ በኋላ የክፍያ ስክሪንሾት ይላኩ።\nየትዕዛዝ መለያ: {order_id}"), is_main_menu=True)
            return

    if prefix == "admin":
        if len(parts) < 4: return
        action = parts[1]
        obj_id = int(parts[2])
        target_user_id = int(parts[3])
        if query.from_user.id != ADMIN_ID: return
        user_lang_for_notification = _get_user_language(target_user_id)

        async def edit_admin_msg(text_append, kb=None):
            if query.message.caption: 
                await query.edit_message_caption(caption=query.message.caption + text_append, reply_markup=kb)
            else: 
                await query.edit_message_text(text=query.message.text + text_append, reply_markup=kb)

        if action == "approve_order":
            order_details = get_order_details(obj_id)
            if not order_details: return
            update_order_status(obj_id, "processing")
            
            referrer_id = get_referrer_id(target_user_id)
            if referrer_id:
                rate = _get_commission_rate(order_details['price'])
                commission = order_details['price'] * rate
                if commission > 0:
                    add_affiliate_balance(referrer_id, commission)
                    try: await context.bot.send_message(chat_id=referrer_id, text=t(_get_user_language(referrer_id), f"💰 Commission earned: {commission:.2f} ETB ({rate*100:.2f}% of purchase price) from an approved order by your referral (Order ID: {obj_id}).\nYour affiliate balance is now {get_affiliate_balance(referrer_id):.2f} ETB.", f"💰 አዲስ ኮሚሽን ገቢ ተደረገ: {commission:.2f} ብር (ከጠቅላላ ዋጋ {rate*100:.2f}%) ከርስዎ ተጋባዥ በተፈቀደ ትዕዛዝ (ID: {obj_id}) ተገኝቷል። አጠቃላይ ኮሚሽንዎ {get_affiliate_balance(referrer_id):.2f} ብር ነው።"))
                    except Exception: pass
            
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, "✅ Payment Accepted. Your order is now PENDING/PROCESSING.", "✅ ክፍያ ተቀባይነት አግኝቷል። ትዕዛዝዎ በመሰራት ላይ ነው።"))
            except Exception: pass
            
            new_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Job Done / Completed", callback_data=f"admin|complete_order|{obj_id}|{target_user_id}")],
                [InlineKeyboardButton("❌ Cancel & Refund", callback_data=f"admin|refund_processing_order|{obj_id}|{target_user_id}")]
            ])
            await edit_admin_msg("\n\n⚠️ PAYMENT APPROVED. STATUS: PROCESSING.", new_kb)
            return

        if action == "complete_order":
            update_order_status(obj_id, "completed")
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, "🎉 Congratulations! Your order has been completed.", "🎉 እንኳን ደስ አለዎት! ትዕዛዝዎ ተጠናቅቋል።"))
            except Exception: pass
            await edit_admin_msg("\n\n✅ JOB COMPLETED.", None)
            return

        if action == "refund_processing_order":
            order_details = get_order_details(obj_id)
            if not order_details: return
            add_balance(target_user_id, order_details['price'])
            update_order_status(obj_id, "cancelled")
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, f"⚠️ Your order has been cancelled. {order_details['price']:.2f} ETB has been refunded to your bot balance. Please check your account.", f"⚠️ ትዕዛዝዎ ተሰርዟል። {order_details['price']:.2f} ብር ወደ ቦት ሂሳብዎ ተመልሷል። እባክዎ ሂሳብዎን ያረጋግጡ።"))
            except Exception: pass
            await edit_admin_msg("\n\n❌ CANCELED & REFUNDED.", None)
            return

        if action == "reject_order":
            order_details = get_order_details(obj_id)
            refund_msg = ""
            if order_details and order_details.get("payment_method") == "balance":
                add_balance(target_user_id, order_details['price'])
                refund_msg = t(user_lang_for_notification, f"\n\n{order_details['price']:.2f} ETB has been refunded to your balance.", f"\n\n{order_details['price']:.2f} ብር ወደ ቀሪ ሂሳብዎ ተመልሷል።")
            update_order_status(obj_id, "rejected")
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, "❌ Your order was rejected. Please try again or contact admin.", "❌ ትዕዛዝዎ አልተፈቀደም። እባክዎ ደግመው ይሞክሩ።") + refund_msg)
            except Exception: pass
            await edit_admin_msg("\n\n❌ Rejected by admin.", None)
            return
        
        if action == "approve_recharge":
            recharge_id = obj_id
            # Re-fetch is needed to get amount
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT amount FROM recharges WHERE id=%s", (recharge_id,))
            r = cur.fetchone()
            cur.close()
            conn.close()
            if not r: return
            r_amount = r[0]
            
            add_balance(target_user_id, r_amount)
            update_recharge_status(recharge_id, "approved")
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, f"✅ Your recharge of {r_amount:.2f} ETB has been approved and added to your balance.", f"✅ ክፍያዎት ተፈቅዷል። {r_amount:.2f} ብር በቀሪ ሂሳብዎ ታክሏል።"))
            except Exception: pass
            await edit_admin_msg(f"\n\n✅ Recharge approved ({r_amount:.2f})", None)
            return

        if action == "reject_recharge":
            update_recharge_status(obj_id, "rejected")
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, "❌ Your recharge was rejected. Please try again or contact admin.", "❌ ክፍያዎት አልተፈቀደም። እባክዎ ሌላ ዘዴ ይሞክሩ።"))
            except Exception: pass
            await edit_admin_msg("\n\n❌ Recharge rejected", None)
            return

    if prefix == "cmd":
        if len(parts) < 2: return
        cmd = parts[1]
        if cmd == "balance":
            bal = get_balance(user.id)
            await _send_or_edit_message(update, context, t(lang, f"Your balance: {bal:.2f} ETB", f"ቀሪ ሂሳብ: {bal:.2f} ብር"), is_main_menu=True)
            return
        if cmd == "recharge":
            kb = [[InlineKeyboardButton("200 ETB", callback_data="recharge_amt|200")], [InlineKeyboardButton("500 ETB", callback_data="recharge_amt|500")], [InlineKeyboardButton("1000 ETB", callback_data="recharge_amt|1000")], [InlineKeyboardButton(t(lang, "Custom amount", "የራስዎ መጠን"), callback_data="recharge_custom|")], [InlineKeyboardButton(t(lang, "Back", "ተመለስ"), callback_data="back|")]]
            await _send_or_edit_message(update, context, t(lang, "Choose amount to recharge:", "እባክዎ መጠን ይምረጡ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
            return
        if cmd == "language":
            kb = [[InlineKeyboardButton("አማርኛ", callback_data="lang|am"), InlineKeyboardButton("English", callback_data="lang|en")]]
            await _send_or_edit_message(update, context, t(lang, "Choose language:", "ቋንቋ ይምረጡ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
            return
        if cmd == "referral":
            aff_bal = get_affiliate_balance(user.id)
            bot_username = context.bot.username if context.bot.username else "ElevatePromotionBot"
            invite_link = f"https://t.me/{bot_username}?start=r_{user.id}"
            invited_users = get_invited_users(user.id)
            invited_list_am, invited_list_en = "አንድም ተጋባዥ የለዎትም።", "You have not invited anyone yet."
            if invited_users:
                invited_list_en, invited_list_am = "Invited Users:\n", "የጋበዟቸው ተጠቃሚዎች:\n"
                for invited_id, invited_username, invited_firstname in invited_users:
                    display_name = f"@{invited_username}" if invited_username != "N/A" else invited_firstname
                    invited_list_en += f"• {display_name} (ID: {invited_id})\n"
                    invited_list_am += f"• {display_name} (ID: {invited_id})\n"
            kb = [[InlineKeyboardButton(t(lang, "Withdraw Commission", "ኮሚሽን ማውጫ"), callback_data="affiliate|withdraw"), InlineKeyboardButton(t(lang, "History", "ታሪክ"), callback_data="cmd|referral_history")], [InlineKeyboardButton(t(lang, "Share Invite Link", "የመጋበዣ ሊንክ ላክ"), url=f"https://t.me/share/url?url={invite_link}&text={t(lang, 'Check out this bot!', 'ይህን ቦት ይመልከቱ!')}")], [InlineKeyboardButton(t(lang, "Back", "ተመለስ"), callback_data="back|")]]
            message_text = t(lang, f"*💰 Affiliate Program*\nInvite people and earn a commission every time they buy a package and the order is approved!\n\n*Your Affiliate Balance:* {aff_bal:.2f} ETB\n*Your Invite Link:*\n`{invite_link}`\n(Tap the link above to copy the text, or use the 'Share' button below.)\n\n{invited_list_en}", f"*💰 ሰው በመጋበዝ ብር ይሰብስቡ*\nሰዎችን በመጋበዝ እና ፓኬጅ በገዙ ቁጥር ኮሚሽን ያገኛሉ!\n\n*የኮሚሽን ቀሪ ሂሳብ:* {aff_bal:.2f} ብር\n*የእርሶ መጋበዣ ሊንክ:*\n`{invite_link}`\n(ጽሑፉን ለመቅዳት ሊንኩን ይንኩ፣ ወይም ከታች ያለውን 'ላክ' የሚለውን ቁልፍ ይጠቀሙ።)\n\n{invited_list_am}")
            await _send_or_edit_message(update, context, message_text, reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
            return
        if cmd == "referral_history":
            history = get_withdrawal_history(user.id)
            if not history:
                message_text = t(lang, "You have no withdrawal history yet.", "እስካሁን ምንም የማውጣት ታሪክ የለዎትም።")
            else:
                message_text = t(lang, "*Your Withdrawal History (Latest First):*\n", "*የማውጣት ታሪክዎ (የቅርብ ጊዜው መጀመሪያ):*\n")
                status_map = {"pending": t(lang, "PENDING ⏳", "በመጠባበቅ ላይ ⏳"), "approved": t(lang, "SUCCESSFUL ✅", "ተሳክቷል ✅"), "rejected": t(lang, "REJECTED ❌", "ተቀባይነት አላገኘም ❌")}
                for wid, amount, method, detail, status, created_at_str in history:
                    try:
                        dt_utc = datetime.fromisoformat(created_at_str)
                        dt_local = pytz.utc.localize(dt_utc).astimezone(pytz.timezone('Africa/Nairobi')).strftime('%Y-%m-%d %H:%M')
                    except Exception: dt_local = created_at_str.split('T')[0]
                    status_lbl = status_map.get(status, status.upper())
                    message_text += t(lang, f"• *ID {wid}*: {amount:.2f} ETB to {method.upper()} ({status_lbl}) on {dt_local}", f"• *ID {wid}*: {amount:.2f} ብር ወደ {method.upper()} ({status_lbl}) በ {dt_local}") + "\n"
            await _send_or_edit_message(update, context, message_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(t(lang, "Back to Referral Menu", "ወደ ኮሚሽን ምናሌ ተመለስ"), callback_data="cmd|referral")]]))
            return

    if prefix == "affiliate":
        action = parts[1]
        if action == "withdraw":
            aff_bal = get_affiliate_balance(user.id)
            min_withdraw = 200.00
            if aff_bal < min_withdraw:
                 await _send_or_edit_message(update, context, t(lang, f"Minimum withdrawal is {min_withdraw:.2f} ETB. Your current balance is {aff_bal:.2f} ETB.", f"ቢያንስ {min_withdraw:.2f} ብር ማውጣት ይችላሉ። የአሁኑ ቀሪ ሂሳብዎ {aff_bal:.2f} ብር ነው።"), is_main_menu=True)
                 return
            context.user_data.pop('pending_withdrawal_amount', None)
            context.user_data.pop('awaiting_withdrawal_detail', None)
            context.user_data['awaiting_withdrawal_amount'] = True
            await _send_or_edit_message(update, context, t(lang, f"Your Affiliate Balance: {aff_bal:.2f} ETB.\nMinimum withdrawal: {min_withdraw:.2f} ETB.\n\nSend the amount you wish to withdraw (numbers only, max {aff_bal:.2f}):", f"የኮሚሽን ቀሪ ሂሳብዎ: {aff_bal:.2f} ብር ነው። አነስተኛ ማውጣት: {min_withdraw:.2f} ብር ነው።\n\nማውጣት የሚፈልጉትን መጠን ይላኩ (ቁጥር ብቻ፣ ከፍተኛው {aff_bal:.2f}):"), is_main_menu=True)
            return
        elif action == "select_method":
            method = parts[2]
            amount = context.user_data.get('pending_withdrawal_amount', 0.0)
            if amount <= 0.00: 
                await _send_or_edit_message(update, context, t(lang, "Error: Invalid amount. Try again.", "ስህተት: የተሳሳተ መጠን።"), is_main_menu=True)
                return
            context.user_data['awaiting_withdrawal_detail'] = method
            prompt_en, prompt_am = "", ""
            if method == "telebirr": prompt_en, prompt_am = f"You are withdrawing {amount:.2f} ETB via Telebirr.\nPlease send your *Telebirr phone number*:", f"{amount:.2f} ብር በቴሌብር እያወጡ ነው።\nእባክዎ *የቴሌብር ስልክ ቁጥርዎን* ይላኩ:"
            elif method == "cbe": prompt_en, prompt_am = f"You are withdrawing {amount:.2f} ETB via CBE.\nPlease send your *CBE account number*:", f"{amount:.2f} ብር በCBE እያወጡ ነው።\nእባክዎ *የCBE አካውንት ቁጥርዎን* ይላኩ:"
            context.user_data.pop('pending_withdrawal_amount', None)
            await _send_or_edit_message(update, context, t(lang, prompt_en, prompt_am), is_main_menu=True)
            return

    if prefix == "affiliate_admin":
        action = parts[1]
        withdrawal_id = int(parts[2])
        target_user_id = int(parts[3])
        if query.from_user.id != ADMIN_ID: return
        details = get_withdrawal_details(withdrawal_id)
        if not details: return
        amount = details['amount']
        user_lang_for_notification = _get_user_language(target_user_id)
        if action == "approve_withdrawal":
            aff_bal = get_affiliate_balance(target_user_id)
            if aff_bal < amount:
                await query.answer(f"Error: User {target_user_id} only has {aff_bal:.2f} ETB.", show_alert=True)
                return
            ok, new_bal = deduct_affiliate_balance(target_user_id, amount)
            if ok:
                update_withdrawal_status_and_admin_msg(withdrawal_id, "approved")
                try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, f"✅ Your withdrawal of {amount:.2f} ETB has been approved and successfully sent to your {details['method'].upper()} account ({details['account_detail']}). Your affiliate balance is now {new_bal:.2f} ETB.", f"✅ የ{amount:.2f} ብር ኮሚሽን ማውጣት ጥያቄዎ ተፈቅዷል እና በ {details['method'].upper()} አካውንትዎ ({details['account_detail']}) ተልኳል። ቀሪ ኮሚሽንዎ {new_bal:.2f} ብር ነው።"))
                except Exception: pass
                await query.edit_message_text(query.message.text + f"\n\n✅ APPROVED/SENT. Balance deducted from user. ({new_bal:.2f} remaining)", reply_markup=None)
            return
        elif action == "reject_withdrawal":
            update_withdrawal_status_and_admin_msg(withdrawal_id, "rejected")
            try: await context.bot.send_message(chat_id=target_user_id, text=t(user_lang_for_notification, f"❌ Your withdrawal request for {amount:.2f} ETB was rejected. Please contact the admin for details.", f"❌ የ{amount:.2f} ብር ኮሚሽን ማውጣት ጥያቄዎ አልተፈቀደም። እባክዎ አስተዳዳሪውን ያነጋግሩ።"))
            except Exception: pass
            await query.edit_message_text(query.message.text + f"\n\n❌ REJECTED.", reply_markup=None)
            return

    if prefix == "back":
        await start(update, context)
        return

    if prefix == "lang":
        if len(parts) >= 2:
            chosen = parts[1]
            if chosen in ("am", "en"):
                _set_user_language(user.id, chosen)
                context.user_data["lang"] = chosen
                try: await query.delete_message()
                except Exception: pass
                await start(update, context)
                return

    await _send_or_edit_message(update, context, t(lang, "Unknown action.", "ያልታወቀ እርስዎ።"), is_main_menu=True)

# ---------------- Text Handler ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    lang = _get_user_language(user.id)
    context.user_data['lang'] = lang

    # --- Withdrawal Amount ---
    if context.user_data.get("awaiting_withdrawal_amount"):
        txt = update.message.text.strip()
        aff_bal = get_affiliate_balance(user_id)
        min_withdraw = 200.00
        try:
            amount = float(txt)
            if amount < min_withdraw:
                raise ValueError(t(lang, f"Amount must be at least {min_withdraw:.2f} ETB.", f"መጠኑ ቢያንስ {min_withdraw:.2f} ብር መሆን አለበት።"))
            if amount > aff_bal:
                 raise ValueError(t(lang, f"Insufficient balance. Your current affiliate balance is {aff_bal:.2f} ETB.", f"በቂ ቀሪ ሂሳብ የለም። የአሁኑ ኮሚሽንዎ {aff_bal:.2f} ብር ነው።"))
            context.user_data.pop("awaiting_withdrawal_amount", None)
            context.user_data['pending_withdrawal_amount'] = amount
            kb = [[InlineKeyboardButton("Telebirr", callback_data=f"affiliate|select_method|telebirr")], [InlineKeyboardButton("CBE", callback_data=f"affiliate|select_method|cbe")], [InlineKeyboardButton(t(lang, "Cancel", "ሰርዝ"), callback_data="cmd|referral")]]
            await _send_or_edit_message(update, context, t(lang, f"You wish to withdraw {amount:.2f} ETB. Choose your payment method:", f"{amount:.2f} ብር ማውጣት ይፈልጋሉ። የክፍያ መንገድዎን ይምረጡ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
            return
        except ValueError as e:
            await update.message.reply_text(t(lang, str(e), str(e)))
            context.user_data['awaiting_withdrawal_amount'] = True 
            return

    # --- Custom Recharge Amount ---
    if context.user_data.get("awaiting_custom_recharge_amount"):
        txt = update.message.text.strip()
        try:
            amount = float(txt)
            if amount <= 0: raise ValueError("Amount must be positive.")
            context.application.bot_data[f"recharge_pending:{user_id}"] = {"amount": amount, "method": None}
            context.user_data.pop("awaiting_custom_recharge_amount", None)
            kb = []
            for m in PAYMENT_INFO.keys(): kb.append([InlineKeyboardButton(m.capitalize(), callback_data=f"recharge_pay|{m}")])
            kb.append([InlineKeyboardButton(t(lang, "Cancel", "ሰርዝ"), callback_data="cmd|recharge")])
            await _send_or_edit_message(update, context, t(lang, f"Send {amount:.2f} ETB to one of these accounts and upload screenshot here.", f"{amount:.2f} ብር ወደ ከዚህ አካውንቶች ይላኩ እና ስክሪንሾት ይላኩ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)
        except ValueError:
            await update.message.reply_text(t(lang, "Please send a valid number amount.", "እባክዎ ትክክለኛ ቁጥር ይላኩ።"))
        return
    
    # --- Withdrawal Detail ---
    if context.user_data.get("awaiting_withdrawal_detail"):
        detail = update.message.text.strip()
        method = context.user_data.pop("awaiting_withdrawal_detail", None)
        amount = context.user_data.pop('pending_withdrawal_amount', 0.0)
        if amount <= 0.00: 
            await update.message.reply_text(t(lang, "Error: Invalid withdrawal amount or session expired. Try again.", "ስህተት: የተሳሳተ የማውጣት መጠን ወይም ጊዜው አልፏል። ድገም."))
            return
        if not detail or len(detail) < 5 or len(detail) > 20: 
            await update.message.reply_text(t(lang, "Invalid input. Please send a valid phone/account number.", "የተሳሳተ ግብአት። ትክክለኛ ስልክ ቁጥር/አካውንት ቁጥር ይላኩም።"))
            context.user_data['awaiting_withdrawal_detail'] = method
            context.user_data['pending_withdrawal_amount'] = amount
            return
        withdrawal_id = create_withdrawal_request(user_id, amount, method, detail)
        await update.message.reply_text(t(lang, f"✅ Your withdrawal request for {amount:.2f} ETB via {method.upper()} (Detail: {detail}) has been submitted.\n*You will receive your money in less than 2 days.*", f"✅ የ{amount:.2f} ብር ኮሚሽን ማውጣት ጥያቄዎ በ{method.upper()} (መለያ: {detail}) ገብቷል።\n*ገንዘብዎን ከ 2 ቀን ባነሰ ጊዜ ውስጥ ያገኛሉ።*"))
        caption = f"🚨 *NEW WITHDRAWAL REQUEST* (ID: {withdrawal_id})\nUser: @{user.username or user.first_name} (ID: {user_id})\nAmount: {amount:.2f} ETB\nMethod: {method.upper()}\nAccount Detail: `{detail}`\nStatus: PENDING ADMIN APPROVAL"
        admin_kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve/Sent", callback_data=f"affiliate_admin|approve_withdrawal|{withdrawal_id}|{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"affiliate_admin|reject_withdrawal|{withdrawal_id}|{user_id}")]])
        try:
            sent = await context.bot.send_message(chat_id=ADMIN_ID, text=caption, reply_markup=admin_kb)
            update_withdrawal_status_and_admin_msg(withdrawal_id, "pending", admin_message_id=sent.message_id)
        except Exception as e:
            logger.error(f"Failed to send withdrawal request to admin: {e}")
            await update.message.reply_text(t(lang, "Error sending notification to admin. Please contact support.", "ለአስተዳዳሪ ማሳወቂያ መላክ አልተቻለም።"))
        return

    # --- Order Link/Username ---
    if context.user_data.get("awaiting_link_for_order"):
        link = update.message.text.strip()
        order = context.application.bot_data.get(f"order:{user.id}")
        if not order:
            await _send_or_edit_message(update, context, t(lang, "No order found. Use /start to begin.", "ትዕዛዝ አልተገኘም። /start ይጠቀሙም።"), is_main_menu=True)
            context.user_data.pop("awaiting_link_for_order", None)
            return
        
        service_key = order.get("service_key")
        subkey = order.get("subkey")
        clean_link = link.strip().lstrip('@')
        target_url = link

        is_url_service = False
        if (service_key == "tiktok" and subkey != "followers") or \
           (service_key == "youtube" and subkey != "subs") or \
           (service_key == "facebook" and subkey == "post_likes") or \
           (service_key == "telegram" and subkey in ("reactions", "post_views")) or \
           (service_key == "instagram" and subkey in ("likes", "views")):
            is_url_service = True

        if is_url_service:
            if not (link.lower().startswith("http") and "." in link and len(link) > 8):
                 await update.message.reply_text(t(lang, "❌ Invalid Link. Please send a valid URL starting with http:// or https://", "❌ የተሳሳተ ሊንክ። እባክዎ ትክክለኛ http:// ወይም https:// የሚጀምር ሊንክ ይላኩ።"))
                 context.user_data['awaiting_link_for_order'] = True
                 return
        
        if len(link) < 2:
             await update.message.reply_text(t(lang, "Invalid input. Please send a complete link or username (must be 2 or more characters).", "ትክክለኛ ያልሆነ ግብዓት። ሙሉ ሊንክ ወይም ዩዘርኔም ይላኩ (ቢያንስ 2 ፊደላት/ቁጥሮች ያስፈልጋል)።"))
             context.user_data['awaiting_link_for_order'] = True 
             return

        if not clean_link.lower().startswith('http'):
            if service_key == "tiktok" and order['subkey'] == 'followers': target_url = f"https://www.tiktok.com/@{clean_link}"
            elif service_key == "youtube" and order['subkey'] in ('subs', 'views', 'shares', 'likes'): target_url = f"https://www.youtube.com/@{clean_link}"
            elif service_key == "instagram" and order['subkey'] in ('likes', 'views', 'followers'): target_url = f"https://www.instagram.com/{clean_link}"
            elif service_key == "facebook" and order['subkey'] in ('page_likes_and_followers', 'followers'): target_url = f"https://www.facebook.com/{clean_link}"
            elif service_key == "telegram" and order['subkey'] == 'members': target_url = f"https://t.me/{clean_link}"
            else: target_url = link
        else:
            target_url = link

        order["target"] = target_url
        context.application.bot_data[f"order:{user.id}"] = order
        context.user_data.pop("awaiting_link_for_order", None)
        
        confirmation_msg_en = f"Please confirm the target link/username for '{order['package_title']}' ({order['price']:.2f} ETB):\n\nLINK: {target_url}\n\nIs this correct?"
        confirmation_msg_am = f"እባክዎ ለ '{order['package_title']}' ({order['price']:.2f} ብር) ትዕዛዝ የሚፈልጉት ሊንክ/ዩዘርኔም ትክክል መሆኑን ያረጋግጡ:\n\nሊንክ: {target_url}\n\nይህ ትክክል ነው?"
        kb = [[InlineKeyboardButton(t(lang, "Yes, Confirm", "አዎ አረጋግጥ"), callback_data="confirm_order|yes"), InlineKeyboardButton(t(lang, "Change", "ቀይር"), callback_data="confirm_order|change")], [InlineKeyboardButton(t(lang, "Open/Copy Link", "ሊንኩን ክፈት/ቅዳ"), url=target_url)]]
        
        try:
            await context.bot.send_message(chat_id=user_id, text=t(lang, confirmation_msg_en, confirmation_msg_am), reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=False)
        except Exception:
            await update.message.reply_text("Error processing link. Please type /start")
        return

    await update.message.reply_text(t(lang, "Use /start to begin an order, /recharge to add balance, or /balance to see your balance.", "እባክዎ /start ይጠቀሙ ለትዕዛዝ፣ /recharge ለገንዘብ ማስገቢያ፣ ወይም /balance ለቀሪ ሂሳብ።"))

# ---------------- Photo handler ----------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    lang = _get_user_language(user.id)
    context.user_data['lang'] = lang

    if not update.message.photo:
            await update.message.reply_text(t(lang, "Please send a photo screenshot.", "እባክዎ ስክሪንሾት ይላኩ።"))
            return

    file_id = update.message.photo[-1].file_id
    pending_recharge = context.application.bot_data.get(f"recharge_pending:{user_id}")
    if pending_recharge:
        amount = pending_recharge.get("amount")
        method = pending_recharge.get("method")
        recharge_id = create_recharge(user_id, amount, method or "unknown", status="pending")
        caption = f"🔔 Recharge request\nUser: @{user.username or user.first_name} (ID: {user_id})\nAmount: {amount:.2f} ETB\nMethod: {method or 'N/A'}\nRecharge ID: {recharge_id}"
        admin_kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"admin|approve_recharge|{recharge_id}|{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin|reject_recharge|{recharge_id}|{user_id}")]])
        try:
            sent = await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=admin_kb)
            update_recharge_status(recharge_id, "pending", admin_message_id=sent.message_id)
            context.application.bot_data.pop(f"recharge_pending:{user_id}", None)
            await update.message.reply_text(t(lang, "Your payment is being reviewed. Please wait.", "ክፍያዎን እየገመገምን ነው። እባክዎ ይጠብቁ።"))
        except Exception as e:
            logger.exception("Failed to forward recharge to admin: %s", e)
            await update.message.reply_text(t(lang, "Could not forward screenshot to admin. Try later.", "ስክሪንሾትን ወደ አስተዳደር ማስመላለሻ አልተቻለም።"))
        return

    order = context.application.bot_data.get(f"order:{user.id}")
    if order and order.get("order_id") and order.get("payment_method"):
        order_id = order.get("order_id")
        caption = f"🔔 Order payment\nUser: @{user.username or user.first_name} (ID: {user_id})\nOrder ID: {order_id}\nService: {SERVICES[order['service_key']]['label_en']} - {order['package_title']}\nTarget: {order.get('target','N/A')}\nPrice: {order['price']:.2f} ETB\nMethod: {order.get('payment_method','N/A')}"
        admin_kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Approve", callback_data=f"admin|approve_order|{order_id}|{user_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin|reject_order|{order_id}|{user_id}")]])
        try:
            sent = await context.bot.send_photo(chat_id=ADMIN_ID, photo=file_id, caption=caption, reply_markup=admin_kb)
            await update.message.reply_text(t(lang, "Your payment is being reviewed. Please wait.", "ክፍያዎን እየገመገምን ነው። እባክዎ ይጠብቁ።"))
            context.application.bot_data.pop(f"order:{user_id}", None)
        except Exception as e:
            logger.exception("Failed to forward order payment to admin: %s", e)
            await update.message.reply_text(t(lang, "Could not forward screenshot to admin. Try later.", "ስክሪንሾትን ወደ አስተዳደር ማስመላለሻ አልተቻለም።"))
        return

    await update.message.reply_text(t(lang, "No pending order or recharge found. Use /start or /recharge to begin.", "ምንም የቆየ ትዕዛዝ ወይም ክፍያ የለም። /start ወይም /recharge ይጠቀሙ።"))

# ---------------- Commands ----------------
async def service_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = _get_user_language(user_id)
    context.user_data['lang'] = lang
    bal = get_balance(user_id)
    await _send_or_edit_message(update, context, t(lang, f"Your balance: {bal:.2f} ETB", f"ቀሪ ሂሳብ: {bal:.2f} ብር"), is_main_menu=True)

async def recharge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_user_language(update.effective_user.id)
    context.user_data['lang'] = lang
    kb = [[InlineKeyboardButton("200 ETB", callback_data="recharge_amt|200")], [InlineKeyboardButton("500 ETB", callback_data="recharge_amt|500")], [InlineKeyboardButton("1000 ETB", callback_data="recharge_amt|1000")], [InlineKeyboardButton(t(lang, "Custom amount", "የራስዎ መጠን"), callback_data="recharge_custom|")], [InlineKeyboardButton(t(lang, "Back", "ተመለስ"), callback_data="back|")]]
    await _send_or_edit_message(update, context, t(lang, "Choose amount to recharge:", "እባክዎ መጠን ይምረጡ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)

async def referral_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    class MockQuery:
        def __init__(self, data, from_user):
            self.data = data
            self.from_user = from_user
            self.message = None 
        async def answer(self): pass 
    mock_query = MockQuery("cmd|referral", update.effective_user)
    update.callback_query = mock_query 
    await callback_handler(update, context)
    update.callback_query = None 

async def addbalance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = int(context.args[0])
        amount = float(context.args[1])
        new_bal = add_balance(user_id, amount)
        await update.message.reply_text(f"✅ Added {amount:.2f} ETB to {user_id}. New balance: {new_bal:.2f} ETB")
    except Exception:
        await update.message.reply_text("Usage: /addbalance <user_id> <amount>")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID: return
    message_to_send = " ".join(context.args)
    if not message_to_send:
        await update.message.reply_text("Usage: /broadcast <your message here>")
        return
    users = get_all_user_ids()
    status_msg = await update.message.reply_text(f"📢 Starting broadcast to {len(users)} users...")
    success_count, block_count = 0, 0
    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message_to_send)
            success_count += 1
        except Exception:
            block_count += 1
    await context.bot.edit_message_text(chat_id=user_id, message_id=status_msg.message_id, text=f"✅ Broadcast Complete.\n\nSent to: {success_count}\nFailed/Blocked: {block_count}\nTotal: {len(users)}")

async def post_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    caption_text = (
        "💸 *በኢሊቬት ገንዘብ ይስሩ!* 💸\n\n"
        "ብዙ ሰዎች ሌሎችን በመጋበዝ ብቻ በቦታችን በሺዎች የሚቆጠር ገንዘብ እየሰሩ ነው! 😱\n\n"
        "እርስዎም ጓደኞችዎን በመጋበዝ ከሚያስገቡት ክፍያ ላይ ኮሚሽን ማግኘት ይችላሉ።\n\n"
        "👇 የመጋበዣ ሊንክዎን ለማግኘት እና ገቢ ለመጀመር ከታች ያለውን ይጫኑ!\n\n"
        "--------------------------------\n\n"
        "💸 *Make Money with Elevate!* 💸\n\n"
        "Many people are making thousands of birr using our bot just by inviting others! 😱\n\n"
        "Don't miss out! You can also earn commissions on every deposit your friends make.\n\n"
        "👇 Click the button below to get your Invite Link and start earning today!"
    )
    keyboard = [[InlineKeyboardButton("💰 Join Affiliate Program / ገንዘብ ማግኘት ይጀምሩ 💰", callback_data="cmd|referral")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    photo_name = "pos 1.jpg" 
    users = get_all_user_ids()
    await update.message.reply_text(f"⏳ Sending Affiliate Promo to {len(users)} users...")
    if not os.path.isfile(photo_name):
        await update.message.reply_text(f"❌ Error: Could not find '{photo_name}' in the folder.")
        return
    success = 0
    for uid in users:
        try:
            with open(photo_name, 'rb') as ph:
                await context.bot.send_photo(chat_id=uid, photo=ph, caption=caption_text, parse_mode='Markdown', reply_markup=reply_markup)
            success += 1
        except Exception: pass
    await update.message.reply_text(f"✅ Done! Sent to {success} users.")

async def my_orders_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = _get_user_language(user_id)
    context.user_data['lang'] = lang
    
    orders = get_last_orders(user_id)
    
    if not orders:
        msg = t(lang, "You have no order history.", "የትዕዛዝ ታሪክ የለዎትም።")
        await update.message.reply_text(msg)
        return

    text = t(lang, "*📦 Your Recent Orders:*\n\n", "*📦 የእርስዎ የቅርብ ትዕዛዞች:*\n\n")
    
    for oid, title, price, status, date in orders:
        status_display = status.upper()
        if status in ['pending', 'pending_approval', 'processing']:
            status_display = "⏳ PENDING"
        elif status in ['completed', 'approved']:
            status_display = "✅ DONE"
        elif status in ['rejected', 'cancelled']:
            status_display = "❌ CANCELED"
            
        text += f"🆔 {oid} | {title}\n💰 {price:.2f} ETB | {status_display}\n\n"
        
    await update.message.reply_text(text, parse_mode='Markdown')

async def more_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = _get_user_language(user_id)
    context.user_data['lang'] = lang
    
    msg = t(lang, 
            "📞 *Support & Info*\n\nFor any issues, deposits, or questions, please contact our support team:\n\n👤 @Elevatesupport\n📞 0955974297",
            "📞 *መረጃ እና እርዳታ*\n\nለማንኛውም ጥያቄ ወይም ችግር፣ እባክዎ የድጋፍ ቡድናችንን ያግኙ:\n\n👤 @Elevatesupport\n📞 0955974297"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_user_language(update.effective_user.id)
    context.user_data['lang'] = lang
    kb = [[InlineKeyboardButton("አማርኛ", callback_data="lang|am"), InlineKeyboardButton("English", callback_data="lang|en")]]
    await _send_or_edit_message(update, context, t(lang, "Choose language:", "ቋንቋ ይምረጡ።"), reply_markup=InlineKeyboardMarkup(kb), is_main_menu=True)

async def unknown_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _get_user_language(update.effective_user.id)
    context.user_data['lang'] = lang
    await update.message.reply_text(t(lang, "Use /start or /recharge to begin.", "እባክዎ /start ወይም /recharge ይጠቀሙ።"))

# ---------------- Main ----------------
def main():
    if not BOT_TOKEN:
        logger.error("FATAL ERROR: BOT_TOKEN not set.")
        return
    if ADMIN_ID == 0:
        logger.error("FATAL ERROR: ADMIN_ID not set.")
        return
    
    # 1. Start the dummy web server in a separate thread (KEEPS RENDER AWAKE)
    keep_alive()

    # 2. Build App
    app = Application.builder().token(BOT_TOKEN).read_timeout(7).write_timeout(30).arbitrary_callback_data(True).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("service", service_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("recharge", recharge_cmd))
    app.add_handler(CommandHandler("referral", referral_cmd))
    app.add_handler(CommandHandler("addbalance", addbalance_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd)) 
    app.add_handler(CommandHandler("postpromo", post_promo))
    app.add_handler(CommandHandler("my_orders", my_orders_cmd))
    app.add_handler(CommandHandler("more", more_cmd))
    app.add_handler(CommandHandler("language", language_cmd))

    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_cmd))
    
    logger.info("Elevate Promotion bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
