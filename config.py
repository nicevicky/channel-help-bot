import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
MAIN_ADMIN_ID = int(os.getenv('MAIN_ADMIN_ID'))
CRYPTO_WALLET_BTC = os.getenv('CRYPTO_WALLET_BTC')
CRYPTO_WALLET_ETH = os.getenv('CRYPTO_WALLET_ETH')
BANK_DETAILS = os.getenv('BANK_DETAILS')

# Upgrade prices
UPGRADE_PRICE_STARS = 100
UPGRADE_PRICE_USD = 5
