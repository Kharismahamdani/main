#!/bin/bash

# Konfigurasi
SCRIPT_NAME="ok.py"
REPO_URL="https://github.com/Kharismahamdani/main.git"
VERSION_FILE=".version"

# Fungsi untuk update script
update_script() {
    echo "Memulai proses update ok.py..."
    
    # Backup script lama jika ada
    if [ -f "$SCRIPT_NAME" ]; then
        cp "$SCRIPT_NAME" "${SCRIPT_NAME}.backup"
        echo "Backup script lama tersimpan sebagai ${SCRIPT_NAME}.backup"
    fi
    
    # Pull perubahan terbaru
    git pull origin main
    
    # Cek apakah file ok.py ada
    if [ -f "$SCRIPT_NAME" ]; then
        # Berikan permission eksekusi
        chmod +x "$SCRIPT_NAME"
        echo "Update ok.py berhasil!"
        echo "Versi baru telah diinstall."
    else
        echo "Error: $SCRIPT_NAME tidak ditemukan di repository!"
        # Kembalikan backup jika update gagal
        if [ -f "${SCRIPT_NAME}.backup" ]; then
            cp "${SCRIPT_NAME}.backup" "$SCRIPT_NAME"
            echo "Mengembalikan ke versi backup"
        fi
    fi
}

# Fungsi untuk setup awal
initial_setup() {
    echo "Melakukan setup awal..."
    
    # Cek apakah sudah ada repository git
    if [ ! -d ".git" ]; then
        echo "Clone repository dari GitHub..."
        git clone "$REPO_URL" .
        
        if [ $? -ne 0 ]; then
            echo "Error: Gagal clone repository!"
            exit 1
        fi
    fi
    
    # Cek apakah file ok.py ada
    if [ ! -f "$SCRIPT_NAME" ]; then
        echo "Error: $SCRIPT_NAME tidak ditemukan setelah clone!"
        exit 1
    fi
    
    chmod +x "$SCRIPT_NAME"
    echo "Setup awal selesai!"
}

# Main script
main() {
    # Periksa git terinstall
    if ! command -v git &> /dev/null; then
        echo "Error: Git tidak terinstall. Silakan install git terlebih dahulu."
        exit 1
    fi
    
    # Jalankan setup awal jika belum ada .git
    if [ ! -d ".git" ]; then
        initial_setup
    fi
    
    # Cek dan ambil perubahan dari remote
    echo "Memeriksa update dari GitHub..."
    git fetch origin
    
    # Bandingkan versi lokal dengan remote
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})
    
    if [ $LOCAL != $REMOTE ]; then
        echo "Update tersedia!"
        read -p "Apakah Anda ingin update ok.py sekarang? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            update_script
        fi
    else
        echo "ok.py sudah dalam versi terbaru"
    fi
    
    # Jalankan script python
    if [ -f "$SCRIPT_NAME" ]; then
        python "$SCRIPT_NAME"
    else
        echo "Error: $SCRIPT_NAME tidak ditemukan!"
        exit 1
    fi
}

# Jalankan script
main "$@"
