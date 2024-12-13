import os
import json
import requests
import qrcode
import io
from flask import Flask, request, jsonify
from threading import Thread
from telegram import Bot, Update
from telegram.ext import CallbackContext, ConversationHandler
from uuid import uuid4

AWAITING_WALLET_NAME = 1

# Path to save Lightning wallets JSON file
LN_WALLETS_FILE = "ln_wallets.json"

# Dictionary to store user Lightning wallets
ln_user_wallets = {}

# Bot Token (replace with your actual bot token)
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
bot = Bot(token=BOT_TOKEN)

# Create a Flask app for webhook
webhook_app = Flask(__name__)

# =========================
# Support Functions
# =========================

def load_ln_wallets():
    """Load saved Lightning wallets from the JSON file."""
    global ln_user_wallets
    if os.path.exists(LN_WALLETS_FILE):
        with open(LN_WALLETS_FILE, "r") as f:
            ln_user_wallets = json.load(f)

def save_ln_wallets():
    """Save Lightning wallets to the JSON file."""
    try:
        with open(LN_WALLETS_FILE, "w") as f:
            json.dump(ln_user_wallets, f, indent=4)
        print("Lightning wallets successfully saved to ln_wallets.json")
    except Exception as e:
        print(f"Error saving Lightning wallets: {str(e)}")

# Load wallets on startup
load_ln_wallets()

# =========================
# Lightning Wallet Functions
# =========================

def create_ln_wallet(update: Update, context: CallbackContext):
    """Create a new Lightning wallet."""
    user_id = str(update.effective_user.id)
    wallet_name = f"lnwallet_{uuid4().hex[:8]}"

    headers = {
        "accept": "application/json",
        "X-API-KEY": "YOUR_LN_ADMIN_KEY",  # Replace with your LNBits admin key
        "Content-Type": "application/json"
    }

    payload = {
        "name": wallet_name
    }

    try:
        response = requests.post("https://your-lnbits-instance.com/api/v1/wallet", headers=headers, json=payload)
        if response.status_code in [200, 201]:
            wallet_data = response.json()
            ln_user_wallets[user_id] = {
                "ln_wallet_id": wallet_data["id"],
                "ln_admin_key": wallet_data["adminkey"],
                "ln_invoice_key": wallet_data["inkey"],
                "ln_wallet_name": wallet_name
            }
            save_ln_wallets()
            update.message.reply_text(
                f"⚡ *Lightning Wallet Created!*\n\n"
                f"🪪 *Wallet Name:* `{wallet_name}`\n"
                f"🔑 *Admin Key:* `{wallet_data['adminkey']}`\n"
                f"📥 *Invoice Key:* `{wallet_data['inkey']}`",
                parse_mode='Markdown'
            )
        else:
            update.message.reply_text(f"❌ Error creating wallet: {response.text}")
    except Exception as e:
        update.message.reply_text(f"❌ Exception: {str(e)}")

def check_ln_balance(update: Update, context: CallbackContext):
    """Check the balance of the user's Lightning wallet."""
    user_id = str(update.effective_user.id)
    if user_id not in ln_user_wallets:
        update.message.reply_text("❌ No Lightning wallet found. Use /create_ln_wallet to generate one.")
        return

    headers = {
        "accept": "application/json",
        "X-API-KEY": ln_user_wallets[user_id]["ln_admin_key"]
    }

    try:
        response = requests.get("https://your-lnbits-instance.com/api/v1/wallet", headers=headers)
        if response.status_code == 200:
            balance = response.json()["balance"] / 1000  # Convert millisatoshis to satoshis
            update.message.reply_text(f"⚡ *Lightning Wallet Balance:* {balance} sat", parse_mode='Markdown')
        else:
            update.message.reply_text(f"❌ Error fetching balance: {response.text}")
    except Exception as e:
        update.message.reply_text(f"❌ Exception: {str(e)}")

def create_ln_invoice(update: Update, context: CallbackContext):
    """Create a Lightning invoice."""
    user_id = str(update.effective_user.id)
    if user_id not in ln_user_wallets:
        update.effective_message.reply_text("❌ No Lightning wallet found. Use /create_ln_wallet to generate one.")
        return

    if len(context.args) != 2:
        update.effective_message.reply_text("❌ Usage: /create_ln_invoice [amount in sat] [memo]")
        return

    try:
        amount = int(context.args[0])
    except ValueError:
        update.effective_message.reply_text("❌ Invalid amount. Please enter a numeric value in sats.")
        return

    memo = context.args[1]

    headers = {
        "accept": "application/json",
        "X-API-KEY": ln_user_wallets[user_id]["ln_admin_key"],
        "Content-Type": "application/json"
    }

    payload = {
        "out": False,
        "amount": amount,
        "memo": memo
    }

    try:
        response = requests.post("https://your-lnbits-instance.com/api/v1/payments", headers=headers, json=payload)
        if response.status_code == 201:
            payment_request = response.json()["payment_request"]

            # Generate QR code
            qr = qrcode.QRCode()
            qr.add_data(payment_request)
            qr.make(fit=True)
            
            img = io.BytesIO()
            qr_img = qr.make_image(fill="black", back_color="white")
            qr_img.save(img, format="PNG")
            img.seek(0)

            # Send the invoice with the QR code
            update.effective_message.reply_photo(
                photo=img,
                caption=(
                    f"⚡ *Invoice Created!*\n\n"
                    f"💵 *Amount:* {amount} sat\n"
                    f"📝 *Memo:* {memo}\n\n"
                    f"🔗 *Payment Request:* `{payment_request}`"
                ),
                parse_mode='Markdown'
            )
        else:
            update.effective_message.reply_text(f"❌ Error creating invoice: {response.text}")
    except Exception as e:
        update.effective_message.reply_text(f"❌ Exception: {str(e)}")

# =========================
# Flask Webhook
# =========================

@webhook_app.route('/webhook_ln', methods=['POST'])
def webhook_ln():
    """Receive webhook notifications for incoming Lightning payments."""
    data = request.json
    print(f"Webhook received: {data}")

    payment_amount = data.get("amount", 0) / 1000  # Convert millisatoshis to satoshis
    memo = data.get("memo", "No memo")
    payment_hash = data.get("payment_hash", "Unknown")
    user_id = data.get("user", None)

    if user_id and user_id in ln_user_wallets:
        try:
            bot.send_message(
                chat_id=user_id,
                text=(
                    f"✅ *Payment Received!*\n\n"
                    f"💵 *Amount:* {payment_amount} sat\n"
                    f"📝 *Memo:* {memo}\n"
                    f"🔗 *Payment Hash:* `{payment_hash}`"
                ),
                parse_mode='Markdown'
            )
            return jsonify({"status": "success"}), 200
        except Exception as e:
            print(f"Error sending message: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": "User not found"}), 404

def run_webhook_server():
    """Run the Flask server for handling webhooks."""
    webhook_app.run(host='0.0.0.0', port=5050)

# Start the Flask server in a separate thread
Thread(target=run_webhook_server, daemon=True).start()
