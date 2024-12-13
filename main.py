import requests
import time
import threading
import binascii
import bip32utils
import hashlib
import base58
import bech32
import matplotlib.pyplot as plt
import io
from bit import Key
from bip32 import BIP32
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters
from bip_utils import Bip84, Bip84Coins, Bip32KeyIndex
from bip32utils import BIP32Key
from Crypto.Hash import RIPEMD160, SHA256
from wallet_analysis import start_wallet_analysis, wallet_analysis, cancel, AWAITING_ZPUB, check_balance
from ln_wallet_manager import create_ln_wallet, check_ln_balance, create_ln_invoice
import os
from dotenv import load_dotenv
from telegram.ext import Updater, CommandHandler
from wallet_manager import create_wallet, check_balance, send_bitcoin, wallet_info
from ln_wallet_manager import start_create_ln_wallet, create_ln_wallet_with_name, cancel_create_ln_wallet, AWAITING_WALLET_NAME
from ln_wallet_manager import pay_ln_invoice, send_to_ln_address
from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, Filters

# Bot Token
BOT_TOKEN = 'YOUT BOT TOKEN'
# **Global variable for monitoring whale transactions**
whale_monitoring = {}
load_dotenv()
# **Global variable for price alert
price_alerts = {}
# File to  save wallets


#comand /start

def start(update: Update, context: CallbackContext):
    user_language = update.effective_user.language_code

    description_it = (
    "👋 *Benvenuto nel BTCWatcherBot!*\n\n"
    "Questo bot ti consente di monitorare la rete Bitcoin e la Lightning Network e molto altro ancora!\n\n"
    "• 🛠️ *Crea il tuo Wallet Bitcoin*: Genera un wallet Bitcoin direttamente nel bot, ricevi la tua seed phrase e mantieni il controllo totale delle tue chiavi (`/create_wallet`). La tua privacy è fondamentale! 🔐\n\n"
    "• 📈 *Prezzo Bitcoin*: Ottieni il prezzo attuale di Bitcoin in USD ed EUR (`/price`).\n"
    "• ⛽ *Tariffe di Transazione*: Visualizza le fee consigliate per le transazioni on-chain (`/calc_fee [size]`).\n"
    "• 📬 *Monitoraggio Nuovi Blocchi*: Ricevi notifiche quando viene minato un nuovo blocco (`/monitor_blocks`).\n"
    "• 📊 *Statistiche Blockchain*: Visualizza lo stato aggiornato della rete Bitcoin (`/stats`).\n\n"
    "🔍 Scopri molte altre funzionalità utili esplorando il menu dei comandi!\n\n"
    "🙏 Se trovi utile il bot e vuoi supportarlo, digita /donate."
)

    # Descrizione in inglese
    description_en = (
    "👋 *Welcome to BTCWatcherBot!*\n\n"
    "This bot helps you monitor the Bitcoin and Lightning Network, and much more!\n\n"
    "• 🛠️ *Create Your Bitcoin Wallet*: Generate a Bitcoin wallet directly in the bot, receive your seed phrase, and keep full control of your keys (`/create_wallet`). Your privacy is our priority! 🔐\n\n"
    "• 📈 *Bitcoin Price*: Get the current Bitcoin price in USD and EUR (`/price`).\n"
    "• ⛽ *Transaction Fees*: View recommended on-chain transaction fees (`/calc_fee [size]`).\n"
    "• 📬 *New Block Monitoring*: Get notified when a new block is mined (`/monitor_blocks`).\n"
    "• 📊 *Blockchain Stats*: Check the latest Bitcoin network status (`/stats`).\n\n"
    "🔍 Discover many more useful features by exploring the command menu!\n\n"
    "🙏 If you find this bot useful and want to support it, digit /donate."
)

    # **If the user has their language set to Italian, display the description in Italian.**
    if user_language == 'it':
        update.message.reply_text(description_it, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        # **Otherwise, display the description in English.**
        update.message.reply_text(description_en, parse_mode='Markdown', disable_web_page_preview=True)

def donate(update: Update, context: CallbackContext):
    user_language = update.effective_user.language_code

    # Message in italiano
    message_it = (
        "🙏 *Grazie per il tuo supporto!*\n\n"
        "Puoi donare tramite Lightning Network o Bitcoin on-chain:\n\n"
        "⚡ *Lightning Address*: `ln_address`\n\n"
        "💼 *Indirizzo BTC*: `btc_address`\n\n"
        "Ogni donazione aiuta a mantenere e migliorare il bot! Grazie di cuore! 💙"
    )

    # Message in inglese
    message_en = (
        "🙏 *Thank you for your support!*\n\n"
        "You can donate via Lightning Network or Bitcoin on-chain:\n\n"
        "⚡ *Lightning Address*: `ln_address`\n\n"
        "💼 *BTC Address*: `btc_address`\n\n"
        "Every donation helps maintain and improve the bot! Thank you so much! 💙"
    )

    # Send the message in the appropriate language.
    if user_language == 'it':
        update.message.reply_text(message_it, parse_mode='Markdown')
    else:
        update.message.reply_text(message_en, parse_mode='Markdown')



def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()





# Function to get detailed information about a Lightning Network node
def node_info(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("❌ Please provide a node public key. Usage: /node_info [public key]")
        return

    public_key = context.args[0]
    url = f'https://mempool.space/api/v1/lightning/nodes/{public_key}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        alias = data.get('alias', 'N/A')
        capacity = int(data.get('capacity', 0)) / 1e8  
        channels = data.get('channels', 'N/A')
        color = data.get('color', 'N/A')
        updated = data.get('updated', 'N/A')

        message = (
            f"🔎 *Lightning Node Info*\n\n"
            f"🏷️ Alias: {alias}\n"
            f"🔑 Public Key: `{public_key}`\n"
            f"💰 Capacity: {capacity:.2f} BTC\n"
            f"🔗 Channels: {channels}\n"
            f"🎨 Color: {color}\n"
            f"🕒 Last Updated: {updated}"
        )
    else:
        message = f"❌ Error fetching node information. Status code: {response.status_code}"

    update.message.reply_text(message, parse_mode='Markdown')



# Function to get Lightning Network stats from Mempool.space
def ln_stats(update: Update, context: CallbackContext):
    url = 'https://mempool.space/api/v1/lightning/statistics/latest'
    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json().get('latest', {})
            node_count = data.get('node_count', 'N/A')
            channel_count = data.get('channel_count', 'N/A')
            total_capacity = data.get('total_capacity', 'N/A') / 1e8  # Converti da satoshi a BTC
            avg_capacity = data.get('avg_capacity', 'N/A') / 1e8
            med_capacity = data.get('med_capacity', 'N/A') / 1e8

            message = (
                f"⚡ *Lightning Network Stats*\n\n"
                f"🖧 Nodes: {node_count}\n"
                f"🔗 Channels: {channel_count}\n"
                f"💰 Total Capacity: {total_capacity:.2f} BTC\n"
                f"📏 Average Channel Capacity: {avg_capacity:.2f} BTC\n"
                f"📈 Median Channel Capacity: {med_capacity:.2f} BTC"
            )
        except Exception as e:
            message = f"❌ Error parsing Lightning Network stats: {str(e)}"
    else:
        message = f"❌ Error fetching Lightning Network stats. Status code: {response.status_code}"

    update.message.reply_text(message, parse_mode='Markdown')

# Function to track a Bitcoin transaction
def track_tx(update: Update, context: CallbackContext):
    try:
        txid = context.args[0]
        chat_id = update.effective_chat.id
        update.message.reply_text(f"🔍 Tracking transaction: {txid}\nPlease wait for confirmation...")

        def check_transaction_status():
            url = f'https://blockstream.info/api/tx/{txid}'
            while True:
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data['status']['confirmed']:
                        context.bot.send_message(chat_id=chat_id, text=f"✅ *Transaction Confirmed!*\n\n🆔 TXID: {txid}")
                        break
                time.sleep(60)  # Controlla ogni 60 secondi

        threading.Thread(target=check_transaction_status).start()

    except IndexError:
        update.message.reply_text("❌ Please provide a TXID. Usage: /track_tx [txid]")


# Function to calculate estimated fee for a transaction
def calc_fee(update: Update, context: CallbackContext):
    try:
        if not context.args:
            raise ValueError  

        size = int(context.args[0])
        fees_data = get_fees()
        if fees_data:
            fastest_fee = size * fees_data['fastest']
            half_hour_fee = size * fees_data['half_hour']
            hour_fee = size * fees_data['hour']
            message = (
                f"🧮 *Estimated Transaction Fees*\n\n"
                f"🚀 Fastest \\(10 min\\): {fastest_fee} sat\n"
                f"⚡ Half Hour \\(30 min\\): {half_hour_fee} sat\n"
                f"🐢 Hour \\(60 min\\): {hour_fee} sat"
            )
        else:
            message = "❌ Error fetching network fees."
    except (IndexError, ValueError):
        message = "❌ Please provide a valid transaction size in bytes\\. Usage: /calc\\_fee \\[size\\]"

    update.message.reply_text(message, parse_mode='MarkdownV2')

# Function to show price trend for the last 24 hours
def price_trend(update: Update, context: CallbackContext):
    url = 'https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        prices = [price[1] for price in data['prices']]
        times = [price[0] / 1000 for price in data['prices']]  

       
        times = [time.strftime('%H:%M', time.gmtime(t)) for t in times]

        
        plt.figure(figsize=(10, 5))
        plt.plot(times, prices, label="BTC Price (USD)")
        plt.xticks(rotation=45)
        plt.title("Bitcoin Price Trend (Last 24 Hours)")
        plt.xlabel("Time")
        plt.ylabel("Price (USD)")
        plt.legend()
        plt.grid()

       
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        update.message.reply_photo(photo=buf)
        buf.close()
        plt.close()
    else:
        update.message.reply_text("❌ Error fetching price trend data.")


fee_alerts = {}

# Function to check mempool fees periodically for alerts
def check_fee_alerts(context: CallbackContext):
    while True:
        fees_data = get_fees()
        if fees_data:
            for chat_id, threshold in list(fee_alerts.items()):
                if fees_data['fastest'] <= threshold:
                    context.bot.send_message(chat_id=chat_id, text=f"🚨 *Fee Alert!* Fastest fee is now {fees_data['fastest']} sat/vB")
                    del fee_alerts[chat_id]  # Rimuove l'alert dopo aver inviato la notifica
        time.sleep(60)  # Controlla ogni 60 secondi

# Command to set a fee alert
def set_fee_alert(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    try:
        threshold = int(context.args[0])
        fee_alerts[chat_id] = threshold
        update.message.reply_text(f"🔔 Fee alert set for {threshold} sat/vB!")
    except (IndexError, ValueError):
        update.message.reply_text("❌ Please provide a valid fee threshold. Usage: /set_fee_alert [fee]")



# Function to check BTC price periodically for alerts
def check_price_alerts(context: CallbackContext):
    while True:
        usd_price, _ = get_price()
        if usd_price:
            for chat_id, threshold in list(price_alerts.items()):
                if usd_price >= threshold:
                    context.bot.send_message(chat_id=chat_id, text=f"🚨 *Price Alert!* Bitcoin has reached ${usd_price}")
                    del price_alerts[chat_id]  # Rimuove l'alert dopo aver inviato la notifica
        time.sleep(60)  # Controlla ogni 60 secondi

# Command to set a price alert
def set_price_alert(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    try:
        threshold = float(context.args[0])
        price_alerts[chat_id] = threshold
        update.message.reply_text(f"🔔 Price alert set for ${threshold}!")
    except (IndexError, ValueError):
        update.message.reply_text("❌ Please provide a valid price threshold. Usage: /set_price_alert [price]")


# Function to get BTC price in USD and EUR
def get_price():
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        usd_price = data['bitcoin']['usd']
        eur_price = data['bitcoin']['eur']
        return usd_price, eur_price
    else:
        return None, None

# Command to show BTC price
def price(update: Update, context: CallbackContext):
    usd_price, eur_price = get_price()
    if usd_price and eur_price:
        message = f"💰 *Bitcoin Price*\n\n" \
                  f"💵 USD: ${usd_price}\n" \
                  f"💶 EUR: €{eur_price}"
    else:
        message = "❌ Error fetching the Bitcoin price."
    update.message.reply_text(message, parse_mode='Markdown')

# Function to get current mempool fees
def get_fees():
    url = 'https://mempool.space/api/v1/fees/recommended'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        fees = {
            "fastest": data['fastestFee'],
            "half_hour": data['halfHourFee'],
            "hour": data['hourFee']
        }
        return fees
    else:
        return None

# Command to show current fees
def fees(update: Update, context: CallbackContext):
    fees_data = get_fees()
    if fees_data:
        message = f"⛽ *Current Network Fees*\n\n" \
                  f"🚀 Fastest (10 min): {fees_data['fastest']} sat/vB\n" \
                  f"⚡ Half Hour (30 min): {fees_data['half_hour']} sat/vB\n" \
                  f"🐢 Hour (60 min): {fees_data['hour']} sat/vB"
    else:
        message = "❌ Error fetching network fees."
    update.message.reply_text(message, parse_mode='Markdown')

# Function to get the latest block height
def get_latest_block_height():
    url = 'https://blockstream.info/api/blocks/tip/height'
    response = requests.get(url)
    if response.status_code == 200:
        return int(response.text)
    else:
        return None

# Function to monitor new blocks (notifica un solo blocco e si ferma)
def monitor_new_blocks(chat_id, context: CallbackContext):
    current_height = get_latest_block_height()
    if current_height is None:
        context.bot.send_message(chat_id=chat_id, text="❌ Error fetching the latest block height.")
        return

    context.bot.send_message(chat_id=chat_id, text=f"🚀 Monitoring the next block. Current height: {current_height}")

    while True:
        latest_height = get_latest_block_height()
        if latest_height and latest_height > current_height:
            message = f"🔗 *New Block Mined!*\n\n" \
                      f"🆙 Block Height: {latest_height}\n" \
                      f"🔍 [View Block](https://blockstream.info/block-height/{latest_height})"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            break  # Interrompe il monitoraggio dopo la prima notifica
        time.sleep(60)

# Command to start block monitoring
def start_block_monitoring(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    update.message.reply_text("🚀 Started monitoring for new blocks!")
    threading.Thread(target=monitor_new_blocks, args=(chat_id, context)).start()

# Command to provide security tips
def security(update: Update, context: CallbackContext):
    tips = (
        "🔐 *Bitcoin Security Tips*\n\n"
        "1. Use a hardware wallet for large amounts.\n"
        "2. Never share your private keys.\n"
        "3. Enable 2FA on exchanges.\n"
        "4. Verify addresses before sending.\n"
        "5. Use CoinJoin to improve privacy."
    )
    update.message.reply_text(tips, parse_mode='Markdown')

# Command to show blockchain stats

def stats(update: Update, context: CallbackContext):
    try:
        
        block_height_url = 'https://mempool.space/api/blocks/tip/height'
        block_height_response = requests.get(block_height_url)
        block_height = block_height_response.text if block_height_response.status_code == 200 else 'N/A'

        
        mempool_url = 'https://mempool.space/api/mempool'
        mempool_response = requests.get(mempool_url)
        if mempool_response.status_code == 200:
            mempool_data = mempool_response.json()
            mempool_count = mempool_data.get('count', 'N/A')
            mempool_vsize = mempool_data.get('vsize', 'N/A')
        else:
            mempool_count = mempool_vsize = 'N/A'

        
        difficulty_url = 'https://mempool.space/api/v1/difficulty-adjustment'
        difficulty_response = requests.get(difficulty_url)
        if difficulty_response.status_code == 200:
            difficulty_data = difficulty_response.json()
            difficulty_percentage = difficulty_data.get('difficultyChange', 'N/A')
            remaining_blocks = difficulty_data.get('remainingBlocks', 'N/A')
        else:
            difficulty_percentage = remaining_blocks = 'N/A'

        
        hashrate_url = 'https://mempool.space/api/v1/mining/pool/foundryusa/hashrate'
        hashrate_response = requests.get(hashrate_url)
        if hashrate_response.status_code == 200:
            hashrate_data = hashrate_response.json()
            avg_hashrate = sum(item['avgHashrate'] for item in hashrate_data) / len(hashrate_data)
            avg_hashrate_eh = avg_hashrate / 1e18  # Converti in EH/s
        else:
            avg_hashrate_eh = 'N/A'

        
        message = (
            f"📊 *Blockchain Stats*\n\n"
            f"📈 Block Height: {block_height}\n"
            f"⏳ Mempool Transactions: {mempool_count}\n"
            f"📦 Mempool Size: {mempool_vsize} vB\n"
            f"⚒️ Difficulty Change: {difficulty_percentage}%\n"
            f"🕒 Blocks Until Adjustment: {remaining_blocks}\n"
            f"🔗 Network Hashrate: {avg_hashrate_eh:.2f} EH/s"
        )

    except Exception as e:
        message = f"❌ Error fetching blockchain stats: {str(e)}"

    update.message.reply_text(message, parse_mode='Markdown')



import numpy as np

def fee_forecast(update: Update, context: CallbackContext):
    url = 'https://mempool.space/api/v1/fees/mempool-blocks'
    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()

            
            fees = [round(block['medianFee'], 1) for block in data[:6]]

            message = (
                "\ud83d\udcc9 *Fee Forecast*\n\n"
                f"\u23f3 1 Hour:\n"
                f"\ud83d\ude80 High Priority: {fees[0]} sat/vB\n"
                f"\u26a1 Medium Priority: {fees[1]} sat/vB\n"
                f"\ud83d\udc11 Low Priority: {fees[2]} sat/vB\n\n"
                f"\u23f3 3 Hours:\n"
                f"\ud83d\ude80 High Priority: {fees[3]} sat/vB\n"
                f"\u26a1 Medium Priority: {fees[4]} sat/vB\n"
                f"\ud83d\udc11 Low Priority: {fees[5]} sat/vB\n"
            )
        except Exception as e:
            message = f"\u274c Error parsing fee forecast data: {str(e)}"
    else:
        message = "\u274c Error fetching fee forecast data."

    update.message.reply_text(message, parse_mode='Markdown')


# Command to monitor large unconfirmed transactions
def monitor_whales(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    threshold = int(context.args[0]) if context.args else 100
    update.message.reply_text(f"🐋 Monitoring for transactions larger than {threshold} BTC...")

    def check_large_transactions():
        seen_txids = set()
        whale_monitoring[chat_id] = True
        while whale_monitoring.get(chat_id, False):
            url = 'https://mempool.space/api/mempool/recent'
            response = requests.get(url)
            if response.status_code == 200:
                transactions = response.json()
                for tx in transactions:
                    amount = tx['value'] / 1e8
                    txid = tx['txid']
                    if amount >= threshold and txid not in seen_txids:
                        seen_txids.add(txid)
                        message = f"🐋 *Large BTC Transaction Detected!*\n\n" \
                                  f"💼 Amount: {amount:.2f} BTC\n" \
                                  f"🔗 [View Transaction](https://mempool.space/tx/{txid})"
                        context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
            time.sleep(300)

    threading.Thread(target=check_large_transactions).start()

# Command to stop monitoring large transactions
def stop_monitor_whales(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    whale_monitoring[chat_id] = False
    update.message.reply_text("🛑 Stopped monitoring large transactions.")
import requests


def get_watchonly_balance(zpub):
    url = f"https://blockchain.info/balance?active={zpub}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        balance = data.get(zpub, {}).get('final_balance', 0) / 1e8  # Converti satoshi in BTC
        return balance
    else:
        return None


def set_watchonly_wallet(update, context):
    zpub = context.args[0]
    balance = get_watchonly_balance(zpub)
    if balance is not None:
        update.message.reply_text(f"💰 Watch-only wallet balance: {balance} BTC")
    else:
        update.message.reply_text("❌ Failed to retrieve balance. Please check the zpub and try again.")



def arbitrage(update: Update, context: CallbackContext):
    exchanges = ['binance', 'coinbase-pro', 'kraken']
    prices = {}
    
    for exchange in exchanges:
        url = f'https://api.coingecko.com/api/v3/exchanges/{exchange}/tickers?coin_ids=bitcoin'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            tickers = data.get('tickers', [])
            price = next((ticker.get('last') for ticker in tickers if ticker.get('target') == 'USD'), 'N/A')
            prices[exchange] = price
        else:
            prices[exchange] = 'N/A'
    
    message = (
        "\ud83d\udcca *Bitcoin Arbitrage Opportunities*\n\n"
        f"\ud83d\udcc8 Binance: ${prices['binance']}\n"
        f"\ud83d\udcc8 Coinbase: ${prices['coinbase-pro']}\n"
        f"\ud83d\udcc8 Kraken: ${prices['kraken']}\n"
    )
    
    update.message.reply_text(message, parse_mode='Markdown')


def fiat_rates(update: Update, context: CallbackContext):
    url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,eur,gbp,jpy,cny'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json().get('bitcoin', {})
        message = (
            "\ud83c\udf0d *Bitcoin to Fiat Exchange Rates*\n\n"
            f"\ud83d\udcb5 USD: ${data.get('usd', 'N/A')}\n"
            f"\ud83d\udcb6 EUR: \u20ac{data.get('eur', 'N/A')}\n"
            f"\ud83d\udcb8 GBP: \u00a3{data.get('gbp', 'N/A')}\n"
            f"\ud83c\uddef\ud83c\uddf5 JPY: \u00a5{data.get('jpy', 'N/A')}\n"
            f"\ud83c\udde8\ud83c\uddf3 CNY: \u00a5{data.get('cny', 'N/A')}\n"
        )
    else:
        message = "\u274c Error fetching fiat exchange rates."

    update.message.reply_text(message, parse_mode='Markdown')


# Main function to run the bot
def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('wallet_analysis', start_wallet_analysis)],
        states={
            AWAITING_ZPUB: [MessageHandler(Filters.text & ~Filters.command, wallet_analysis)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    dispatcher.add_handler(conv_handler)
    # Parte conversione ln wallet creazione
    conv_handler_ln_wallet = ConversationHandler(
    entry_points=[CommandHandler('create_ln_wallet', start_create_ln_wallet)],
    states={
        AWAITING_WALLET_NAME: [MessageHandler(Filters.text & ~Filters.command, create_ln_wallet_with_name)],
    },
    fallbacks=[CommandHandler('cancel', cancel_create_ln_wallet)]
    )

    dispatcher.add_handler(conv_handler_ln_wallet)

    # Aggiungi il comando /start
    dispatcher.add_handler(CommandHandler('start', start))
    # Aggiunta del comando `arbitrage`
    dispatcher.add_handler(CommandHandler('arbitrage', arbitrage))
    # Aggiungi il gestore per la pressione dei pulsanti
    dispatcher.add_handler(CallbackQueryHandler(button))

   
    dispatcher.add_handler(CommandHandler('price', price))
    dispatcher.add_handler(CommandHandler('fees', fees))
    dispatcher.add_handler(CommandHandler('monitor_blocks', start_block_monitoring))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('security', security))
    dispatcher.add_handler(CommandHandler('monitor_whales', monitor_whales, pass_args=True))
    dispatcher.add_handler(CommandHandler('stop_monitor_whales', stop_monitor_whales))
    dispatcher.add_handler(CommandHandler('set_price_alert', set_price_alert))

    
    threading.Thread(target=check_price_alerts, args=(updater,), daemon=True).start()

    
    dispatcher.add_handler(CommandHandler('ln_stats', ln_stats))
    dispatcher.add_handler(CommandHandler('track_tx', track_tx, pass_args=True))
    dispatcher.add_handler(CommandHandler('calc_fee', calc_fee, pass_args=True))
    dispatcher.add_handler(CommandHandler('price_trend', price_trend))
    dispatcher.add_handler(CommandHandler('set_fee_alert', set_fee_alert, pass_args=True))
    dispatcher.add_handler(CommandHandler('node_info', node_info, pass_args=True))
    dispatcher.add_handler(CallbackQueryHandler(check_balance, pattern='^check_balance$'))
    dispatcher.add_handler(CommandHandler('donate', donate))
    dispatcher.add_handler(CommandHandler('create_wallet', create_wallet))
    dispatcher.add_handler(CommandHandler('check_balance', check_balance))
    dispatcher.add_handler(CommandHandler('send_bitcoin', send_bitcoin))
    dispatcher.add_handler(CommandHandler('wallet_info', wallet_info))
    
    dispatcher.add_handler(CommandHandler('fiat_rates', fiat_rates))
    
    dispatcher.add_handler(CommandHandler('create_ln_wallet', create_ln_wallet))
    dispatcher.add_handler(CommandHandler('check_ln_balance', check_ln_balance))
    dispatcher.add_handler(CommandHandler('create_ln_invoice', create_ln_invoice, pass_args=True))
   
    dispatcher.add_handler(CommandHandler('pay_ln_invoice', pay_ln_invoice, pass_args=True))
    dispatcher.add_handler(CommandHandler('send_to_ln_address', send_to_ln_address, pass_args=True))
    
    dispatcher.add_handler(CommandHandler('fee_forecast', fee_forecast))
    updater.start_polling()
    updater.idle()

# Avvia il bot
if __name__ == '__main__':
    main()
