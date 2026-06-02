import json
import os
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from rapidfuzz import process, fuzz

app = Flask(__name__)
CORS(app)

def load_knowledge_base():
    nama_file = 'knowledge_base.json'
    if not os.path.exists(nama_file):
        print(f"ERROR: File '{nama_file}' tidak ditemukan!")
        return []
    try:
        with open(nama_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        print(f"ERROR saat membaca file JSON: {e}")
        return []

KNOWLEDGE_BASE = load_knowledge_base()

def dapatkan_menu_utama_reply():
    return {
        "text": "Halo! Terima kasih sudah menghubungi Fannia Entertainment. ✨\n\nUntuk mempermudah kakak mendapatkan informasi seputar layanan kami, silakan ketik salah satu *kata kunci* atau *angka menu* di bawah ini ya:\n\n1. 🏢 *Profil* (Tentang Fannia Entertainment)\n2. 💼 *Layanan* (Kebutuhan acara yang bisa kami bantu)\n3. 💰 *Paket* / *Harga* (Pricelist EO & WO terbaru)\n4. ⭐️ *Testimoni* (Review jujur dari para klien kami)\n5. 📍 *Kontak* (Alamat kantor & media sosial)\n\nAtau jika kakak ingin langsung berkonsultasi secara personal dengan tim kami, silakan klik tombol WhatsApp di bawah ini ya! 👇",
        "wa_text": "Halo Admin Fannia Entertainment, saya mau konsultasi mengenai rencana acara saya.",
        "status": "bingung",
        "next_state": "menu_utama",
        "pernah_lihat_menu": True
    }

def cari_intent_terbaik(pesan_user, pernah_lihat_menu, last_state):
    pesan_user = pesan_user.lower().strip()
    
    data_dict = {d['intent']: d for d in KNOWLEDGE_BASE}
    
    if pesan_user in ["0", "kembali", "menu utama", "menu", "back"]:
        return dapatkan_menu_utama_reply()

    if last_state == "menu_paket" and (pesan_user in ["1", "2"] or "silver" in pesan_user or "gold" in pesan_user):
        if "1" in pesan_user or "silver" in pesan_user:
            return {
                "text": "🔹 *Paket Wedding Silver (Rp 25 Juta)* 🔹\n\nCocok untuk 300 undangan. Sudah include:\n- Dekorasi Pelaminan Standard\n- Makanan Prasmanan Utama\n- Rias & Busana Pengantin\n- Team WO Hari H (4 Orang)\n- Sound System & MC.\n\n---\n*0. 🔙 Kembali ke Menu Utama*",
                "wa_text": "Halo Fannia Entertainment, saya tertarik Paket Wedding Silver Rp 25 Juta.",
                "status": "paham", 
                "next_state": "none", 
                "pernah_lihat_menu": pernah_lihat_menu
            }
        elif "2" in pesan_user or "gold" in pesan_user:
            return {
                "text": "👑 *Paket Wedding Gold (Rp 45 Juta)* 👑\n\nPaket Exclusive untuk 600 undangan. Sudah include:\n- Dekorasi Pelaminan Mewah + Mini Garden\n- Catering Premium (Menu Utama + 3 Pondokan)\n- Rias & Busana (Pengantin, Orang Tua, & Penerima Tamu)\n- Full Team WO & Planner dari A-Z\n- Live Acoustic Music, Sound, & MC Hits.\n\n---\n*0. 🔙 Kembali ke Menu Utama*",
                "wa_text": "Halo Fannia Entertainment, saya tertarik Paket Wedding Gold Rp 45 Juta.",
                "status": "paham", 
                "next_state": "none", 
                "pernah_lihat_menu": pernah_lihat_menu
            }

    if pesan_user in ["1", "2", "3", "4", "5"]:
        for data in KNOWLEDGE_BASE:
            if data.get('menu_number') == pesan_user:
                reply_text = data['reply']
                if data['intent'] == 'paket_dan_harga':
                    reply_text += "\n\n*0. 🔙 Kembali ke Menu Utama*"
                else:
                    reply_text += "\n\n---\n*0. 🔙 Kembali ke Menu Utama*"
                
                return {
                    "text": reply_text,
                    "wa_text": data['wa_text'],
                    "status": "paham",
                    "next_state": "menu_paket" if data['intent'] == 'paket_dan_harga' else "none",
                    "pernah_lihat_menu": True
                }

    for data in KNOWLEDGE_BASE:
        for p_kw in data.get('priority_keywords', []):
            if p_kw in pesan_user:
                if data['intent'] == 'greeting':
                    return dapatkan_menu_utama_reply()
                
                reply_text = data['reply']
                if pernah_lihat_menu:
                    if data['intent'] == 'paket_dan_harga':
                        reply_text += "\n\n*0. 🔙 Kembali ke Menu Utama*"
                    else:
                        reply_text += "\n\n---\n*0. 🔙 Kembali ke Menu Utama*"
                
                return {
                    "text": reply_text,
                    "wa_text": data['wa_text'],
                    "status": "paham",
                    "next_state": "menu_paket" if data['intent'] == 'paket_dan_harga' else "none",
                    "pernah_lihat_menu": pernah_lihat_menu
                }

    intent_terpilih = None
    skor_tertinggi = 0
    
    for data in KNOWLEDGE_BASE:
        hasil_fuzzy = process.extractOne(pesan_user, data['keywords'], scorer=fuzz.partial_ratio)
        if hasil_fuzzy and hasil_fuzzy[1] >= 80:
            skor_kemiripan = hasil_fuzzy[1]
            
            if data['intent'] in ['paket_dan_harga', 'profil_perusahaan', 'layanan_servis', 'kontak_lokasi', 'testimoni']:
                skor_kemiripan += 20
            
            if skor_kemiripan > skor_tertinggi:
                skor_tertinggi = skor_kemiripan
                intent_terpilih = data

    if intent_terpilih and skor_tertinggi >= 80:
        if intent_terpilih['intent'] == 'greeting':
            return dapatkan_menu_utama_reply()

        reply_text = intent_terpilih['reply']
        if pernah_lihat_menu:
            if intent_terpilih['intent'] == 'paket_dan_harga':
                reply_text += "\n\n*0. 🔙 Kembali ke Menu Utama*"
            else:
                reply_text += "\n\n---\n*0. 🔙 Kembali ke Menu Utama*"

        return {
            "text": reply_text,
            "wa_text": intent_terpilih['wa_text'],
            "status": "paham",
            "next_state": "menu_paket" if intent_terpilih['intent'] == 'paket_dan_harga' else "none",
            "pernah_lihat_menu": pernah_lihat_menu
        }

    return dapatkan_menu_utama_reply()


@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    data = request.json or {}
    pesan_user = data.get('message', '')
    
    pernah_lihat_menu = data.get('pernah_lihat_menu', False)
    last_state = data.get('last_state', 'none')
    
    if not pesan_user.strip():
        return jsonify({"error": "Pesan tidak boleh kosong"}), 400
        
    respon_bot = cari_intent_terbaik(pesan_user, pernah_lihat_menu, last_state)
    return jsonify(respon_bot)

app = app
if __name__ == '__main__':
    app.run(debug=True, port=5000)