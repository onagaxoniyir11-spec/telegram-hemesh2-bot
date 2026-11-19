import telebot
from telebot import types
import pyzipper
from datetime import datetime, timezone
import random
import os
import io
import time
import base64
import json
import requests
from flask import Flask, request

# Load credentials (Uses provided Token as default if BOT_TOKEN env var is not set)
TOKEN = os.environ.get("BOT_TOKEN", "8908618066:AAFbWasMZ1pyrYisSFRoGYY1VFTVEjFK7jE")
FIREBASE_URL = os.environ.get("FIREBASE_URL")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("BOT_TOKEN is missing!")
if not FIREBASE_URL:
    raise ValueError("FIREBASE_URL environment variable is missing!")

FIREBASE_URL = FIREBASE_URL.rstrip("/")

bot = telebot.TeleBot(TOKEN, threaded=False)

# Support Username & Admin IDs
support_admin_username = "@soeminhtun101"
ADMIN_IDS = [8138758919]
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "N1010")

# In-memory Database & State Management
user_amounts = {}
user_states = {}
user_balances = {}
user_purchases = {}
user_deposits = {}
pending_deposits = {}
used_txids = set()
user_languages = {}
all_users = set()
temp_admin_data = {}

# ----------------- COUNTRY FLAG & CHINESE NAME HELPER -----------------
COUNTRY_ZH_NAMES = {
    "afghanistan": "阿富汗", "albania": "阿尔巴尼亚", "algeria": "阿尔及利亚", "andorra": "安道尔",
    "angola": "安哥拉", "argentina": "阿根廷", "armenia": "亚美尼亚", "australia": "澳大利亚",
    "austria": "奥地利", "azerbaijan": "阿塞拜疆", "bahamas": "巴哈马", "bahrain": "巴林",
    "bangladesh": "孟加拉国", "barbados": "巴巴多斯", "belarus": "白俄罗斯", "belgium": "比利时",
    "belize": "伯利兹", "benin": "贝宁", "bhutan": "不丹", "bolivia": "玻利维亚",
    "bosnia": "波斯尼亚", "botswana": "博茨瓦纳", "brazil": "巴西", "brunei": "文莱",
    "bulgaria": "保加利亚", "burkina faso": "布基纳法索", "burundi": "布隆迪", "cambodia": "柬埔寨",
    "cameroon": "喀麦隆", "canada": "加拿大", "chad": "乍得", "chile": "智利",
    "china": "中国", "colombia": "哥伦比亚", "congo": "刚果", "costa rica": "哥斯达黎加",
    "croatia": "克罗地亚", "cuba": "古巴", "cyprus": "塞浦路斯", "czech republic": "捷克",
    "czechia": "捷克", "denmark": "丹麦", "djibouti": "吉布提", "dominican republic": "多米尼加",
    "ecuador": "厄瓜多尔", "egypt": "埃及", "el salvador": "萨尔瓦多", "estonia": "爱沙尼亚",
    "ethiopia": "埃塞俄比亚", "fiji": "斐济", "finland": "芬兰", "france": "法国",
    "gabon": "加蓬", "gambia": "冈比亚", "georgia": "格鲁吉亚", "germany": "德国",
    "ghana": "加纳", "greece": "希腊", "guatemala": "危地马拉", "guinea": "几内亚",
    "haiti": "海地", "honduras": "洪都拉斯", "hong kong": "中国香港", "hungary": "匈牙利",
    "iceland": "冰岛", "india": "印度", "indonesia": "印度尼西亚", "iran": "伊朗",
    "iraq": "伊拉克", "ireland": "爱尔兰", "israel": "以色列", "italy": "意大利",
    "ivory coast": "科特迪瓦", "jamaica": "牙买加", "japan": "日本", "jordan": "约旦",
    "kazakhstan": "哈萨克斯坦", "kenya": "肯尼亚", "kuwait": "科威特", "kyrgyzstan": "吉尔吉斯斯坦",
    "laos": "老挝", "latvia": "拉脱维亚", "lebanon": "黎巴嫩", "liberia": "利比里亚",
    "libya": "利比亚", "lithuania": "立陶宛", "luxembourg": "卢森堡", "macau": "中国澳门",
    "madagascar": "马达加斯加", "malawi": "马拉维", "malaysia": "马来西亚", "maldives": "马尔代夫",
    "mali": "马里", "malta": "马耳他", "mauritania": "毛里塔尼亚", "mauritius": "毛里求斯",
    "mexico": "墨西哥", "moldova": "摩尔多瓦", "monaco": "摩纳哥", "mongolia": "蒙古",
    "montenegro": "黑山", "morocco": "摩洛哥", "mozambique": "莫桑比克", "myanmar": "缅甸",
    "burma": "缅甸", "namibia": "纳米比亚", "nepal": "尼泊尔", "netherlands": "荷兰",
    "new zealand": "新西兰", "nicaragua": "尼加拉瓜", "niger": "尼日尔", "nigeria": "尼日利亚",
    "north korea": "朝鲜", "north macedonia": "北马其顿", "norway": "挪威", "oman": "阿曼",
    "pakistan": "巴基斯坦", "palestine": "巴勒斯坦", "panama": "巴拿马", "papua new guinea": "巴布亚新几内亚",
    "paraguay": "巴拉圭", "peru": "秘鲁", "philippines": "菲律宾", "poland": "波兰",
    "portugal": "葡萄牙", "puerto rico": "波多黎各", "qatar": "卡塔尔", "romania": "罗马尼亚",
    "russia": "俄罗斯", "rwanda": "卢旺达", "saudi arabia": "沙特阿拉伯", "senegal": "塞内加尔",
    "serbia": "塞尔维亚", "sierra leone": "塞拉利昂", "singapore": "新加坡", "slovakia": "斯洛伐克",
    "slovenia": "斯洛文尼亚", "somalia": "索马里", "south africa": "南非", "south korea": "韩国",
    "korea": "韩国", "south sudan": "南苏丹", "spain": "西班牙", "sri lanka": "斯里兰卡",
    "sudan": "苏丹", "sweden": "瑞典", "switzerland": "瑞士", "syria": "叙利亚",
    "taiwan": "中国台湾", "tajikistan": "塔吉克斯坦", "tanzania": "坦桑尼亚", "thailand": "泰国",
    "togo": "多哥", "trinidad and tobago": "特立尼达和多巴哥", "tunisia": "突尼斯", "turkey": "土耳其",
    "turkmenistan": "土库曼斯坦", "uganda": "乌干达", "ukraine": "乌克兰", "uae": "阿联酋",
    "united arab emirates": "阿联酋", "uk": "英国", "united kingdom": "英国",
    "usa": "美国", "united states": "美国", "uruguay": "乌拉圭", "uzbekistan": "乌兹别克斯坦",
    "venezuela": "委内瑞拉", "vietnam": "越南", "yemen": "也门", "zambia": "赞比亚",
    "zimbabwe": "津巴布韦"
}

COUNTRY_FLAGS_BY_NAME = {
    "afghanistan": "🇦🇫", "albania": "🇦🇱", "algeria": "🇩🇿", "andorra": "🇦🇩",
    "angola": "🇦🇴", "argentina": "🇦🇷", "armenia": "🇦🇲", "australia": "🇦🇺",
    "austria": "🇦🇹", "azerbaijan": "🇦🇿", "bahamas": "🇧🇸", "bahrain": "🇧🇭",
    "bangladesh": "🇧🇩", "barbados": "🇧🇧", "belarus": "🇧🇾", "belgium": "🇧🇪",
    "belize": "🇧🇿", "benin": "🇧🇯", "bhutan": "🇧🇹", "bolivia": "🇧🇴",
    "bosnia": "🇧🇦", "botswana": "🇧🇼", "brazil": "🇧🇷", "brunei": "🇧🇳",
    "bulgaria": "🇧🇬", "burkina faso": "🇧🇫", "burundi": "🇧🇮", "cambodia": "🇰🇭",
    "cameroon": "🇨🇲", "canada": "🇨🇦", "chad": "🇹🇩", "chile": "🇨🇱",
    "china": "🇨🇳", "colombia": "🇨🇴", "congo": "🇨🇬", "costa rica": "🇨🇷",
    "croatia": "🇭🇷", "cuba": "🇨🇺", "cyprus": "🇨🇾", "czech republic": "🇨🇿",
    "czechia": "🇨🇿", "denmark": "🇩🇰", "djibouti": "🇩🇯", "dominican republic": "🇩🇴",
    "ecuador": "🇪🇨", "egypt": "🇪🇬", "el salvador": "🇸🇻", "estonia": "🇪🇪",
    "ethiopia": "🇪🇹", "fiji": "🇫🇯", "finland": "🇫🇮", "france": "🇫🇷",
    "gabon": "🇬🇦", "gambia": "🇬🇲", "georgia": "🇬🇪", "germany": "🇩🇪",
    "ghana": "🇬🇭", "greece": "🇬🇷", "guatemala": "🇬🇹", "guinea": "🇬🇳",
    "haiti": "🇭🇹", "honduras": "🇭🇳", "hong kong": "🇭🇰", "hungary": "🇭🇺",
    "iceland": "🇮🇸", "india": "🇮🇳", "indonesia": "🇮🇩", "iran": "🇮🇷",
    "iraq": "🇮🇶", "ireland": "🇮🇪", "israel": "🇮🇱", "italy": "🇮🇹",
    "ivory coast": "🇨🇮", "jamaica": "🇯🇲", "japan": "🇯🇵", "jordan": "🇯🇴",
    "kazakhstan": "🇰🇿", "kenya": "🇰🇪", "kuwait": "🇰🇼", "kyrgyzstan": "🇰🇬",
    "laos": "🇱🇦", "latvia": "🇱🇻", "lebanon": "🇱🇧", "liberia": "🇱🇷",
    "libya": "🇱🇾", "lithuania": "🇱🇹", "luxembourg": "🇱🇺", "macau": "🇲🇴",
    "madagascar": "🇲🇬", "malawi": "🇲🇼", "malaysia": "🇲🇾", "maldives": "🇲🇻",
    "mali": "🇲🇱", "malta": "🇲🇹", "mauritania": "🇲🇷", "mauritius": "🇲🇺",
    "mexico": "🇲🇽", "moldova": "🇲🇩", "monaco": "🇲🇨", "mongolia": "🇲🇳",
    "montenegro": "🇲🇪", "morocco": "🇲🇦", "mozambique": "🇲🇿", "myanmar": "🇲🇲",
    "burma": "🇲🇲", "namibia": "🇳🇦", "nepal": "🇳🇵", "netherlands": "🇳🇱",
    "new zealand": "🇳🇿", "nicaragua": "🇳🇮", "niger": "🇳🇪", "nigeria": "🇳🇬",
    "north korea": "🇰🇵", "north macedonia": "🇲🇰", "norway": "🇳🇴", "oman": "🇴🇲",
    "pakistan": "🇵🇰", "palestine": "🇵🇸", "panama": "🇵🇦", "papua new guinea": "🇵🇬",
    "paraguay": "🇵🇾", "peru": "🇵🇪", "philippines": "🇵🇭", "poland": "🇵🇱",
    "portugal": "🇵🇹", "puerto rico": "🇵🇷", "qatar": "🇶🇦", "romania": "🇷🇴",
    "russia": "🇷🇺", "rwanda": "🇷🇼", "saudi arabia": "🇸🇦", "senegal": "🇸🇳",
    "serbia": "🇷🇸", "sierra leone": "🇸🇱", "singapore": "🇸🇬", "slovakia": "🇸🇰",
    "slovenia": "🇸🇮", "somalia": "🇸🇴", "south africa": "🇿🇦", "south korea": "🇰🇷",
    "korea": "🇰🇷", "south sudan": "🇸🇸", "spain": "🇪🇸", "sri lanka": "🇱🇰",
    "sudan": "🇸🇩", "sweden": "🇸🇪", "switzerland": "🇨🇭", "syria": "🇸🇾",
    "taiwan": "🇹🇼", "tajikistan": "🇹🇯", "tanzania": "🇹🇿", "thailand": "🇹🇭",
    "togo": "🇹🇬", "trinidad and tobago": "🇹🇹", "tunisia": "🇹🇳", "turkey": "🇹🇷",
    "turkmenistan": "🇹🇲", "uganda": "🇺🇬", "ukraine": "🇺🇦", "uae": "🇦🇪",
    "united arab emirates": "🇦🇪", "uk": "🇬🇧", "united kingdom": "🇬🇧",
    "usa": "🇺🇸", "united states": "🇺🇸", "uruguay": "🇺🇾", "uzbekistan": "🇺🇿",
    "venezuela": "🇻🇪", "vietnam": "🇻🇳", "yemen": "🇾🇪", "zambia": "🇿🇲",
    "zimbabwe": "🇿🇼"
}

COUNTRY_FLAGS_BY_CODE = {
    "+93": "🇦🇫", "+355": "🇦🇱", "+213": "🇩🇿", "+376": "🇦🇩", "+244": "🇦🇴",
    "+54": "🇦🇷", "+374": "🇦🇲", "+61": "🇦🇺", "+43": "🇦🇹", "+994": "🇦🇿",
    "+973": "🇧🇭", "+880": "🇧🇩", "+375": "🇧🇾", "+32": "🇧🇪", "+501": "🇧🇿",
    "+229": "🇧🇯", "+975": "🇧🇹", "+591": "🇧🇴", "+387": "🇧🇦", "+267": "🇧🇼",
    "+55": "🇧🇷", "+673": "🇧🇳", "+359": "🇧🇬", "+226": "🇧🇫", "+257": "🇧🇮",
    "+855": "🇰🇭", "+237": "🇨🇲", "+235": "🇹🇩", "+56": "🇨🇱", "+86": "🇨🇳",
    "+57": "🇨🇴", "+506": "🇨🇷", "+385": "🇭🇷", "+53": "🇨🇺", "+357": "🇨🇾",
    "+420": "🇨🇿", "+45": "🇩🇰", "+253": "🇩🇯", "+593": "🇪🇨", "+20": "🇪🇬",
    "+503": "🇸🇻", "+372": "🇪🇪", "+251": "🇪🇹", "+679": "🇫🇯", "+358": "🇫🇮",
    "+33": "🇫🇷", "+241": "🇬🇦", "+220": "🇬🇲", "+995": "🇬🇪", "+49": "🇩🇪",
    "+233": "🇬🇭", "+30": "🇬🇷", "+502": "🇬🇹", "+224": "🇬🇳", "+509": "🇭🇹",
    "+504": "🇭🇳", "+852": "🇭🇰", "+36": "🇭🇺", "+354": "🇮🇸", "+91": "🇮🇳",
    "+62": "🇮🇩", "+98": "🇮🇷", "+964": "🇮🇶", "+353": "🇮🇪", "+972": "🇮🇱",
    "+39": "🇮🇹", "+225": "🇨🇮", "+81": "🇯🇵", "+962": "🇯🇴", "+7": "🇷🇺",
    "+254": "🇰🇪", "+965": "🇰🇼", "+996": "🇰🇬", "+856": "🇱🇦", "+371": "🇱🇻",
    "+961": "🇱🇧", "+231": "🇱🇷", "+218": "🇱🇾", "+370": "🇱🇹", "+352": "🇱🇺",
    "+853": "🇲🇴", "+261": "🇲🇬", "+265": "🇲🇼", "+60": "🇲🇾", "+960": "🇲🇻",
    "+223": "🇲🇱", "+356": "🇲🇹", "+222": "🇲🇷", "+230": "🇲🇺", "+52": "🇲🇽",
    "+373": "🇲🇩", "+377": "🇲🇨", "+976": "🇲🇳", "+382": "🇲🇪", "+212": "🇲🇦",
    "+258": "🇲🇿", "+95": "🇲🇲", "+264": "🇳🇦", "+977": "🇳🇵", "+31": "🇳🇱",
    "+64": "🇳🇿", "+505": "🇳🇮", "+227": "🇳🇪", "+234": "🇳🇬", "+850": "🇰🇵",
    "+389": "🇲🇰", "+47": "🇳🇴", "+968": "🇴🇲", "+92": "🇵🇰", "+970": "🇵🇸",
    "+507": "🇵🇦", "+675": "🇵🇬", "+595": "🇵🇾", "+51": "🇵🇪", "+63": "🇵🇭",
    "+48": "🇵🇱", "+351": "🇵🇹", "+974": "🇶🇦", "+40": "🇷🇴", "+250": "🇷🇼",
    "+966": "🇸🇦", "+221": "🇸🇳", "+381": "🇷🇸", "+232": "🇸🇱", "+65": "🇸🇬",
    "+421": "🇸🇰", "+386": "🇸🇮", "+252": "🇸🇴", "+27": "🇿🇦", "+82": "🇰🇷",
    "+211": "🇸🇸", "+34": "🇪🇸", "+94": "🇱🇰", "+249": "🇸🇩", "+46": "🇸🇪",
    "+41": "🇨🇭", "+963": "🇸🇾", "+886": "🇹🇼", "+992": "🇹🇯", "+255": "🇹🇿",
    "+66": "🇹🇭", "+228": "🇹🇬", "+216": "🇹🇳", "+90": "🇹🇷", "+993": "🇹🇲",
    "+256": "🇺🇬", "+380": "🇺🇦", "+971": "🇦🇪", "+44": "🇬🇧", "+1": "🇺🇸",
    "+598": "🇺🇾", "+998": "🇺🇿", "+58": "🇻🇪", "+84": "🇻🇳", "+967": "🇾🇪",
    "+260": "🇿🇲", "+263": "🇿🇼"
}

def strip_leading_flag(text):
    s = str(text).strip()
    if len(s) >= 2 and 0x1F1E6 <= ord(s[0]) <= 0x1F1FF and 0x1F1E6 <= ord(s[1]) <= 0x1F1FF:
        return s[2:].strip()
    return s

def format_country_display_name(country_key, raw_name, lang_code="en"):
    clean_en = strip_leading_flag(country_key)
    clean_raw = strip_leading_flag(raw_name if raw_name else country_key)
    if lang_code == "zh":
        if clean_raw and clean_raw.lower() != clean_en.lower() and any('\u4e00' <= ch <= '\u9fff' for ch in clean_raw):
            return clean_raw
        key_lower = clean_en.lower()
        if key_lower in COUNTRY_ZH_NAMES:
            return COUNTRY_ZH_NAMES[key_lower]
        for k, zh_val in COUNTRY_ZH_NAMES.items():
            if k in key_lower:
                return zh_val
        return clean_raw
    else:
        if clean_raw:
            return clean_raw[0].upper() + clean_raw[1:]
        return clean_en

def get_country_flag(country_name, country_code=""):
    clean_name = strip_leading_flag(country_name).lower()
    if clean_name in COUNTRY_FLAGS_BY_NAME:
        return COUNTRY_FLAGS_BY_NAME[clean_name]
    for key, flg in COUNTRY_FLAGS_BY_NAME.items():
        if key in clean_name:
            return flg
    code_clean = str(country_code).strip()
    if not code_clean.startswith("+") and code_clean:
        code_clean = "+" + code_clean
    if code_clean in COUNTRY_FLAGS_BY_CODE:
        return COUNTRY_FLAGS_BY_CODE[code_clean]
    return "🌐"
# ----------------------------------------------------------------------

# ----------------- FLASK WEB SERVER & WEBHOOK ROUTE -----------------
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is Running via Webhook!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403
# --------------------------------------------------------------------------

DEFAULT_DATABASE = {
    "support_admin": "@soeminhtun101",
    "product_inventory": {
        "Countries": {
            "type": "countries",
            "items": {
                "Bangladesh": {
                    "code": "+880",
                    "price": 1.50,
                    "names": {"en": "Bangladesh", "zh": "孟加拉国"},
                    "accounts": [], "zip_files": []
                },
                "India": {
                    "code": "+91",
                    "price": 1.20,
                    "names": {"en": "India", "zh": "印度"},
                    "accounts": [], "zip_files": []
                },
                "Usa": {
                    "code": "+1",
                    "price": 3.00,
                    "names": {"en": "USA", "zh": "美国"},
                    "accounts": [], "zip_files": []
                },
                "Brazil": {
                    "code": "+55",
                    "price": 2.00,
                    "names": {"en": "Brazil", "zh": "巴西"},
                    "accounts": [], "zip_files": []
                },
                "Pakistan": {
                    "code": "+92",
                    "price": 1.50,
                    "names": {"en": "Pakistan", "zh": "巴基斯坦"},
                    "accounts": [], "zip_files": []
                },
                "Indonesia": {
                    "code": "+62",
                    "price": 2.20,
                    "names": {"en": "Indonesia", "zh": "印度尼西亚"},
                    "accounts": [], "zip_files": []
                }
            }
        }
    }
}

product_inventory = DEFAULT_DATABASE["product_inventory"]

# ----------------- FIREBASE HELPER FUNCTIONS -----------------
def fb_get(path):
    try:
        response = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Firebase GET Error ({path}): {e}")
    return None

def fb_put(path, data):
    try:
        response = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=20)
        if response.status_code != 200:
            print(f"Firebase PUT Failed ({path}): {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Firebase PUT Error ({path}): {e}")
    return False

def fb_delete(path):
    try:
        response = requests.delete(f"{FIREBASE_URL}/{path}.json", timeout=15)
        return response.status_code == 200
    except Exception as e:
        print(f"Firebase DELETE Error ({path}): {e}")
    return False

def load_data_from_firebase():
    global user_balances, user_purchases, user_deposits, user_languages, all_users
    global product_inventory, support_admin_username, pending_deposits, used_txids

    b = fb_get("user_balances")
    if b and isinstance(b, dict):
        user_balances = {int(k): float(v) for k, v in b.items() if v is not None}

    p = fb_get("user_purchases")
    if p and isinstance(p, dict):
        user_purchases = {int(k): v for k, v in p.items() if v is not None}

    d = fb_get("user_deposits")
    if d and isinstance(d, dict):
        user_deposits = {int(k): v for k, v in d.items() if v is not None}

    l = fb_get("user_languages")
    if l and isinstance(l, dict):
        user_languages = {int(k): v for k, v in l.items() if v is not None}

    u = fb_get("all_users")
    if u and isinstance(u, dict):
        all_users = set(int(k) for k, v in u.items() if v)

    pd = fb_get("pending_deposits")
    if pd and isinstance(pd, dict):
        pending_deposits = pd

    tx = fb_get("used_txids")
    if tx and isinstance(tx, list):
        used_txids = set(tx)
    elif tx and isinstance(tx, dict):
        used_txids = set(tx.keys())

    inv = fb_get("product_inventory")
    if inv and isinstance(inv, dict):
        if "Countries" in inv and "items" in inv["Countries"]:
            for c_key, c_val in inv["Countries"]["items"].items():
                if "accounts" not in c_val or c_val["accounts"] is None:
                    c_val["accounts"] = []
                if "zip_files" not in c_val or c_val["zip_files"] is None:
                    c_val["zip_files"] = []
                else:
                    for zf in c_val["zip_files"]:
                        if "extracted_files" not in zf or zf["extracted_files"] is None:
                            zf["extracted_files"] = []
        product_inventory = inv

    sup = fb_get("support_admin_username")
    if sup:
        support_admin_username = sup

def ensure_user_registered(user_id):
    is_new = False
    if user_id not in all_users:
        all_users.add(user_id)
        is_new = True
    if user_id not in user_balances:
        user_balances[user_id] = 0.00
    if user_id not in user_purchases:
        user_purchases[user_id] = []
    if user_id not in user_deposits:
        user_deposits[user_id] = []
    if is_new:
        save_user_data(user_id)

def save_user_data(user_id):
    fb_put(f"user_balances/{user_id}", user_balances.get(user_id, 0.0))
    fb_put(f"user_purchases/{user_id}", user_purchases.get(user_id, []))
    fb_put(f"user_deposits/{user_id}", user_deposits.get(user_id, []))
    fb_put(f"user_languages/{user_id}", user_languages.get(user_id, "en"))
    fb_put(f"all_users/{user_id}", True)

def save_inventory():
    return fb_put("product_inventory", product_inventory)

def save_support():
    fb_put("support_admin_username", support_admin_username)

def save_pending_deposit(dep_id, data):
    fb_put(f"pending_deposits/{dep_id}", data)

def remove_pending_deposit(dep_id):
    fb_delete(f"pending_deposits/{dep_id}")

def save_used_txids():
    fb_put("used_txids", list(used_txids))

print("Initializing & Loading data from Firebase...")
load_data_from_firebase()

def setup_bot_startup():
    try:
        commands = [
            telebot.types.BotCommand("/start", "Re-start Bot & Open Menu"),
            telebot.types.BotCommand("/stock", "View Available Products & Stock")
        ]
        bot.set_my_commands(commands)
        if RENDER_URL:
            clean_render_url = RENDER_URL.rstrip("/")
            current_webhook = bot.get_webhook_info().url
            target_webhook = f"{clean_render_url}/{TOKEN}"
            if current_webhook != target_webhook:
                bot.remove_webhook()
                time.sleep(0.5)
                bot.set_webhook(url=target_webhook)
                print(f"Webhook set to: {target_webhook}")
    except Exception as e:
        print(f"Startup webhook/command setup warning: {e}")

setup_bot_startup()
# ----------------- END FIREBASE & STARTUP HELPERS -----------------

def is_admin(user_id):
    return int(user_id) in ADMIN_IDS

LANG = {
    "en": {
        "welcome": (
            "🌈 Welcome to Soe Min’s Shop!\n"
            "Your trusted marketplace for Telegram Accounts (Session+Json/TData).\n\n"
            "📦 Available Services\n"
            "• Telegram Accounts (Session+Json/TData)\n"
            "• Wholesale & Retail\n"
            "• Instant Delivery\n"
            "• Automatic Balance & Order System\n\n"
            "📖 How to Use\n"
            "1️⃣ Use /start to open the main menu.\n"
            "2️⃣ Recharge your balance.\n"
            "3️⃣ Browse available products.\n"
            "4️⃣ Complete your purchase and receive your files instantly.\n\n"
            "⚠️ Important\n"
            "• Please place a small test order before making bulk purchases.\n"
            "• Check your order immediately after delivery.\n"
            "• Contact support as soon as possible if you experience any issues.\n\n"
            "👨‍💻 Support: {support_user}\n\n"
            "📦 Stock: Use /stock to view the latest available products and inventory.\n\n"
            "🚀 Thank you for choosing Soe Min’s Shop!\n"
            "💙 We wish you successful business!"
        ),
        "products": "📁 Select a country:",
        "account": "◆ PERSONAL CENTER / ACCOUNT\n────────────────────────\nUser ID: {user_id}\nUsername: {username}\nBalance: ${balance:.2f}\nPurchased: {purchased_total}",
        "deposit": (
            "💰 Please select your recharge amount below.\n\n"
            "✅ Please make sure to pay the exact amount shown on your invoice.\n\n"
            "💳 Available Payment Methods:\n\n"
            "• 🔗 USDT (TRC20)\n"
            "• 🔗 USDT (BEP20)\n\n"
            "After selecting your recharge amount, choose your preferred payment method to continue."
        ),
        "support": "👉 {support_user}",
        "rules": (
            "⚠️ Platform Rules & Notice\n"
            "────────────────────────\n"
            "1. All digital products are checked before delivery.\n"
            "2. Please verify your account immediately after purchase.\n"
            "3. Deposits are non-refundable once credited to your balance.\n"
            "4. Always send the exact USDT amount on the selected network.\n"
            "5. For any issues, contact customer service: {support_user}\n\n"
            "Precautions\n"
            "• Only lawful digital items.\n"
            "• Obey local laws & platform terms.\n"
            "• Download zip immediately."
        ),
        "language": "🌐 Language Settings\n\nPlease click the button below to switch language:",
        "admin": "🛠️ Welcome to Admin Panel\n\nChoose an option below:",
        "menu_products": "🛒 Products",
        "menu_account": "👤 Personal Center",
        "menu_deposit": "🪙 Recharge",
        "menu_support": "📞 Contact Customer Service",
        "menu_lang": "🌐 Language",
        "menu_rules": "⚠️ Rules",
        "menu_admin": "🛠️ Admin Panel",
        "select_qty": "🔢 Select Quantity:\n\nChoose how many items you want to buy:",
        "select_country": "🌍 Select a country & phone code:",
        "back": "< Back",
        "main_menu": "< Main Menu",
        "other_amt": "Other Amount",
        "other_qty": "Other Quantity",
        "cancel": "< Cancel",
        "stock": "Stock",
        "price": "Price",
        "purchase_success": "✅ Purchase Successful!",
        "insufficient_stock": "❌ Insufficient stock! Available stock: {stock} items.",
        "insufficient_balance": "❌ Insufficient balance!\nRequired: ${required:.2f}\nYour Balance: ${balance:.2f}\nPlease deposit first.",
        "balance_text": "Remaining Balance:",
        "deposit_select_amt": "Enter custom deposit amount (USDT, Min $5):",
        "min_network": "❌ Minimum deposit for this network is $5.00!",
        "min_deposit_err": "❌ Minimum deposit amount is ${min_limit:.2f}. Please enter again:",
        "invalid_amount": "❌ Invalid amount. Please enter a valid number (e.g., 5 or 10):",
        "selected_amount_pay": "💰 Selected Amount: ${amount:.2f}\n\nPlease select your preferred payment method:",
        "pay_trc20": "💵 USDT (TRC20) (Min $5)",
        "pay_bep20": "💵 USDT (BEP20) (Min $5)",
        "send_txid_btn": "📤 Send Order Id / TxID",
        "txid_prompt": "📤 Please send your payment Transaction ID (TxID) or Proof:\n\nOrder ID: {order_id}",
        "proof_sent": "📤 Your payment proof / Order ID has been sent to the admin successfully. Please wait for verification.",
        "txid_used": "❌ This Order ID / TxID has already been used! Each ID can only be used once for a deposit.",
        "country_detail": "{flag} Country: {name} ({code})\n\n💰 Price: ${price:.2f}\n📦 Available Stock: {stock} items\n\nClick below to proceed to quantity selection:",
        "select_qty_btn": "🛒 Select Quantity",
        "qty_header": "🔢 Select Quantity for {flag} {name}:\n\nChoose how many items you want to buy:",
        "enter_custom_qty": "🔢 Please enter the quantity you want to buy (e.g., 4, 15):",
        "invalid_qty_zero": "❌ Please enter a valid quantity greater than 0:",
        "invalid_qty_num": "❌ Invalid number! Please enter a valid integer (e.g., 2, 5):",
        "product_not_found": "❌ Product not found.",
        "deliver_zip_caption": "✅ Purchase Successful!\n\n{flag} Country: {name}\n📦 File: {file}\n🔐 2FA & ZIP Password: {tfa}\n💵 Paid: ${price:.2f}\n\nRemaining Balance: ${balance:.2f}",
        "deliver_acc_text": "✅ Purchase Successful!\n\n{flag} Country: {name}\n📱 Telegram Number: {num}\n🔐 2FA Code: {tfa}\n💵 Paid: ${price:.2f}\n\nRemaining Balance: ${balance:.2f}",
        "deliver_err": "❌ Error delivering item: {err}",
        "cancel_op": "❌ Current operation cancelled.",
        "dep_accepted_user": "✅ Your deposit has been accepted successfully!\n\n💰 ${amount:.2f} has been credited to your account.",
        "dep_rejected_user": "❌ Sorry, your deposit request has been rejected by admin.\nOrder ID: {order_id}",
        "order_box": (
            "[ ORDER CREATED ]  {currency}\n"
            "──────────────────────\n"
            "  Send     ·  <code>{send_num}</code> USDT\n"
            "  Credit   ·  {credit}\n"
            "  Order    ·  <code>{order_id}</code>\n"
            "  Network  ·  {network}\n"
            "  Address  ·  <code>{address}</code>\n"
            "  Expires  ·  {expires}\n"
            "──────────────────────\n"
            "Send exactly {send_val}, including all decimals. This amount was converted from ${amount:.2f} at the Binance price when the order was created and ends in a unique identifier; ${amount:.2f} is credited when it arrives.\n"
            "Send native assets/tokens on the {network} network only.\n"
            "Your balance will be credited by admin once verified."
        )
    },
    "zh": {
        "welcome": (
            "🌈 欢迎来到 Soe Min’s Shop！\n"
            "您值得信赖的 Telegram 账号 (Session+Json/TData) 交易平台。\n\n"
            "📦 提供服务\n"
            "• Telegram 账号 (Session+Json/TData)\n"
            "• 批发与零售\n"
            "• 自动即时发货\n"
            "• 自动余额与订单系统\n\n"
            "📖 使用指南\n"
            "1️⃣ 发送 /start 打开主菜单。\n"
            "2️⃣ 为您的账户充值余额。\n"
            "3️⃣ 浏览并选择可用商品。\n"
            "4️⃣ 完成购买并立即获取文件。\n\n"
            "⚠️ 重要提示\n"
            "• 大批量购买前请先小额测试下单。\n"
            "• 收货后请立即检查您的订单。\n"
            "• 如遇任何问题，请尽快联系客服。\n\n"
            "👨‍💻 客服支持：{support_user}\n\n"
            "📦 库存查询：发送 /stock 查看最新可用商品及库存。\n\n"
            "🚀 感谢选择 Soe Min’s Shop！\n"
            "💙 祝您生意兴隆！"
        ),
        "products": "📁 选择国家：",
        "account": "◆ 个人中心 / 账户信息\n────────────────────────\n用户 ID: {user_id}\n用户名: {username}\n余额: ${balance:.2f}\n已购总额: {purchased_total}",
        "deposit": (
            "💰 请在下方选择您的充值金额。\n\n"
            "✅ 请务必支付订单上显示的准确金额。\n\n"
            "💳 可用支付方式：\n\n"
            "• 🔗 USDT (TRC20)\n"
            "• 🔗 USDT (BEP20)\n\n"
            "选择充值金额后，请选择您的首选支付方式继续。"
        ),
        "support": "👉 {support_user}",
        "rules": (
            "⚠️ 平台规则与须知\n"
            "────────────────────────\n"
            "1. 所有数字商品在发货前均经过严格检测。\n"
            "2. 购买后请立即检查并验证您的账户。\n"
            "3. 充值金额一旦入账至您的余额，恕不退款。\n"
            "4. 请务必在所选网络上转账准确的 USDT 金额。\n"
            "5. 如有任何问题，请联系客服：{support_user}\n\n"
            "注意事项 (Precautions)\n"
            "• 仅限合法数字商品。\n"
            "• 遵守当地法律及平台条款。\n"
            "• 购买后请立即下载压缩包 (ZIP)。"
        ),
        "language": "🌐 语言设置\n\n请点击下方按钮切换语言：",
        "admin": "🛠️ 欢迎来到管理面板\n\n在下方选择一个选项：",
        "menu_products": "🛒 产品中心",
        "menu_account": "👤 个人中心",
        "menu_deposit": "🪙 账户充值",
        "menu_support": "📞 联系客服",
        "menu_lang": "🌐 语言设置",
        "menu_rules": "⚠️ 规则说明",
        "menu_admin": "🛠️ 管理面板",
        "select_qty": "🔢 选择数量：\n\n请选择您要购买的数量：",
        "select_country": "🌍 选择国家及电话区号：",
        "back": "< 返回",
        "main_menu": "< 主菜单",
        "other_amt": "其他金额",
        "other_qty": "其他数量",
        "cancel": "< 取消",
        "stock": "库存",
        "price": "价格",
        "purchase_success": "✅ 购买成功！",
        "insufficient_stock": "❌ 库存不足！可用库存：{stock} 件。",
        "insufficient_balance": "❌ 余额不足！\n需要：${required:.2f}\n当前余额：${balance:.2f}\n请先进行充值。",
        "balance_text": "剩余余额：",
        "deposit_select_amt": "请输入自定义充值金额 (USDT，最低 $5)：",
        "min_network": "❌ 该网络最低充值金额为 $5.00！",
        "min_deposit_err": "❌ 最低充值金额为 ${min_limit:.2f}，请重新输入：",
        "invalid_amount": "❌ 金额无效，请输入有效的数字（例如：5 或 10）：",
        "selected_amount_pay": "💰 已选金额：${amount:.2f}\n\n请选择您的首选付款方式：",
        "pay_trc20": "💵 USDT (TRC20) (最低 $5)",
        "pay_bep20": "💵 USDT (BEP20) (最低 $5)",
        "send_txid_btn": "📤 发送订单号 / 交易单号 (TxID)",
        "txid_prompt": "📤 请发送您的付款交易单号 (TxID) 或付款截图凭证：\n\n订单号：{order_id}",
        "proof_sent": "📤 您的付款凭证 / 订单号已成功发送给管理员，请等待验证。",
        "txid_used": "❌ 此订单号 / TxID 已被使用！每个单号只能用于充值一次。",
        "country_detail": "{flag} 国家：{name} ({code})\n\n💰 单价：${price:.2f}\n📦 可用库存：{stock} 件\n\n请点击下方按钮选择购买数量：",
        "select_qty_btn": "🛒 选择数量",
        "qty_header": "🔢 选择 {flag} {name} 的购买数量：\n\n请选择您要购买的数量：",
        "enter_custom_qty": "🔢 请输入您要购买的数量（例如：4、15）：",
        "invalid_qty_zero": "❌ 请输入大于 0 的有效数量：",
        "invalid_qty_num": "❌ 数字无效！请输入有效的整数（例如：2、5）：",
        "product_not_found": "❌ 未找到该产品。",
        "deliver_zip_caption": "✅ 购买成功！\n\n{flag} 国家：{name}\n📦 文件：{file}\n🔐 二次验证及压缩包密码：{tfa}\n💵 实付金额：${price:.2f}\n\n剩余余额：${balance:.2f}",
        "deliver_acc_text": "✅ 购买成功！\n\n{flag} 国家：{name}\n📱 电报号码：{num}\n🔐 二次验证码：{tfa}\n💵 实付金额：${price:.2f}\n\n剩余余额：${balance:.2f}",
        "deliver_err": "❌ 发货时出错：{err}",
        "cancel_op": "❌ 当前操作已取消。",
        "dep_accepted_user": "✅ 您的充值申请已审核通过！\n\n💰 ${amount:.2f} 已成功入账到您的账户。",
        "dep_rejected_user": "❌ 抱歉，您的充值申请已被管理员拒绝。\n订单号：{order_id}",
        "order_box": (
            "[ 订单已创建 ]  {currency}\n"
            "──────────────────────\n"
            "  转账金额  ·  <code>{send_num}</code> USDT\n"
            "  到账金额  ·  {credit}\n"
            "  订单编号  ·  <code>{order_id}</code>\n"
            "  转账网络  ·  {network}\n"
            "  收款地址  ·  <code>{address}</code>\n"
            "  创建时间  ·  {expires}\n"
            "──────────────────────\n"
            "请准确转账 {send_val}（包含所有小数位）。该金额按创建订单时的币安汇率由 ${amount:.2f} 换算并带有唯一识别尾数；到账后将自动为您充值 ${amount:.2f}。\n"
            "请仅通过 {network} 网络转账原生资产/代币。\n"
            "管理员验证通过后将立即为您增加账户余额。"
        )
    }
}

def get_lang(user_id):
    return user_languages.get(user_id, "en")

def remove_old_reply_keyboard(chat_id):
    """Removes the old bottom reply keyboard silently so there is no duplicate menu."""
    try:
        msg = bot.send_message(chat_id, "⏳", reply_markup=types.ReplyKeyboardRemove())
        bot.delete_message(chat_id, msg.message_id)
    except Exception:
        pass

def send_colored_main_menu(chat_id, text, user_id):
    remove_old_reply_keyboard(chat_id)
    lang_code = get_lang(user_id)
    t = LANG[lang_code]

    inline_keyboard = [
        [
            {"text": t["menu_products"], "callback_data": "menu_products", "style": "primary"},
            {"text": t["menu_deposit"], "callback_data": "menu_deposit", "style": "success"}
        ],
        [
            {"text": t["menu_support"], "callback_data": "menu_support", "style": "danger"},
            {"text": t["menu_account"], "callback_data": "menu_account", "style": "primary"}
        ],
        [
            {"text": t["menu_lang"], "callback_data": "menu_lang", "style": "success"},
            {"text": t["menu_rules"], "callback_data": "menu_rules", "style": "danger"}
        ]
    ]

    if is_admin(user_id):
        inline_keyboard.append([
            {"text": t["menu_admin"], "callback_data": "menu_admin", "style": "primary"}
        ])

    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": json.dumps({"inline_keyboard": inline_keyboard})
    }
    try:
        res = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data=payload, timeout=15)
        if res.status_code == 200:
            return
    except Exception as e:
        print(f"Colored menu send warning: {e}")

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(t["menu_products"], callback_data="menu_products"),
        types.InlineKeyboardButton(t["menu_deposit"], callback_data="menu_deposit"),
        types.InlineKeyboardButton(t["menu_support"], callback_data="menu_support"),
        types.InlineKeyboardButton(t["menu_account"], callback_data="menu_account"),
        types.InlineKeyboardButton(t["menu_lang"], callback_data="menu_lang"),
        types.InlineKeyboardButton(t["menu_rules"], callback_data="menu_rules")
    )
    if is_admin(user_id):
        markup.add(types.InlineKeyboardButton(t["menu_admin"], callback_data="menu_admin"))
    bot.send_message(chat_id, text, reply_markup=markup)

def get_main_menu_inline_back(user_id):
    t = LANG[get_lang(user_id)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["main_menu"], callback_data="go_main_menu"))
    return markup

def get_select_amount_keyboard(user_id):
    t = LANG[get_lang(user_id)]
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("5 USDT", callback_data="amt_5"),
        types.InlineKeyboardButton("10 USDT", callback_data="amt_10"),
        types.InlineKeyboardButton("20 USDT", callback_data="amt_20"),
        types.InlineKeyboardButton("50 USDT", callback_data="amt_50"),
        types.InlineKeyboardButton("100 USDT", callback_data="amt_100"),
        types.InlineKeyboardButton(t["other_amt"], callback_data="amt_other"),
        types.InlineKeyboardButton(t["cancel"], callback_data="dep_cancel")
    )
    return markup

def get_payment_methods_keyboard(user_id):
    t = LANG[get_lang(user_id)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(t["pay_trc20"], callback_data="order_usdt_trc20"),
        types.InlineKeyboardButton(t["pay_bep20"], callback_data="order_usdt_bep20"),
        types.InlineKeyboardButton(t["cancel"], callback_data="dep_cancel")
    )
    return markup

def get_order_created_keyboard(net_code, order_id, user_id):
    t = LANG[get_lang(user_id)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["send_txid_btn"], callback_data=f"send_order_id_{order_id}"))
    markup.add(types.InlineKeyboardButton(t["back"], callback_data="dep_confirm"))
    markup.add(types.InlineKeyboardButton(t["main_menu"], callback_data="go_main_menu"))
    return markup

def get_quantity_keyboard(item_key, user_id):
    t = LANG[get_lang(user_id)]
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("1", callback_data=f"qty_{item_key}_1"),
        types.InlineKeyboardButton("2", callback_data=f"qty_{item_key}_2"),
        types.InlineKeyboardButton("3", callback_data=f"qty_{item_key}_3"),
        types.InlineKeyboardButton("5", callback_data=f"qty_{item_key}_5"),
        types.InlineKeyboardButton("10", callback_data=f"qty_{item_key}_10"),
        types.InlineKeyboardButton(t["other_qty"], callback_data=f"qty_other_{item_key}"),
        types.InlineKeyboardButton(t["back"], callback_data="back_to_products_menu")
    )
    return markup

def get_account_keyboard(user_id):
    lang_code = get_lang(user_id)
    t = LANG[lang_code]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["main_menu"], callback_data="go_main_menu"))
    return markup

def get_products_countries_keyboard(user_id):
    lang_code = get_lang(user_id)
    t = LANG[lang_code]
    markup = types.InlineKeyboardMarkup(row_width=1)
    if "Countries" in product_inventory and "items" in product_inventory["Countries"]:
        for country, data in product_inventory["Countries"]["items"].items():
            c_code = data.get("code", "")
            raw_name = data.get("names", {}).get(lang_code, country)
            clean_name = format_country_display_name(country, raw_name, lang_code)
            flag = get_country_flag(country, c_code)
            zip_stock_count = sum(len(zf.get("extracted_files", [])) for zf in data.get("zip_files", []))
            total_stock = len(data.get("accounts", [])) + zip_stock_count
            btn_text = f"{flag} {clean_name} ({c_code}) [{total_stock}]"
            markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"select_country_{country}"))
    markup.add(types.InlineKeyboardButton(t["main_menu"], callback_data="go_main_menu"))
    return markup

def get_language_keyboard(user_id):
    t = LANG[get_lang(user_id)]
    current_lang = get_lang(user_id)
    btn_text = "🇨🇳 切换到中文" if current_lang == "en" else "🇬🇧 切换为英文 (Switch to English)"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(btn_text, callback_data="lang_toggle"))
    markup.add(types.InlineKeyboardButton(t["main_menu"], callback_data="go_main_menu"))
    return markup

def get_admin_panel_keyboard(user_id):
    t = LANG[get_lang(user_id)]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast_start"),
        types.InlineKeyboardButton("👥 Management (Users & Balance)", callback_data="admin_management"),
        types.InlineKeyboardButton("➕ Add New Country", callback_data="admin_add_country"),
        types.InlineKeyboardButton("🗂️ Add Zip File Stock", callback_data="admin_add_zip_menu"),
        types.InlineKeyboardButton("✏️ Edit / Delete Countries", callback_data="admin_edit_delete_countries_menu"),
        types.InlineKeyboardButton("📞 Change Support Username", callback_data="admin_change_support"),
        types.InlineKeyboardButton(t["main_menu"], callback_data="go_main_menu")
    )
    return markup

def get_management_keyboard(user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    total_users = len(all_users)
    markup.add(types.InlineKeyboardButton(f"👥 All Users List ({total_users})", callback_data="mgmt_users_0"))
    markup.add(types.InlineKeyboardButton("🔍 Search User by ID", callback_data="mgmt_search_user"))
    markup.add(types.InlineKeyboardButton("💰 Top Balance Users", callback_data="mgmt_top_balance"))
    markup.add(types.InlineKeyboardButton("🛠️ Back to Admin Panel", callback_data="admin_back"))
    return markup

def get_users_list_keyboard(page=0, per_page=10):
    markup = types.InlineKeyboardMarkup(row_width=1)
    users_sorted = sorted(list(all_users), reverse=True)
    total = len(users_sorted)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    page = max(0, min(page, total_pages - 1))
    start = page * per_page
    end = start + per_page
    for uid in users_sorted[start:end]:
        bal = user_balances.get(int(uid), 0.0)
        crown = " 👑" if is_admin(uid) else ""
        markup.add(types.InlineKeyboardButton(f"👤 {uid}{crown} | 💰 ${bal:.2f}", callback_data=f"mgmt_user_{uid}"))
    nav = []
    if page > 0:
        nav.append(types.InlineKeyboardButton("⬅️ Prev", callback_data=f"mgmt_users_{page-1}"))
    if page < total_pages - 1:
        nav.append(types.InlineKeyboardButton("Next ➡️", callback_data=f"mgmt_users_{page+1}"))
    if nav:
        markup.add(*nav)
    markup.add(types.InlineKeyboardButton(f"📄 Page {page+1}/{total_pages} | Total: {total}", callback_data="noop"))
    markup.add(types.InlineKeyboardButton("🔙 Back to Management", callback_data="admin_management"))
    return markup, total_pages, total

def get_user_detail_keyboard(target_uid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Balance", callback_data=f"mgmt_bal_add_{target_uid}"),
        types.InlineKeyboardButton("➖ Subtract Balance", callback_data=f"mgmt_bal_sub_{target_uid}"),
        types.InlineKeyboardButton("✏️ Set Balance", callback_data=f"mgmt_bal_set_{target_uid}"),
        types.InlineKeyboardButton("🔄 Reset to $0", callback_data=f"mgmt_bal_reset_{target_uid}"),
    )
    markup.add(
        types.InlineKeyboardButton("📦 Purchase History", callback_data=f"mgmt_hist_pur_{target_uid}"),
        types.InlineKeyboardButton("💰 Deposit History", callback_data=f"mgmt_hist_dep_{target_uid}"),
    )
    markup.add(types.InlineKeyboardButton("🔙 Back to Users List", callback_data="mgmt_users_0"))
    markup.add(types.InlineKeyboardButton("🛠️ Back to Admin Panel", callback_data="admin_back"))
    return markup

def get_user_detail_text(target_uid):
    bal = user_balances.get(int(target_uid), 0.0)
    pur = user_purchases.get(int(target_uid), [])
    dep = user_deposits.get(int(target_uid), [])
    lang = user_languages.get(int(target_uid), "en")
    is_adm = "Yes 👑" if is_admin(target_uid) else "No"
    return (
        f"👤 User Management\n"
        f"──────────────────────\n"
        f"🆔 User ID: {target_uid}\n"
        f"💰 Balance: ${bal:.2f}\n"
        f"🌐 Language: {lang}\n"
        f"👑 Admin: {is_adm}\n"
        f"📦 Total Purchases: {len(pur)}\n"
        f"💰 Total Deposits: {len(dep)}\n"
        f"──────────────────────\n"
        f"Select an option to edit balance:"
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    user_states.pop(user_id, None)
    ensure_user_registered(user_id)
    lang_code = get_lang(user_id)
    welcome_text = LANG[lang_code]["welcome"].format(support_user=support_admin_username)
    send_colored_main_menu(message.chat.id, welcome_text, user_id)

@bot.message_handler(commands=['stock'])
def stock_command(message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    ensure_user_registered(user_id)
    t = LANG[get_lang(user_id)]
    bot.send_message(message.chat.id, t["products"], reply_markup=get_products_countries_keyboard(user_id))

@bot.message_handler(commands=['admin'])
def admin_command(message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        msg = "❌ 您无权访问管理面板。" if get_lang(user_id) == "zh" else "❌ You are not authorized to use the admin panel."
        bot.send_message(message.chat.id, msg)
        return
    user_states[user_id] = "waiting_for_admin_password"
    bot.send_message(message.chat.id, "🔐 Please enter the Admin Panel password:")

@bot.message_handler(commands=['cancel'])
def cancel_operation(message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    t = LANG[get_lang(user_id)]
    bot.send_message(message.chat.id, t["cancel_op"], reply_markup=get_main_menu_inline_back(user_id))

@bot.message_handler(content_types=['document'])
def handle_document_uploads(message):
    user_id = message.from_user.id
    if user_states.get(user_id) == "waiting_for_zip_file" and is_admin(user_id):
        country_name = temp_admin_data.get(user_id)
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        if country_name in product_inventory["Countries"]["items"]:
            temp_admin_data[f"zip_bytes_{user_id}"] = downloaded_file
            user_states[user_id] = "waiting_for_zip_2fa"
            response_msg = (
                f"✅ ZIP File uploaded successfully for {country_name}!\n\n"
                f"🔐 Now, please send the Password / 2FA Code for this ZIP file so it can be verified and read properly:"
            )
            bot.send_message(message.chat.id, response_msg)
        else:
            bot.send_message(message.chat.id, "❌ Invalid country selected.")
            user_states.pop(user_id, None)

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio'])
def handle_all_messages(message):
    global support_admin_username
    user_id = message.from_user.id
    ensure_user_registered(user_id)

    lang_code = get_lang(user_id)
    t = LANG[lang_code]
    text = message.text if message.text else ""

    # 1. If user clicks any leftover old ReplyKeyboard button, clean it up and open the requested page
    is_products = text in [LANG["en"]["menu_products"], LANG["zh"]["menu_products"], "🛍️ Products", "🛍️ 产品中心"]
    is_account = text in [LANG["en"]["menu_account"], LANG["zh"]["menu_account"]]
    is_deposit = text in [LANG["en"]["menu_deposit"], LANG["zh"]["menu_deposit"], "💰 Recharge", "💰 账户充值"]
    is_support = text in [LANG["en"]["menu_support"], LANG["zh"]["menu_support"], "💬 Contact Customer Service", "💬 联系客服"]
    is_lang = text in [LANG["en"]["menu_lang"], LANG["zh"]["menu_lang"]]
    is_rules = text in [LANG["en"]["menu_rules"], LANG["zh"]["menu_rules"]]
    is_admin_menu = text in [LANG["en"]["menu_admin"], LANG["zh"]["menu_admin"]]

    if any([is_products, is_account, is_deposit, is_support, is_lang, is_rules, is_admin_menu]):
        user_states.pop(user_id, None)
        remove_old_reply_keyboard(message.chat.id)

        if is_lang:
            bot.send_message(message.chat.id, t["language"], reply_markup=get_language_keyboard(user_id))
            return
        elif is_admin_menu:
            if not is_admin(user_id):
                bot.send_message(message.chat.id, "❌ 无权访问。" if lang_code == "zh" else "❌ Unauthorized.")
                return
            user_states[user_id] = "waiting_for_admin_password"
            bot.send_message(message.chat.id, "🔐 Please enter the Admin Panel password:")
            return
        elif is_products:
            bot.send_message(message.chat.id, t["products"], reply_markup=get_products_countries_keyboard(user_id))
            return
        elif is_deposit:
            user_states[user_id] = "waiting_for_deposit"
            bot.send_message(message.chat.id, t["deposit"], reply_markup=get_select_amount_keyboard(user_id))
            return
        elif is_account:
            user = message.from_user
            no_user_str = "无" if lang_code == "zh" else "N/A"
            username = f"@{user.username}" if user.username else no_user_str
            balance_val = user_balances.get(user_id, 0.00)
            purchased_total = len(user_purchases.get(user_id, []))
            account_text = t["account"].format(user_id=user.id, username=username, balance=balance_val, purchased_total=purchased_total)
            bot.send_message(message.chat.id, account_text, reply_markup=get_account_keyboard(user_id))
            return
        elif is_support:
            support_msg = t["support"].format(support_user=support_admin_username)
            bot.send_message(message.chat.id, support_msg, reply_markup=get_account_keyboard(user_id))
            return
        elif is_rules:
            rules_msg = t["rules"].format(support_user=support_admin_username)
            bot.send_message(message.chat.id, rules_msg, reply_markup=get_account_keyboard(user_id))
            return

    # 2. Admin-only states
    state = user_states.get(user_id, "")

    if state == "waiting_for_admin_password" and is_admin(user_id):
        if text.strip() == ADMIN_PASSWORD:
            user_states.pop(user_id, None)
            bot.send_message(message.chat.id, "🛠️ Welcome to Admin Panel\n\nChoose an option below:", reply_markup=get_admin_panel_keyboard(user_id))
        else:
            bot.send_message(message.chat.id, "❌ Incorrect password! Please enter the Admin Panel password again (or send /cancel):")
        return

    if state == "waiting_for_new_support_username" and is_admin(user_id):
        if not text:
            bot.send_message(message.chat.id, "❌ Please enter a valid username:")
            return
        new_support = text.strip()
        if not new_support.startswith("@"):
            new_support = "@" + new_support
        support_admin_username = new_support
        save_support()
        user_states.pop(user_id, None)
        bot.send_message(
            message.chat.id,
            f"✅ Support admin username successfully updated to: {support_admin_username}",
            reply_markup=get_admin_panel_keyboard(user_id)
        )
        return

    if state == "waiting_for_mgmt_search" and is_admin(user_id):
        user_states.pop(user_id, None)
        try:
            target = int(text.strip())
        except Exception:
            bot.send_message(message.chat.id, "❌ Invalid User ID! Please enter numbers only (e.g., 123456789):", reply_markup=get_admin_panel_keyboard(user_id))
            return
        ensure_user_registered(target)
        bot.send_message(message.chat.id, get_user_detail_text(target), reply_markup=get_user_detail_keyboard(target))
        return

    if state.startswith("waiting_for_mgmt_bal_") and is_admin(user_id):
        parts = state.replace("waiting_for_mgmt_bal_", "").split("_")
        action = parts[0]
        target_uid = int(parts[1])
        try:
            amount = float(text.strip())
            if amount < 0:
                raise ValueError()
        except Exception:
            bot.send_message(message.chat.id, "❌ Invalid amount! Please enter a positive number (e.g., 10 or 5.50):")
            return
        old_bal = user_balances.get(target_uid, 0.0)
        if action == "add":
            new_bal = old_bal + amount
            msg_action = f"➕ Added ${amount:.2f}"
        elif action == "sub":
            new_bal = max(0.0, old_bal - amount)
            msg_action = f"➖ Subtracted ${amount:.2f}"
        elif action == "set":
            new_bal = amount
            msg_action = f"✏️ Set to ${amount:.2f}"
        else:
            new_bal = old_bal
            msg_action = ""
        user_balances[target_uid] = round(new_bal, 2)
        save_user_data(target_uid)
        user_states.pop(user_id, None)
        bot.send_message(
            message.chat.id,
            f"✅ Balance Updated!\n\n👤 User ID: {target_uid}\n{msg_action}\n💰 Old Balance: ${old_bal:.2f}\n💰 New Balance: ${new_bal:.2f}",
            reply_markup=get_user_detail_keyboard(target_uid)
        )
        try:
            target_lang = get_lang(target_uid)
            notify_txt = (
                f"💰 管理员已更新您的账户余额！\n\n当前余额：${new_bal:.2f}"
                if target_lang == "zh"
                else f"💰 Your balance has been updated by Admin!\n\nNew Balance: ${new_bal:.2f}"
            )
            bot.send_message(target_uid, notify_txt)
        except Exception:
            pass
        return

    if state == "waiting_for_new_country" and is_admin(user_id):
        if not text:
            bot.send_message(message.chat.id, "❌ Please enter a country name:")
            return
        c_name = strip_leading_flag(text.strip()).capitalize()
        if c_name not in product_inventory["Countries"]["items"]:
            temp_admin_data[user_id] = c_name
            user_states[user_id] = "waiting_for_country_code"
            bot.send_message(message.chat.id, f"📱 Now enter country phone code for {c_name} (e.g., +880):")
        else:
            bot.send_message(message.chat.id, f"⚠️ Country {c_name} already exists.")
            user_states.pop(user_id, None)
        return

    if state == "waiting_for_country_code" and is_admin(user_id):
        c_code = text.strip()
        c_name = temp_admin_data.get(user_id)
        if c_name and c_code:
            zh_name = format_country_display_name(c_name, c_name, "zh")
            product_inventory["Countries"]["items"][c_name] = {
                "code": c_code,
                "price": 1.00,
                "names": {"en": c_name, "zh": zh_name},
                "accounts": [],
                "zip_files": []
            }
            save_inventory()
            flag = get_country_flag(c_name, c_code)
            bot.send_message(message.chat.id, f"✅ Country {flag} {c_name} ({c_code}) added successfully!", reply_markup=get_admin_panel_keyboard(user_id))
        user_states.pop(user_id, None)
        return

    if state.startswith("waiting_for_edit_price_") and is_admin(user_id):
        country_name = state.replace("waiting_for_edit_price_", "")
        try:
            new_price = float(text.strip())
            if new_price < 0:
                raise ValueError()
            if country_name in product_inventory["Countries"]["items"]:
                product_inventory["Countries"]["items"][country_name]["price"] = new_price
                save_inventory()
                bot.send_message(message.chat.id, f"✅ Price for {country_name} successfully updated to ${new_price:.2f}!", reply_markup=get_admin_panel_keyboard(user_id))
            else:
                bot.send_message(message.chat.id, "❌ Country not found.")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Invalid price! Please enter a valid number (e.g., 1.50 or 2):")
        user_states.pop(user_id, None)
        return

    if state.startswith("waiting_for_rename_country_") and is_admin(user_id):
        old_country = state.replace("waiting_for_rename_country_", "")
        new_country = strip_leading_flag(text.strip()).capitalize()
        proto_items = product_inventory["Countries"]["items"]
        if new_country in proto_items:
            bot.send_message(message.chat.id, f"⚠️ Country {new_country} already exists!")
        elif old_country in proto_items:
            proto_items[new_country] = proto_items.pop(old_country)
            if "names" in proto_items[new_country]:
                proto_items[new_country]["names"]["en"] = new_country
                proto_items[new_country]["names"]["zh"] = format_country_display_name(new_country, new_country, "zh")
            save_inventory()
            bot.send_message(message.chat.id, f"✅ Successfully renamed country {old_country} to {new_country}!", reply_markup=get_admin_panel_keyboard(user_id))
        else:
            bot.send_message(message.chat.id, "❌ Country not found.")
        user_states.pop(user_id, None)
        return

    if state == "waiting_for_broadcast_message" and is_admin(user_id):
        user_states.pop(user_id, None)
        success_count = 0
        fail_count = 0
        bot.send_message(message.chat.id, "⏳ Broadcasting message to all users, please wait...")
        for uid in list(all_users):
            try:
                bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
                success_count += 1
            except Exception:
                fail_count += 1
        bot.send_message(message.chat.id, f"✅ Broadcast Completed!\n\n👥 Successfully sent: {success_count} users\n❌ Failed (Blocked bot): {fail_count} users", reply_markup=get_main_menu_inline_back(user_id))
        return

    if state == "waiting_for_zip_2fa" and is_admin(user_id):
        tfa_code = text.strip()
        country_name = temp_admin_data.get(user_id)
        raw_zip_bytes = temp_admin_data.get(f"zip_bytes_{user_id}")
        if country_name and raw_zip_bytes and tfa_code:
            zip_bytes = io.BytesIO(raw_zip_bytes)
            try:
                with pyzipper.AESZipFile(zip_bytes, 'r') as zf:
                    zf.setpassword(tfa_code.encode('utf-8'))
                    file_list = zf.namelist()
                    valid_files = [f for f in file_list if not f.endswith('/')]
                    if not valid_files:
                        bot.send_message(message.chat.id, "❌ The ZIP archive contains no valid files.", reply_markup=get_admin_panel_keyboard(user_id))
                    else:
                        if "zip_files" not in product_inventory["Countries"]["items"][country_name]:
                            product_inventory["Countries"]["items"][country_name]["zip_files"] = []

                        zip_b64 = base64.b64encode(raw_zip_bytes).decode('utf-8')
                        product_inventory["Countries"]["items"][country_name]["zip_files"].append({
                            "zip_b64": zip_b64,
                            "2fa": tfa_code,
                            "extracted_files": valid_files
                        })
                        saved = save_inventory()
                        if saved:
                            bot.send_message(message.chat.id, f"✅ Successfully added & saved ZIP stock for {country_name}!\n📁 Total valid files: {len(valid_files)}\n🔐 Password / 2FA: {tfa_code}", reply_markup=get_admin_panel_keyboard(user_id))
                        else:
                            bot.send_message(message.chat.id, "⚠️ Stock added in memory but failed to save to Firebase! Check file size or Firebase permissions.", reply_markup=get_admin_panel_keyboard(user_id))
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ Password Error!\nError details: {str(e)}", reply_markup=get_admin_panel_keyboard(user_id))
        user_states.pop(user_id, None)
        temp_admin_data.pop(user_id, None)
        temp_admin_data.pop(f"zip_bytes_{user_id}", None)
        return

    # 3. User Input States
    if state.startswith("waiting_for_txid_"):
        order_id = state.replace("waiting_for_txid_", "")
        trx_text_clean = text.strip() if text else ""

        if trx_text_clean:
            if trx_text_clean.lower() in used_txids:
                bot.send_message(message.chat.id, t["txid_used"])
                return
            used_txids.add(trx_text_clean.lower())
            save_used_txids()

        user_states.pop(user_id, None)
        dep_amt = user_amounts.get(user_id, 5.00)
        dep_id = f"dep_{user_id}_{int(time.time())}"
        dep_data = {
            "user_id": user_id,
            "amount": dep_amt,
            "order_id": order_id,
            "txid": trx_text_clean
        }
        pending_deposits[dep_id] = dep_data
        save_pending_deposit(dep_id, dep_data)

        admin_id = ADMIN_IDS[0]
        user_name = message.from_user.first_name or "N/A"
        username = f"@{message.from_user.username}" if message.from_user.username else "N/A"

        admin_markup = types.InlineKeyboardMarkup(row_width=2)
        admin_markup.add(
            types.InlineKeyboardButton("✅ Accept", callback_data=f"dep_accept_{dep_id}"),
            types.InlineKeyboardButton("❌ Reject", callback_data=f"dep_reject_{dep_id}")
        )

        trx_info = trx_text_clean if trx_text_clean else "Screenshot / Media"
        admin_notification = (
            f"💰 New Deposit Request!\n"
            f"──────────────────────\n"
            f"👤 User: {user_name} ({username})\n"
            f"🆔 User ID: {user_id}\n"
            f"📦 Order ID: {order_id}\n"
            f"💵 Amount: ${dep_amt:.2f}\n"
            f"Trx: {trx_info}\n"
            f"──────────────────────\n"
            f"Click buttons below to Accept or Reject:"
        )
        try:
            bot.copy_message(chat_id=admin_id, from_chat_id=message.chat.id, message_id=message.message_id)
            bot.send_message(admin_id, admin_notification, reply_markup=admin_markup)
        except Exception as e:
            print(f"Failed to send proof to admin: {e}")

        bot.send_message(message.chat.id, t["proof_sent"], reply_markup=get_main_menu_inline_back(user_id))
        return

    if state.startswith("waiting_for_custom_qty_"):
        item_key = state.replace("waiting_for_custom_qty_", "")
        try:
            qty = int(text.strip())
            if qty <= 0:
                bot.send_message(message.chat.id, t["invalid_qty_zero"])
                return
            user_states.pop(user_id, None)
            process_product_purchase(message.chat.id, user_id, item_key, qty)
        except ValueError:
            bot.send_message(message.chat.id, t["invalid_qty_num"])
        return

    if state == "waiting_for_custom_amount":
        try:
            custom_amount = float(text.strip())
            min_limit = 5.00
            if custom_amount < min_limit:
                bot.send_message(message.chat.id, t["min_deposit_err"].format(min_limit=min_limit))
                return
            user_amounts[user_id] = custom_amount
            user_states[user_id] = "waiting_for_payment_method"
            payment_text = t["selected_amount_pay"].format(amount=custom_amount)
            bot.send_message(message.chat.id, payment_text, reply_markup=get_payment_methods_keyboard(user_id))
        except ValueError:
            bot.send_message(message.chat.id, t["invalid_amount"])
        return

def process_product_purchase(chat_id, user_id, item_key, qty):
    lang_code = get_lang(user_id)
    t = LANG[lang_code]
    if "Countries" in product_inventory and item_key in product_inventory["Countries"]["items"]:
        c_data = product_inventory["Countries"]["items"][item_key]
        price_per_unit = c_data.get("price", 1.00)
        zip_list = c_data.get("zip_files", [])
        accounts_list = c_data.get("accounts", [])
    else:
        bot.send_message(chat_id, t["product_not_found"])
        return

    zip_total_files = sum(len(zf.get("extracted_files", [])) for zf in zip_list)
    total_stock = len(accounts_list) + zip_total_files
    if total_stock < qty:
        bot.send_message(chat_id, t["insufficient_stock"].format(stock=total_stock), reply_markup=get_main_menu_inline_back(user_id))
        return

    total_price = round(price_per_unit * qty, 2)
    user_balance = user_balances.get(user_id, 0.00)
    if user_balance < total_price:
        bot.send_message(
            chat_id,
            t["insufficient_balance"].format(required=total_price, balance=user_balance),
            reply_markup=get_main_menu_inline_back(user_id)
        )
        return

    flag = get_country_flag(item_key, c_data.get("code", ""))
    display_country_name = format_country_display_name(item_key, c_data.get("names", {}).get(lang_code, item_key), lang_code)
    clean_en_name = format_country_display_name(item_key, item_key, "en")
    delivered_count = 0
    for _ in range(qty):
        try:
            while len(zip_list) > 0 and len(zip_list[0].get("extracted_files", [])) == 0:
                zip_list.pop(0)

            if len(zip_list) > 0:
                zip_item = zip_list[0]
                if "zip_b64" in zip_item:
                    orig_zip_bytes = base64.b64decode(zip_item["zip_b64"])
                else:
                    orig_zip_bytes = bytes(zip_item["zip_bytes"])
                tfa_code = zip_item["2fa"]
                files_in_zip = zip_item["extracted_files"]
                target_file_name = files_in_zip[0]

                single_zip_buffer = io.BytesIO()
                with pyzipper.AESZipFile(single_zip_buffer, 'w', compression=pyzipper.ZIP_DEFLATED, encryption=pyzipper.WZ_AES) as new_zip:
                    new_zip.setpassword(tfa_code.encode('utf-8'))
                    with pyzipper.AESZipFile(io.BytesIO(orig_zip_bytes), 'r') as orig_zip:
                        orig_zip.setpassword(tfa_code.encode('utf-8'))
                        file_data = orig_zip.read(target_file_name)
                        new_zip.writestr(os.path.basename(target_file_name), file_data)
                single_zip_buffer.seek(0)

                files_in_zip.pop(0)
                if len(files_in_zip) == 0:
                    zip_list.pop(0)

                user_balances[user_id] = round(user_balances.get(user_id, 0.0) - price_per_unit, 2)
                purchase_text = f"Bought {clean_en_name} (ZIP file) for ${price_per_unit:.2f}"
                user_purchases.setdefault(user_id, []).append({"text": purchase_text, "timestamp": time.time()})
                delivered_count += 1

                file_short_name = os.path.basename(target_file_name)
                caption_txt = t["deliver_zip_caption"].format(
                    flag=flag,
                    name=display_country_name,
                    file=file_short_name,
                    tfa=tfa_code,
                    price=price_per_unit,
                    balance=user_balances[user_id]
                )
                bot.send_document(
                    chat_id,
                    document=single_zip_buffer,
                    visible_file_name=f"{display_country_name}_{file_short_name}.zip",
                    caption=caption_txt
                )
            elif len(accounts_list) > 0:
                purchased_item = accounts_list.pop(0)
                acc_num = purchased_item.get("number", "N/A")
                acc_2fa = purchased_item.get("2fa", "N/A")

                user_balances[user_id] = round(user_balances.get(user_id, 0.0) - price_per_unit, 2)
                purchase_text = f"Bought {clean_en_name}: {acc_num} for ${price_per_unit:.2f}"
                user_purchases.setdefault(user_id, []).append({"text": purchase_text, "timestamp": time.time()})
                delivered_count += 1

                success_text = t["deliver_acc_text"].format(
                    flag=flag,
                    name=display_country_name,
                    num=acc_num,
                    tfa=acc_2fa,
                    price=price_per_unit,
                    balance=user_balances[user_id]
                )
                bot.send_message(chat_id, success_text)
        except Exception as e:
            print(f"Error in delivering product: {e}")
            bot.send_message(chat_id, t["deliver_err"].format(err=str(e)))
            break

    if delivered_count > 0:
        save_user_data(user_id)
        save_inventory()

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_clicks(call):
    user_id = call.from_user.id
    ensure_user_registered(user_id)

    lang_code = get_lang(user_id)
    t = LANG[lang_code]

    # Colored Main Menu Callbacks
    if call.data == "menu_products":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(t["products"], call.message.chat.id, call.message.message_id, reply_markup=get_products_countries_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, t["products"], reply_markup=get_products_countries_keyboard(user_id))
        return

    if call.data == "menu_deposit":
        user_states[user_id] = "waiting_for_deposit"
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(t["deposit"], call.message.chat.id, call.message.message_id, reply_markup=get_select_amount_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, t["deposit"], reply_markup=get_select_amount_keyboard(user_id))
        return

    if call.data == "menu_support":
        bot.answer_callback_query(call.id)
        support_msg = t["support"].format(support_user=support_admin_username)
        try:
            bot.edit_message_text(support_msg, call.message.chat.id, call.message.message_id, reply_markup=get_account_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, support_msg, reply_markup=get_account_keyboard(user_id))
        return

    if call.data == "menu_account":
        bot.answer_callback_query(call.id)
        user = call.from_user
        no_user_str = "无" if lang_code == "zh" else "N/A"
        username = f"@{user.username}" if user.username else no_user_str
        balance_val = user_balances.get(user_id, 0.00)
        purchased_total = len(user_purchases.get(user_id, []))
        account_text = t["account"].format(user_id=user.id, username=username, balance=balance_val, purchased_total=purchased_total)
        try:
            bot.edit_message_text(account_text, call.message.chat.id, call.message.message_id, reply_markup=get_account_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, account_text, reply_markup=get_account_keyboard(user_id))
        return

    if call.data == "menu_lang":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(t["language"], call.message.chat.id, call.message.message_id, reply_markup=get_language_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, t["language"], reply_markup=get_language_keyboard(user_id))
        return

    if call.data == "menu_rules":
        bot.answer_callback_query(call.id)
        rules_msg = t["rules"].format(support_user=support_admin_username)
        try:
            bot.edit_message_text(rules_msg, call.message.chat.id, call.message.message_id, reply_markup=get_account_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, rules_msg, reply_markup=get_account_keyboard(user_id))
        return

    if call.data == "menu_admin":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "Unauthorized", show_alert=True)
            return
        bot.answer_callback_query(call.id)
        user_states[user_id] = "waiting_for_admin_password"
        bot.send_message(call.message.chat.id, "🔐 Please enter the Admin Panel password:")
        return

    if call.data == "admin_change_support":
        if not is_admin(user_id):
            return
        user_states[user_id] = "waiting_for_new_support_username"
        bot.answer_callback_query(call.id, "Change Support Username")
        try:
            bot.edit_message_text(
                "📞 Change Support Username\n\nPlease send new support username (e.g., @YourUsername):",
                call.message.chat.id,
                call.message.message_id
            )
        except Exception:
            pass
        return

    if call.data.startswith("dep_accept_") or call.data.startswith("dep_reject_"):
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "Unauthorized", show_alert=True)
            return

        action = "accept" if "accept" in call.data else "reject"
        dep_id = call.data.replace("dep_accept_", "").replace("dep_reject_", "")

        if dep_id in pending_deposits:
            dep_info = pending_deposits.pop(dep_id)
            remove_pending_deposit(dep_id)
            target_uid = int(dep_info["user_id"])
            amount = float(dep_info["amount"])
            order_id = dep_info["order_id"]
            target_t = LANG[get_lang(target_uid)]

            if action == "accept":
                old_bal = user_balances.get(target_uid, 0.0)
                new_bal = round(old_bal + amount, 2)
                user_balances[target_uid] = new_bal

                user_deposits.setdefault(target_uid, []).append({
                    "text": f"Deposited ${amount:.2f} (Order: {order_id})",
                    "timestamp": time.time()
                })
                save_user_data(target_uid)

                bot.answer_callback_query(call.id, "Deposit Accepted & Credited!", show_alert=True)
                try:
                    bot.edit_message_text(f"✅ Deposit Accepted!\nOrder ID: {order_id}\nCredited Amount: ${amount:.2f} to User {target_uid}", call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                try:
                    bot.send_message(target_uid, target_t["dep_accepted_user"].format(amount=amount))
                except Exception:
                    pass
            else:
                txid_val = dep_info.get("txid", "")
                if txid_val and txid_val.lower() in used_txids:
                    used_txids.remove(txid_val.lower())
                    save_used_txids()

                bot.answer_callback_query(call.id, "Deposit Rejected!", show_alert=True)
                try:
                    bot.edit_message_text(f"❌ Deposit Rejected!\nOrder ID: {order_id} for User {target_uid}", call.message.chat.id, call.message.message_id)
                except Exception:
                    pass
                try:
                    bot.send_message(target_uid, target_t["dep_rejected_user"].format(order_id=order_id))
                except Exception:
                    pass
        else:
            bot.answer_callback_query(call.id, "Request already processed or expired!", show_alert=True)
        return

    if call.data.startswith("send_order_id_"):
        order_id = call.data.replace("send_order_id_", "")
        user_states[user_id] = f"waiting_for_txid_{order_id}"
        bot.answer_callback_query(call.id)

        prompt_text = t["txid_prompt"].format(order_id=order_id)
        try:
            bot.edit_message_text(prompt_text, call.message.chat.id, call.message.message_id)
        except Exception:
            bot.send_message(call.message.chat.id, prompt_text)
        return

    if call.data == "admin_management":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "Unauthorized", show_alert=True)
            return
        bot.answer_callback_query(call.id, "Management")
        total_users = len(all_users)
        text = (
            f"👥 Management\n"
            f"──────────────────────\n"
            f"👥 Total Users: {total_users}\n"
            f"──────────────────────\n"
            f"Select option below:"
        )
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_management_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, text, reply_markup=get_management_keyboard(user_id))
        return

    if call.data.startswith("mgmt_users_"):
        if not is_admin(user_id):
            return
        try:
            page = int(call.data.replace("mgmt_users_", ""))
        except Exception:
            page = 0
        bot.answer_callback_query(call.id, f"Page {page+1}")
        markup, total_pages, total = get_users_list_keyboard(page)
        text = f"👥 All Users List\n──────────────────────\nTotal Users: {total}\nClick a user to edit balance:"
        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    if call.data == "mgmt_search_user":
        if not is_admin(user_id):
            return
        user_states[user_id] = "waiting_for_mgmt_search"
        bot.answer_callback_query(call.id, "Search User")
        try:
            bot.edit_message_text("🔍 Search User\n\nPlease send User ID (e.g., 123456789):", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    if call.data == "mgmt_top_balance":
        if not is_admin(user_id):
            return
        bot.answer_callback_query(call.id, "Top Balance")
        top = sorted(all_users, key=lambda u: user_balances.get(int(u), 0.0), reverse=True)[:10]
        markup = types.InlineKeyboardMarkup(row_width=1)
        for uid in top:
            bal = user_balances.get(int(uid), 0.0)
            markup.add(types.InlineKeyboardButton(f"👤 {uid} | 💰 ${bal:.2f}", callback_data=f"mgmt_user_{uid}"))
        markup.add(types.InlineKeyboardButton("🔙 Back to Management", callback_data="admin_management"))
        try:
            bot.edit_message_text("💰 Top 10 Balance Users:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    if call.data.startswith("mgmt_user_"):
        if not is_admin(user_id):
            return
        target_uid = int(call.data.replace("mgmt_user_", ""))
        bot.answer_callback_query(call.id, f"User {target_uid}")
        try:
            bot.edit_message_text(get_user_detail_text(target_uid), call.message.chat.id, call.message.message_id, reply_markup=get_user_detail_keyboard(target_uid))
        except Exception:
            bot.send_message(call.message.chat.id, get_user_detail_text(target_uid), reply_markup=get_user_detail_keyboard(target_uid))
        return

    if call.data.startswith("mgmt_bal_add_") or call.data.startswith("mgmt_bal_sub_") or call.data.startswith("mgmt_bal_set_"):
        if not is_admin(user_id):
            return
        rest = call.data.replace("mgmt_bal_", "")
        action, target_uid = rest.split("_")
        user_states[user_id] = f"waiting_for_mgmt_bal_{action}_{target_uid}"
        old_bal = user_balances.get(int(target_uid), 0.0)
        label = {"add": "➕ Add Balance", "sub": "➖ Subtract Balance", "set": "✏️ Set Balance"}[action]
        bot.answer_callback_query(call.id, label)
        try:
            bot.edit_message_text(
                f"{label}\n\n👤 User ID: {target_uid}\n💰 Current Balance: ${old_bal:.2f}\n\nPlease send amount (e.g., 10):",
                call.message.chat.id, call.message.message_id
            )
        except Exception:
            pass
        return

    if call.data.startswith("mgmt_bal_reset_"):
        if not is_admin(user_id):
            return
        target_uid = int(call.data.replace("mgmt_bal_reset_", ""))
        old_bal = user_balances.get(target_uid, 0.0)
        user_balances[target_uid] = 0.0
        save_user_data(target_uid)
        bot.answer_callback_query(call.id, "Balance Reset to $0", show_alert=True)
        try:
            bot.edit_message_text(
                f"✅ Balance Reset!\n\n👤 User ID: {target_uid}\n💰 Old: ${old_bal:.2f} → New: $0.00",
                call.message.chat.id, call.message.message_id, reply_markup=get_user_detail_keyboard(target_uid)
            )
        except Exception:
            pass
        try:
            target_lang = get_lang(target_uid)
            reset_txt = "💰 管理员已将您的余额重置为 $0.00。" if target_lang == "zh" else "💰 Your balance has been reset to $0.00 by Admin."
            bot.send_message(target_uid, reset_txt)
        except Exception:
            pass
        return

    if call.data.startswith("mgmt_hist_pur_"):
        if not is_admin(user_id):
            return
        target_uid = int(call.data.replace("mgmt_hist_pur_", ""))
        pur = user_purchases.get(target_uid, [])
        txt = "\n".join([p.get("text", "") if isinstance(p, dict) else str(p) for p in pur[-20:]]) or "No purchases yet."
        bot.answer_callback_query(call.id, "Purchase History")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"mgmt_user_{target_uid}"))
        try:
            bot.edit_message_text(f"📦 Purchase History - {target_uid}\n──────────────────────\n{txt}", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    if call.data.startswith("mgmt_hist_dep_"):
        if not is_admin(user_id):
            return
        target_uid = int(call.data.replace("mgmt_hist_dep_", ""))
        dep = user_deposits.get(target_uid, [])
        txt = "\n".join([d.get("text", "") if isinstance(d, dict) else str(d) for d in dep[-20:]]) or "No deposits yet."
        bot.answer_callback_query(call.id, "Deposit History")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data=f"mgmt_user_{target_uid}"))
        try:
            bot.edit_message_text(f"💰 Deposit History - {target_uid}\n──────────────────────\n{txt}", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    if call.data == "lang_toggle":
        current_lang = user_languages.get(user_id, "en")
        if current_lang == "en":
            user_languages[user_id] = "zh"
            alert_text = "语言已成功切换为中文！"
        else:
            user_languages[user_id] = "en"
            alert_text = "Language successfully changed to English!"

        save_user_data(user_id)
        bot.answer_callback_query(call.id, alert_text)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message)
        return

    if call.data == "back_to_account":
        bot.answer_callback_query(call.id)
        user = call.from_user
        no_user_str = "无" if lang_code == "zh" else "N/A"
        username = f"@{user.username}" if user.username else no_user_str
        balance_val = user_balances.get(user_id, 0.00)
        purchased_total = len(user_purchases.get(user_id, []))
        account_text = t["account"].format(user_id=user.id, username=username, balance=balance_val, purchased_total=purchased_total)
        try:
            bot.edit_message_text(account_text, call.message.chat.id, call.message.message_id, reply_markup=get_account_keyboard(user_id))
        except Exception:
            pass
        return

    if call.data.startswith("qty_other_"):
        item_key = call.data.replace("qty_other_", "")
        user_states[user_id] = f"waiting_for_custom_qty_{item_key}"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, t["enter_custom_qty"])
        return

    if call.data.startswith("qty_"):
        remainder = call.data.replace("qty_", "")
        last_underscore = remainder.rfind("_")
        item_key = remainder[:last_underscore]
        qty = int(remainder[last_underscore + 1:])
        bot.answer_callback_query(call.id)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        process_product_purchase(call.message.chat.id, user_id, item_key, qty)
        return

    elif call.data.startswith("select_country_"):
        country = call.data.replace("select_country_", "")
        c_data = product_inventory["Countries"]["items"].get(country, {})
        price = c_data.get("price", 1.00)
        c_code = c_data.get("code", "")
        flag = get_country_flag(country, c_code)
        clean_name = format_country_display_name(country, c_data.get("names", {}).get(lang_code, country), lang_code)
        bot.answer_callback_query(call.id, clean_name)
        zip_stock_count = sum(len(zf.get("extracted_files", [])) for zf in c_data.get("zip_files", []))
        stock_count = len(c_data.get("accounts", [])) + zip_stock_count
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(t["select_qty_btn"], callback_data=f"buy_country_{country}"),
            types.InlineKeyboardButton(t["back"], callback_data="back_to_products_menu")
        )
        try:
            country_detail_text = t["country_detail"].format(
                flag=flag,
                name=clean_name,
                code=c_code,
                price=price,
                stock=stock_count
            )
            bot.edit_message_text(country_detail_text, call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    elif call.data.startswith("buy_country_"):
        country = call.data.replace("buy_country_", "")
        c_data = product_inventory["Countries"]["items"].get(country, {})
        flag = get_country_flag(country, c_data.get("code", ""))
        clean_name = format_country_display_name(country, c_data.get("names", {}).get(lang_code, country), lang_code)
        bot.answer_callback_query(call.id, clean_name)
        try:
            proto_qty_text = t["qty_header"].format(flag=flag, name=clean_name)
            bot.edit_message_text(proto_qty_text, call.message.chat.id, call.message.message_id, reply_markup=get_quantity_keyboard(country, user_id))
        except Exception:
            pass
        return

    elif call.data == "admin_broadcast_start":
        if not is_admin(user_id):
            return
        user_states[user_id] = "waiting_for_broadcast_message"
        bot.answer_callback_query(call.id, "Broadcast Mode")
        try:
            bot.edit_message_text("📢 Broadcast System\n\nPlease send the message, photo, video or file that you want to send to all users:", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    elif call.data == "admin_add_country":
        if not is_admin(user_id):
            return
        user_states[user_id] = "waiting_for_new_country"
        bot.answer_callback_query(call.id, "Add Country")
        try:
            bot.edit_message_text("🌍 Enter new country name (e.g., Canada):", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    elif call.data == "admin_edit_delete_countries_menu":
        if not is_admin(user_id):
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        proto_items = product_inventory.get("Countries", {}).get("items", {})
        if proto_items:
            for c_name, c_val in proto_items.items():
                flag = get_country_flag(c_name, c_val.get("code", ""))
                clean_c = format_country_display_name(c_name, c_name, "en")
                markup.add(
                    types.InlineKeyboardButton(f"💵 Edit Price: {flag} {clean_c}", callback_data=f"admin_edit_price_{c_name}"),
                    types.InlineKeyboardButton(f"✏️ Rename: {flag} {clean_c}", callback_data=f"admin_rename_country_{c_name}"),
                    types.InlineKeyboardButton(f"❌ Delete: {flag} {clean_c}", callback_data=f"admin_delete_country_{c_name}")
                )
        markup.add(types.InlineKeyboardButton(t["back"], callback_data="admin_back"))
        bot.answer_callback_query(call.id, "Countries Edit Menu")
        try:
            bot.edit_message_text("🌐 Manage Countries:\nSelect an option for a country below:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    elif call.data.startswith("admin_edit_price_"):
        if not is_admin(user_id):
            return
        country_name = call.data.replace("admin_edit_price_", "")
        user_states[user_id] = f"waiting_for_edit_price_{country_name}"
        current_price = product_inventory["Countries"]["items"].get(country_name, {}).get("price", 1.00)
        bot.answer_callback_query(call.id, f"Edit Price {country_name}")
        try:
            bot.edit_message_text(f"💵 Edit Price for {country_name}\n\nCurrent Price: ${current_price:.2f}\n\nPlease send new price (e.g., 1.50 or 2):", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    elif call.data.startswith("admin_rename_country_"):
        if not is_admin(user_id):
            return
        country_name = call.data.replace("admin_rename_country_", "")
        user_states[user_id] = f"waiting_for_rename_country_{country_name}"
        bot.answer_callback_query(call.id, f"Rename {country_name}")
        try:
            bot.edit_message_text(f"✏️ Enter new name for country {country_name}:", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    elif call.data.startswith("admin_delete_country_"):
        if not is_admin(user_id):
            return
        country_name = call.data.replace("admin_delete_country_", "")
        proto_items = product_inventory.get("Countries", {}).get("items", {})
        if country_name in proto_items:
            del proto_items[country_name]
            save_inventory()
            bot.answer_callback_query(call.id, f"Deleted {country_name}")
            markup = types.InlineKeyboardMarkup(row_width=1)
            for c, c_val in proto_items.items():
                flag = get_country_flag(c, c_val.get("code", ""))
                clean_c = format_country_display_name(c, c, "en")
                markup.add(
                    types.InlineKeyboardButton(f"💵 Edit Price: {flag} {clean_c}", callback_data=f"admin_edit_price_{c}"),
                    types.InlineKeyboardButton(f"✏️ Rename: {flag} {clean_c}", callback_data=f"admin_rename_country_{c}"),
                    types.InlineKeyboardButton(f"❌ Delete: {flag} {clean_c}", callback_data=f"admin_delete_country_{c}")
                )
            markup.add(types.InlineKeyboardButton(t["back"], callback_data="admin_back"))
            try:
                bot.edit_message_text(f"✅ Country {country_name} deleted successfully!\n\n🌐 Manage Countries:", call.message.chat.id, call.message.message_id, reply_markup=markup)
            except Exception:
                pass
        else:
            bot.answer_callback_query(call.id, "Country not found", show_alert=True)
        return

    elif call.data == "admin_add_zip_menu":
        if not is_admin(user_id):
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for c, c_val in product_inventory["Countries"]["items"].items():
            flag = get_country_flag(c, c_val.get("code", ""))
            clean_c = format_country_display_name(c, c, "en")
            markup.add(types.InlineKeyboardButton(f"🗂️ {flag} {clean_c}", callback_data=f"select_zip_country_{c}"))
        markup.add(types.InlineKeyboardButton(t["back"], callback_data="admin_back"))
        bot.answer_callback_query(call.id, "ZIP Menu")
        try:
            bot.edit_message_text("Select country to upload ZIP file stock:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        except Exception:
            pass
        return

    elif call.data.startswith("select_zip_country_"):
        if not is_admin(user_id):
            return
        country_name = call.data.replace("select_zip_country_", "")
        temp_admin_data[user_id] = country_name
        user_states[user_id] = "waiting_for_zip_file"
        bot.answer_callback_query(call.id, country_name)
        try:
            bot.edit_message_text(f"📁 Please send the .zip file for {country_name}:", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    elif call.data == "admin_back":
        if not is_admin(user_id):
            return
        try:
            bot.edit_message_text("🛠️ Welcome to Admin Panel\n\nChoose an option below:", call.message.chat.id, call.message.message_id, reply_markup=get_admin_panel_keyboard(user_id))
        except Exception:
            pass
        return

    elif call.data == "noop":
        bot.answer_callback_query(call.id)
        return

    if call.data in ["btn_deposit_open", "dep_confirm", "▲ Deposit"]:
        try:
            bot.answer_callback_query(call.id)
            bot.edit_message_text(t["deposit"], call.message.chat.id, call.message.message_id, reply_markup=get_select_amount_keyboard(user_id))
        except Exception:
            bot.send_message(call.message.chat.id, t["deposit"], reply_markup=get_select_amount_keyboard(user_id))
        return

    elif call.data.startswith("amt_"):
        if call.data == "amt_other":
            user_states[user_id] = "waiting_for_custom_amount"
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, t["deposit_select_amt"])
        else:
            try:
                selected_val = float(call.data.split("_")[1])
                user_amounts[user_id] = selected_val
                user_states[user_id] = "waiting_for_payment_method"
                payment_text = t["selected_amount_pay"].format(amount=selected_val)
                bot.answer_callback_query(call.id)
                bot.edit_message_text(payment_text, call.message.chat.id, call.message.message_id, reply_markup=get_payment_methods_keyboard(user_id))
            except Exception:
                pass
        return

    elif call.data in ["order_usdt_trc20", "order_usdt_bep20"]:
        current_amount = user_amounts.get(user_id, 5.00)
        if current_amount < 5.0:
            bot.answer_callback_query(call.id, t["min_network"], show_alert=True)
            return
        order_id = f"ORD-{random.randint(100000, 999999)}"
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if call.data == "order_usdt_trc20":
            calculated_val = current_amount * (10.016 / 10.0)
            send_val = f"{calculated_val:.3f} USDT"
            credit_val = f"${current_amount:.2f}"
            currency_type = "USDT · TRC20"
            wallet_address = "TLciFN9Z7DGSsK6eHNP1WGHQxLWN29o2n7"
            network_name = "Tron (TRC20)"
            net_code = "tron"
        else:
            calculated_val = current_amount * (10.076 / 10.0)
            send_val = f"{calculated_val:.3f} USDT"
            credit_val = f"${current_amount:.2f}"
            currency_type = "USDT · BEP20"
            wallet_address = "0x8fd14bf35fc69d0354b5202c936e4ddce33733f9"
            network_name = "BNB Smart Chain (BEP20)"
            net_code = "bsc"

        temp_admin_data[f"order_temp_{user_id}"] = {"order_id": order_id, "method": currency_type}
        deposit_text = f"Order: {order_id} | Amt: ${current_amount:.2f} ({currency_type}) | Time: {current_time}"
        user_deposits.setdefault(user_id, []).append({"text": deposit_text, "timestamp": time.time()})
        save_user_data(user_id)

        order_text = t["order_box"].format(
            currency=currency_type,
            send_num=f"{calculated_val:.3f}",
            credit=credit_val,
            order_id=order_id,
            network=network_name,
            address=wallet_address,
            expires=current_time,
            send_val=send_val,
            amount=current_amount
        )
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(order_text, call.message.chat.id, call.message.message_id, parse_mode="HTML", reply_markup=get_order_created_keyboard(net_code, order_id, user_id))
        except Exception:
            bot.send_message(call.message.chat.id, order_text, parse_mode="HTML", reply_markup=get_order_created_keyboard(net_code, order_id, user_id))
        return

    elif call.data == "back_to_products_menu":
        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(t["products"], call.message.chat.id, call.message.message_id, reply_markup=get_products_countries_keyboard(user_id))
        except Exception:
            pass
        return

    elif call.data in ["go_main_menu", "dep_cancel"]:
        bot.answer_callback_query(call.id)
        user_states.pop(user_id, None)
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        send_welcome(call.message)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"Webhook Bot is running on port {port}...")
    app.run(host='0.0.0.0', port=port)
