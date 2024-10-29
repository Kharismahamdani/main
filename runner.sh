#!/bin/bash

# Konfigurasi
REPO_URL="https://github.com/Kharismahamdani/termux.py.git"
BRANCH="main"
SCRIPT_NAME="super.py"
UPDATE_INTERVAL=300  # Cek update setiap 5 menit

# Fungsi untuk setup awal
initial_setup() {
    echo "Melakukan setup awal..."
    
    # Install dependencies jika belum
    pkg update -y
    pkg install -y git python

    # Clone repository jika belum ada
    if [ ! -d "termux.py" ]; then
        git clone $REPO_URL
        cd termux.py
    else
        cd termux.py
        git fetch origin
        git reset --hard origin/$BRANCH
    fi

    # Install Python dependencies
    pip install aiohttp aiofiles requests

    # Set executable permissions
    chmod +x *.py
}

# Fungsi untuk update dari GitHub
check_update() {
    echo "Memeriksa update..."
    git fetch origin
    
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u})
    
    if [ $LOCAL != $REMOTE ]; then
        echo "Update ditemukan, mengupdate script..."
        git pull origin $BRANCH
        chmod +x *.py
        
        # Restart script setelah update
        echo "Update selesai, merestart script..."
        pkill -f $SCRIPT_NAME
        python $SCRIPT_NAME &
    else
        echo "Script sudah versi terbaru"
    fi
}

# Fungsi untuk monitoring script
monitor_script() {
    while true; do
        if ! pgrep -f $SCRIPT_NAME > /dev/null; then
            echo "Script tidak berjalan, menjalankan ulang..."
            python $SCRIPT_NAME &
        fi
        sleep 60
    done
}

# Main script
echo "Starting Auto-Update Runner..."
initial_setup

# Jalankan script utama
python $SCRIPT_NAME &

# Loop untuk auto update
while true; do
    check_update
    monitor_script &
    sleep $UPDATE_INTERVAL
done
