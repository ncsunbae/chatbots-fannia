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

INTENT_MAP = {
    item["intent"]: item
    for item in KNOWLEDGE_BASE
}

def normalisasi_pesan(pesan):
    pesan = pesan.lower().strip()
    pesan = re.sub(r"[^\w\s]", "", pesan)
    pesan = re.sub(r"\s+", " ", pesan)
    return pesan

def buat_response(
    text,
    wa_text="",
    status="paham",
    next_state="none",
    pernah_lihat_menu=False,
    actions=None,
):
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
    return buat_response(
        text=(
            "Halo! Terima kasih sudah menghubungi "
            "Fannia Entertainment. ✨\n\n"
            "Silakan pilih menu berikut:"
        ),
        wa_text=(
            "Halo Admin Fannia Entertainment, "
            "saya mau konsultasi mengenai acara saya."
        ),
        status="bingung",
        next_state="menu_utama",
        pernah_lihat_menu=True,
        actions=[
            {"label": "🏢 Profil", "value": "1"},
            {"label": "💼 Layanan", "value": "2"},
            {"label": "💰 Paket", "value": "3"},
            {"label": "⭐ Testimoni", "value": "4"},
            {"label": "📍 Kontak", "value": "5"},
        ],
    )

PAKET_WEDDING = {
    "silver": {
        "text": (
            "🔹 *Paket Wedding Silver (Rp 25 Juta)* 🔹\n\n"
            "Cocok untuk 300 undangan.\n\n"
            "Include:\n"
            "- Dekorasi Pelaminan Standard\n"
            "- Catering Prasmanan\n"
            "- Rias & Busana Pengantin\n"
            "- Team WO Hari H (4 Orang)\n"
            "- Sound System & MC\n\n"
            "---\n"
            "*0. 🔙 Kembali ke Menu Utama*"
        ),
        "wa_text": (
            "Halo Admin Fannia Entertainment, "
            "saya tertarik dengan Paket Wedding Silver Rp 25 Juta."
        ),
    },
    "gold": {
        "text": (
            "👑 *Paket Wedding Gold (Rp 45 Juta)* 👑\n\n"
            "Cocok untuk 600 undangan.\n\n"
            "Include:\n"
            "- Dekorasi Premium + Mini Garden\n"
            "- Catering Premium\n"
            "- Rias & Busana Lengkap\n"
            "- Full Team WO & Planner\n"
            "- Live Music\n"
            "- Sound System & MC\n\n"
            "---\n"
            "*0. 🔙 Kembali ke Menu Utama*"
        ),
        "wa_text": (
            "Halo Admin Fannia Entertainment, "
            "saya tertarik dengan Paket Wedding Gold Rp 45 Juta."
        ),
    },
}

def cari_intent_terbaik(pesan_user, pernah_lihat_menu, last_state):
    pesan_user_normal = normalisasi_pesan(pesan_user)

    fallback = INTENT_MAP.get(
        "fallback",
        {"reply": "Maaf kak, saya belum memahami pertanyaan tersebut 🙏"}
    )

    if pesan_user_normal in ["0", "menu", "menu utama", "kembali", "back"]:
        return dapatkan_menu_utama_reply()

    if last_state == "menu_paket":
        if pesan_user_normal in ["1", "silver"] or "silver" in pesan_user_normal:
            paket = PAKET_WEDDING["silver"]
            return buat_response(
                text=paket["text"],
                wa_text=paket["wa_text"],
                next_state="none",
                pernah_lihat_menu=pernah_lihat_menu,
            )
        elif pesan_user_normal in ["2", "gold"] or "gold" in pesan_user_normal:
            paket = PAKET_WEDDING["gold"]
            return buat_response(
                text=paket["text"],
                wa_text=paket["wa_text"],
                next_state="none",
                pernah_lihat_menu=pernah_lihat_menu,
            )

    if last_state == "booking":
        if "wedding" in pesan_user_normal or pesan_user_normal == "1":
            return buat_response(
                text=(
                    "💍 Kakak memilih Wedding.\n\n"
                    "Silakan hubungi admin kami untuk menentukan tanggal "
                    "dan paket yang sesuai ya 😊"
                ),
                wa_text="Halo Admin Fannia Entertainment, saya ingin booking Wedding.",
                next_state="none",
                pernah_lihat_menu=True,
            )
        elif "birthday" in pesan_user_normal or "ulang tahun" in pesan_user_normal or pesan_user_normal == "2":
            return buat_response(
                text=(
                    "🎂 Kakak memilih Birthday Party.\n\n"
                    "Tim kami siap membantu membuat acara ulang tahun yang berkesan ✨"
                ),
                wa_text="Halo Admin Fannia Entertainment, saya ingin booking Birthday Party.",
                next_state="none",
                pernah_lihat_menu=True,
            )
        elif "gathering" in pesan_user_normal or pesan_user_normal == "3":
            return buat_response(
                text=(
                    "🎉 Kakak memilih Gathering.\n\n"
                    "Silakan konsultasi dengan admin kami untuk kebutuhan gathering ya 😊"
                ),
                wa_text="Halo Admin Fannia Entertainment, saya ingin booking Gathering.",
                next_state="none",
                pernah_lihat_menu=True,
            )

    if pesan_user_normal in ["1", "2", "3", "4", "5"]:
        for data in KNOWLEDGE_BASE:
            if data.get("menu_number") == pesan_user_normal:
                reply = data["reply"]
                if data["intent"] == "paket_dan_harga":
                    reply += "\n\nPilih:\n1. Silver\n2. Gold\n\n*0. 🔙 Kembali ke Menu Utama*"
                    current_next_state = "menu_paket"
                else:
                    reply += "\n\n---\n*0. 🔙 Kembali ke Menu Utama*"
                    current_next_state = "none"

                return buat_response(
                    text=reply,
                    wa_text=data.get("wa_text", ""),
                    next_state=current_next_state,
                    pernah_lihat_menu=True,
                )

    greeting = INTENT_MAP.get("greeting")
    if greeting:
        for keyword in greeting.get("priority_keywords", []):
            if normalisasi_pesan(keyword) in pesan_user_normal:
                if last_state != "none":
                    return buat_response(
                        text="Halo kak 😊\n\nAda yang ingin ditanyakan lagi terkait informasi sebelumnya?",
                        wa_text=greeting.get("wa_text", ""),
                        next_state=last_state,
                        pernah_lihat_menu=pernah_lihat_menu,
                    )
                return dapatkan_menu_utama_reply()

    for data in KNOWLEDGE_BASE:
        if data["intent"] in ["greeting", "fallback"]:
            continue

        for keyword in data.get("priority_keywords", []):
            if normalisasi_pesan(keyword) in pesan_user_normal:
                if data["intent"] == "booking":
                    return buat_response(
                        text="Tentu kak 😊\n\nAcara apa yang ingin dibooking?\n\n1. Wedding\n2. Birthday\n3. Gathering",
                        wa_text=data["wa_text"],
                        next_state="booking",
                        pernah_lihat_menu=True,
                    )

                reply = data["reply"]
                current_next_state = "none"
                if data["intent"] == "paket_dan_harga":
                    reply += "\n\nPilih:\n1. Silver\n2. Gold"
                    current_next_state = "menu_paket"

                if pernah_lihat_menu:
                    reply += "\n\n---\n*0. 🔙 Kembali ke Menu Utama*"

                return buat_response(
                    text=reply,
                    wa_text=data.get("wa_text", ""),
                    next_state=current_next_state,
                    pernah_lihat_menu=pernah_lihat_menu,
                )

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
        current_next_state = "none"
        
        if intent_terpilih["intent"] == "paket_dan_harga":
            reply += "\n\nPilih:\n1. Silver\n2. Gold"
            current_next_state = "menu_paket"

        if pernah_lihat_menu:
            reply += "\n\n---\n*0. 🔙 Kembali ke Menu Utama*"

        return buat_response(
            text=reply,
            wa_text=intent_terpilih.get("wa_text", ""),
            next_state=current_next_state,
            pernah_lihat_menu=pernah_lihat_menu,
        )
        
    return buat_response(
        text=fallback["reply"] + ("\n\n---\n*0. 🔙 Kembali ke Menu Utama*" if pernah_lihat_menu else ""),
        wa_text=fallback.get("wa_text", "Halo Admin Fannia Entertainment, saya ingin konsultasi langsung."),
        status="bingung",
        next_state=last_state,
        pernah_lihat_menu=True,
    )

@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    data = request.json or {}
    pesan_user = data.get("message", "")
    pernah_lihat_menu = data.get("pernah_lihat_menu", False)
    last_state = data.get("last_state", "none")

    if not pesan_user.strip():
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400

    respon_bot = cari_intent_terbaik(
        pesan_user,
        pernah_lihat_menu,
        last_state,
    )

    return jsonify(respon_bot)

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )
