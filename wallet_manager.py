import os
import json
from mnemonic import Mnemonic
from bip32utils import BIP32Key, BIP32_HARDEN
from telegram import Update
from telegram.ext import CallbackContext
from bit import Key
from bit.format import bytes_to_wif
from bit.network import NetworkAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Dictionary to store users' wallets
user_wallets = {}

# Path to the JSON file for saving wallets
WALLETS_FILE = "wallets.json"
print(f"Saving path: {os.path.abspath(WALLETS_FILE)}")

# =========================
# Functions to Load and Save Wallets
# =========================

def load_wallets():
    """Load wallets from the JSON file."""
    global user_wallets
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, "r") as f:
            user_wallets = json.load(f)

def save_wallets():
    """Save wallets to the JSON file."""
    try:
        with open(WALLETS_FILE, "w") as f:
            json.dump(user_wallets, f, indent=4)
        print("Wallets successfully saved to wallets.json")
    except Exception as e:
        print(f"Error saving wallets: {str(e)}")

# Load wallets on startup
load_wallets()

# =========================
# Wallet Commands
# =========================

def create_wallet(update: Update, context: CallbackContext):
    """Create a new Bitcoin wallet for the user."""
    user_id = str(update.effective_user.id)
    mnemo = Mnemonic("english")
    seed_phrase = mnemo.generate(strength=128)
    seed = mnemo.to_seed(seed_phrase)
    
    master_key = BIP32Key.fromEntropy(seed)
    child_key = master_key.ChildKey(0 + BIP32_HARDEN).ChildKey(0).ChildKey(0)
    address = child_key.Address()
    private_key_wif = bytes_to_wif(child_key.PrivateKey())
    
    user_wallets[user_id] = {
        "seed_phrase": seed_phrase,
        "address": address,
        "private_key": private_key_wif
    }
    
    save_wallets()
    print(f"user_wallets: {user_wallets}")
    
    message = (
        "💰 *Bitcoin Wallet Created!*\n\n"
        f"🧩 *Seed Phrase:* `{seed_phrase}`\n"
        f"💳 *Address:* `{address}`\n"
        f"🗒 *Private Key (WIF):* `{private_key_wif}`\n\n"
        "🚫 *Keep your seed phrase and private key secure!*"
    )
    update.message.reply_text(message, parse_mode='Markdown')

def check_balance(update: Update, context: CallbackContext):
    """Check the balance of the user's Bitcoin wallet."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_wallets:
        update.message.reply_text("❌ No wallet found. Use /create_wallet to generate one.")
        return
    
    address = user_wallets[user_id]['address']
    
    try:
        balance = NetworkAPI.get_balance(address)
        balance_btc = balance / 1e8
        update.message.reply_text(f"💰 Balance for {address}: {balance_btc} BTC")
    except Exception as e:
        update.message.reply_text(f"❌ Error fetching balance: {str(e)}")

def wallet_info(update: Update, context: CallbackContext):
    """Display the user's wallet information."""
    user_id = str(update.effective_user.id)
    
    if user_id not in user_wallets:
        update.message.reply_text("❌ No wallet found. Use /create_wallet to generate one.")
        return
    
    wallet = user_wallets[user_id]
    message = (
        "💰 *Your Wallet Info:*\n\n"
        f"💳 *Address:* `{wallet['address']}`\n"
        f"🧩 *Seed Phrase:* `{wallet['seed_phrase']}`\n"
        f"🗒 *Private Key (WIF):* `{wallet['private_key']}`\n"
    )
    update.message.reply_text(message, parse_mode='Markdown')

def send_bitcoin(update: Update, context: CallbackContext):
    """Send Bitcoin to a specified recipient address."""
    user_id = str(update.effective_user.id)
    
    # Check if the user has a wallet
    if user_id not in user_wallets:
        update.message.reply_text("❌ No wallet found. Use /create_wallet to generate one.")
        return

    # Verify that the correct arguments are provided
    if len(context.args) != 2:
        update.message.reply_text("❌ Usage: /send_bitcoin [recipient_address] [amount]")
        return
    
    recipient = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        update.message.reply_text("❌ Invalid amount. Please enter a numeric value.")
        return

    # Extract the user's private key
    private_key_wif = user_wallets[user_id]['private_key']
    
    try:
        # Create a key using the 'bit' library
        key = Key(private_key_wif)
        
        # Send Bitcoin to the specified recipient
        tx_hash = key.send([(recipient, amount, 'btc')])
        
        # Notify the user of the successful transaction
        update.message.reply_text(f"✅ Transaction sent successfully!\n\n🔗 TXID: {tx_hash}")
    except Exception as e:
        # In case of an error, notify the user
        update.message.reply_text(f"❌ Error sending Bitcoin: {str(e)}")
