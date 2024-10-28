# setup.sh
pkg update -y && pkg upgrade -y
pkg install python -y
pip install aiohttp aiofiles
python termux.py
