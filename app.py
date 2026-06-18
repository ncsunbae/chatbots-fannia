import json
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from rapidfuzz import process, fuzz

app = Flask(__name__)
CORS(app)

WHATSAPP_NUMBER = "6281316429729"

def load_knowledge_base():
    nama_file = "knowledge_base.json"
    if not os.path.exists(nama_file):
        print(f"ERROR: File '{nama_file}' tidak ditemukan!")
        return []
    try:
        with open(nama_file, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"ERROR saat membaca file JSON: {e}")
        return []

KNOWLEDGE_BASE = load_knowledge_base()
INTENT_MAP = {item["intent"]: item for item in KNOWLEDGE_BASE}

def normalisasi_pesan(pesan):
    pesan = pesan.lower().strip()
    pesan = re.sub(r"[^\w\s]", "", pesan)
    pesan = re.sub(r"\s+", " ", pesan)
    return pesan

def buat_response(text, wa_text="", status="paham", next_state="none", pernah_lihat_menu=False, actions=None):
    return {
        "text": text,
        "wa_text": wa_text,
        "wa_number": WHATSAPP_NUMBER,
        "status": status,
        "next_state": next_state,
        "pernah_lihat_menu": pernah_lihat_menu,
        "actions": actions or [],
    }

def dapatkan_menu_utama_reply():
    greeting_data = INTENT_MAP.get("greeting")
    reply_text = greeting_data["reply"] if greeting_data else "Halo! Silakan pilih menu berikut:"
    actions_data = greeting_data["actions"] if greeting_data else []
    
    return buat_response(
        text=reply_text,
        wa_text=greeting_data.get("wa_text", "") if greeting_data else "",
        status="bingung",
        next_state="pilih_menu",
        pernah_lihat_menu=True,
        actions=actions_data,
    )

PAKET_WEDDING = {
    "bronze": {
        "text": "Berikut detail isi Paket Bronze (Rp 27.500.000):\n\n- Tenda standard full karpet\n- Pelaminan standard bunga asli\n- Rias & busana pengantin premium\n- Kursi tamu 100 set & cover\n- Blower 1 unit\n- Sound system standard & MC\n- Dokumentasi foto standard\n- Janur 1 jalur",
        "wa_text": "Halo Admin Fannia Entertainment, saya tertarik dengan Paket Wedding Bronze Rp 27.500.000."
    },
    "silver": {
        "text": "Berikut detail isi Paket Silver (Rp 30.500.000):\n\n- Tenda 120 meter full karpet\n- Pelaminan luxury mini\n- Kursi futura 1 set\n- Make up & busana premium\n- Kursi tamu 120 set & cover\n- Blower 2 unit\n- Round table 6 pcs\n- MC & sound system\n- Photobooth mini\n- Dokumentasi standard\n- Janur 1 jalur",
        "wa_text": "Halo Admin Fannia Entertainment, saya tertarik dengan Paket Wedding Silver Rp 30.500.000."
    },
    "gold": {
        "text": "Berikut detail isi Paket Gold (Rp 35.500.000):\n\n- Tenda 150 meter full karpet\n- Pelaminan mewah & bunga segar\n- Kursi futura 1 set\n- Make up & busana premium\n- Kursi tamu 150 set & cover\n- Blower 3 unit\n- Round table 8 pcs\n- MC & entertainment\n- Photobooth area\n- Dokumentasi cinematic\n- Janur 2 jalur\n- Wedding organizer team",
        "wa_text": "Halo Admin Fannia Entertainment, saya tertarik dengan Paket Wedding Gold Rp 35.500.000."
    },
    "ruby": {
        "text": "Berikut detail isi Paket Ruby (Rp 50.500.000):\n\n- Dekorasi pelaminan glamor & eksklusif\n- Tenda dekorasi premium full karpet\n- Rias & busana pengantin eksklusif (akad & resepsi)\n- Kursi tamu 200 set & cover premium\n- Blower cooling fan 4 unit\n- Round table premium 10 pcs\n- MC, Acoustic/Live Band Entertainment\n- Exclusive photobooth spot\n- Dokumentasi full cinematic\n- Janur eksklusif 2 jalur\n- Full team Wedding Organizer & Planner",
        "wa_text": "Halo Admin Fannia Entertainment, saya tertarik dengan Paket Wedding Ruby Rp 50.500.000."
    },
    "emerald": {
        "text": "Berikut detail isi Paket Emerald (Rp 58.800.000):\n\n- Konsep dekorasi Luxury Modern\n- Tenda VIP / Rigging khusus full karpet tebal\n- Rias & busana pengantin premium custom desainer\n- Kursi tamu VIP & cover khusus\n- AC portable & Blower cooling system lengkap\n- Round table VIP dengan centerpiece premium\n- MC kondang & Full Entertainment\n- Interactive photobooth / 360 video booth\n- Dokumentasi premium\n- Gate jalan & janur lux 4 jalur\n- Professional Wedding Planner & Coordinator Full Team",
        "wa_text": "Halo Admin Fannia Entertainment, saya tertarik dengan Paket Wedding Emerald Rp 58.800.000."
    },
    "diamond": {
        "text": "Berikut detail isi Paket Diamond (Rp 70.500.000):\n\n- Konsep Masterpiece Luxury Ter-eksklusif\n- Tenda Dome VIP / Grand dekorasi termewah full karpet\n- Rias & busana pengantin kustom eksklusif plus keluarga inti\n- Kursi tamu premium VIP terlengkap\n- Full AC system area utama\n- Round table luxury dengan dekorasi meja VIP\n- MC premium, Full band entertainment, & guest star support\n- Premium unlimited photobooth service\n- Dokumentasi VIP lengkap\n- Gate utama megah & janur premium 4 jalur\n- Top-tier Wedding Planner, Organizer, & Runner Full Team",
        "wa_text": "Halo Admin Fannia Entertainment, saya tertarik dengan Paket Wedding Diamond Rp 70.500.000."
    }
}

def cari_intent_terbaik(pesan_user, pernah_lihat_menu, last_state):
    pesan_user_normal = normalisasi_pesan(pesan_user)
    fallback = INTENT_MAP.get("fallback", {"reply": "Maaf kak, saya belum memahami pertanyaan tersebut."})

    if pesan_user_normal in ["0", "menu", "menu utama", "kembali", "back", "halo"]:
        return dapatkan_menu_utama_reply()

    if last_state == "tanya_paket":
        if pesan_user_normal == "00":
            data_paket = INTENT_MAP.get("paket_dan_harga")
            if data_paket:
                reply = data_paket["reply"] + "\n\n*0. Kembali ke Menu Utama*"
                return buat_response(text=reply, next_state="tanya_paket", pernah_lihat_menu=True, actions=data_paket.get("actions", []))

        pilihan_paket = None
        mapping_paket = {
            "1": "bronze", "2": "silver", "3": "gold",
            "4": "ruby", "5": "emerald", "6": "diamond"
        }
        
        if pesan_user_normal in mapping_paket:
            pilihan_paket = mapping_paket[pesan_user_normal]
        else:
            for nama in PAKET_WEDDING.keys():
                if nama in pesan_user_normal:
                    pilihan_paket = nama
                    break

        if pilihan_paket:
            paket = PAKET_WEDDING[pilihan_paket]
            reply_text = paket["text"] + "\n\n---\n*00. Kembali ke Menu Paket*\n*0. Kembali ke Menu Utama*"
            return buat_response(
                text=reply_text,
                wa_text=paket["wa_text"],
                next_state="tanya_paket",
                pernah_lihat_menu=pernah_lihat_menu,
                actions=[
                    {"label": "Hubungi WA Admin", "value": "booking"},
                    {"label": "Kembali ke Paket", "value": "00"},
                    {"label": "Menu Utama", "value": "0"}
                ]
            )

    greeting = INTENT_MAP.get("greeting")
    if greeting:
        for keyword in greeting.get("priority_keywords", []):
            if normalisasi_pesan(keyword) in pesan_user_normal:
                if last_state != "none" and last_state != "pilih_menu":
                    return buat_response(text="Halo kak.\n\nAda yang ingin ditanyakan lagi terkait informasi sebelumnya?", wa_text=greeting.get("wa_text", ""), next_state=last_state, pernah_lihat_menu=pernah_lihat_menu, actions=greeting.get("actions", []))
                return dapatkan_menu_utama_reply()

    for data in KNOWLEDGE_BASE:
        if data["intent"] in ["greeting", "fallback"]:
            continue

        for keyword in data.get("priority_keywords", []):
            if normalisasi_pesan(keyword) in pesan_user_normal:
                reply = data["reply"]
                current_next_state = data.get("next_state", "none")
                
                if data["intent"] == "paket_dan_harga":
                    current_next_state = "tanya_paket"

                if pernah_lihat_menu:
                    reply += "\n\n---\n*0. Kembali ke Menu Utama*"

                return buat_response(text=reply, wa_text=data.get("wa_text", ""), next_state=current_next_state, pernah_lihat_menu=pernah_lihat_menu, actions=data.get("actions", []))

    intent_terpilih = None
    skor_tertinggi = 0
    daftar_kata_kunci = []
    for data in KNOWLEDGE_BASE:
        if data["intent"] == "fallback":
            continue
        for kw in data.get("keywords", []):
            daftar_kata_kunci.append((normalisasi_pesan(kw), data))

    if daftar_kata_kunci:
        kunci_hanya_teks = [item[0] for item in daftar_kata_kunci]
        hasil_fuzzy = process.extractOne(pesan_user_normal, kunci_hanya_teks, scorer=fuzz.WRatio)
        if hasil_fuzzy:
            teks_tercocok, skor, indeks = hasil_fuzzy
            if skor >= 80:
                skor_tertinggi = skor
                intent_terpilih = daftar_kata_kunci[indeks][1]

    if intent_terpilih and skor_tertinggi >= 80:
        reply = intent_terpilih["reply"]
        current_next_state = intent_terpilih.get("next_state", "none")
        
        if intent_terpilih["intent"] == "paket_dan_harga":
            current_next_state = "tanya_paket"
            
        if pernah_lihat_menu:
            reply += "\n\n---\n*0. Kembali ke Menu Utama*"

        return buat_response(text=reply, wa_text=intent_terpilih.get("wa_text", ""), next_state=current_next_state, pernah_lihat_menu=pernah_lihat_menu, actions=intent_terpilih.get("actions", []))
        
    return buat_response(text=fallback["reply"] + ("\n\n---\n*0. Kembali ke Menu Utama*" if pernah_lihat_menu else ""), wa_text=fallback.get("wa_text", "Halo Admin Fannia Entertainment, saya ingin konsultasi langsung."), status="bingung", next_state=last_state, pernah_lihat_menu=True, actions=fallback.get("actions", []))

@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.json or {}
    pesan_user = data.get("message", "")
    pernah_lihat_menu = data.get("pernah_lihat_menu", False)
    last_state = data.get("last_state", "none")

    if not pesan_user.strip():
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400

    respon_bot = cari_intent_terbaik(pesan_user, pernah_lihat_menu, last_state)
    return jsonify(respon_bot)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
