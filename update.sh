#!/bin/bash

# Konfigurasi yang disesuaikan dengan repository Anda
MAIN_SCRIPT="ok.py"
BRANCH="main"
REPO_URL="https://github.com/Kharismahamdani/main.git"  # Sesuai dengan nama repository Anda

# Fungsi untuk update script
update_script() {
    echo "Memulai proses update $MAIN_SCRIPT..."
    
    # Backup script yang ada
    if [ -f "$MAIN_SCRIPT" ]; then
        cp "$MAIN_SCRIPT" "${MAIN_SCRIPT}.backup"
        echo "Backup script lama tersimpan sebagai ${MAIN_SCRIPT}.backup"
    fi
    
    # Pull perubahan terbaru
    git pull origin $BRANCH
    
    # Cek keberhasilan pull dan keberadaan file
    if [ $? -eq 0 ] && [ -f "$MAIN_SCRIPT" ]; then
        chmod +x "$MAIN_SCRIPT"
        echo "Update $MAIN_SCRIPT berhasil!"
        # Update file lain yang penting
        if [ -f "fixing.py" ]; then chmod +x fixing.py; fi
        if [ -f "best.py" ]; then chmod +x best.py; fi
    else
        echo "Error: Gagal mengupdate atau $MAIN_SCRIPT tidak ditemukan!"
        if [ -f "${MAIN_SCRIPT}.backup" ]; then
            cp "${MAIN_SCRIPT}.backup" "$MAIN_SCRIPT"
            echo "Mengembalikan ke versi backup"
        fi
    fi
}

# Fungsi untuk setup awal
initial_setup() {
    echo "Melakukan setup awal..."
    
    if [ ! -d ".git" ]; then
        echo "Clone repository dari GitHub..."
        git clone "$REPO_URL" .
        
        if [ $? -ne 0 ]; then
            echo "Error: Gagal clone repository!"
            exit 1
        fi
    fi
    
    # Set permission untuk semua file Python
    chmod +x *.py 2>/dev/null
    echo "Setup awal selesai!"
}

# Main script
main() {
    if ! command -v git &> /dev/null; then
        echo "Error: Git tidak terinstall. Silakan install git terlebih dahulu."
        exit 1
    fi
    
    if [ ! -d ".git" ]; then
        initial_setup
    fi
    
    echo "Memeriksa update dari GitHub..."
    git fetch origin
    
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})
    
    if [ $LOCAL != $REMOTE ]; then
        echo "Update tersedia!"
        read -p "Apakah Anda ingin update sekarang? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            update_script
        fi
    else
        echo "Semua file sudah dalam versi terbaru"
    fi
    
    # Jalankan script utama
    if [ -f "$MAIN_SCRIPT" ]; then
        python "$MAIN_SCRIPT"
    else
        echo "Error: $MAIN_SCRIPT tidak ditemukan!"
        exit 1
    fi
}

# Jalankan script
main "$@"
