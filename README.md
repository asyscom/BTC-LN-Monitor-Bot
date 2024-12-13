
```markdown
# ⚡ BTCWatcherBot

BTCWatcherBot is a comprehensive Telegram bot that helps you monitor Bitcoin and the Lightning Network. It supports creating Bitcoin wallets, Lightning wallets (via LNbits), tracking prices, fees, transactions, and more!

## 📌 **Features**

- 🛠 **Create Bitcoin Wallets** and generate seed phrases.
- ⚡ **Create Lightning Wallets** and manage invoices/payments via LNbits.
- 💰 **Check Balances** for both Bitcoin and Lightning wallets.
- 📈 **Track Bitcoin Prices** in USD and EUR.
- ⛽ **Check Transaction Fees** and set alerts.
- 🔗 **Monitor Blockchain Events** like new blocks and large transactions.
- 🔔 **Set Price and Fee Alerts** with real-time notifications.
- 📝 **Receive Lightning Payments** and generate QR codes for invoices.

## 🚀 **Getting Started**

### 🔧 **Prerequisites**

Ensure you have the following installed:

- **Python 3.10+**
- **Telegram Bot Token** (from [BotFather](https://core.telegram.org/bots#botfather))
- **LNbits Instance** for Lightning wallet operations
- **Flask** for webhook server

### 📦 **Dependencies**

Install required packages:

```bash
pip install requests python-telegram-bot==13.7 bit mnemonic qrcode flask python-dotenv
```

### ⚙️ **Environment Variables**

Create a `.env` file to store your bot token:

```
BOT_TOKEN=your_telegram_bot_token
```

### 📂 **Project Structure**

```
BTCWatcherBot/
│-- main.py
│-- wallet_manager.py
│-- ln_wallet_manager.py
│-- wallets.json
│-- ln_wallets.json
└-- .env
```

### 🚀 **Running the Bot**

1. **Start the Bot**:

   ```bash
   python3 main.py
   ```

2. **Start the Webhook Server** for Lightning payments (Flask runs on port 5050):

   The webhook server runs automatically in a separate thread when the bot starts.

### 📝 **Commands**

#### 🛠 **Bitcoin Wallet Commands**

- `/create_wallet` – Create a new Bitcoin wallet.
- `/check_balance` – Check your Bitcoin wallet balance.
- `/send_bitcoin [address] [amount]` – Send Bitcoin to a specified address.
- `/wallet_info` – Show your wallet information.

#### ⚡ **Lightning Wallet Commands**

- `/create_ln_wallet` – Create a new Lightning wallet.
- `/check_ln_balance` – Check your Lightning wallet balance.
- `/create_ln_invoice [amount] [memo]` – Create a Lightning invoice and QR code.
- `/pay_ln_invoice [bolt11_invoice]` – Pay a Lightning invoice.
- `/send_to_ln_address [ln_address] [amount]` – Send sats to a Lightning Address.

#### 🔍 **Blockchain Monitoring**

- `/price` – Get the current Bitcoin price.
- `/fees` – Check current transaction fees.
- `/monitor_blocks` – Monitor new Bitcoin blocks.
- `/track_tx [txid]` – Track a Bitcoin transaction.
- `/stats` – Get Bitcoin network stats.
- `/ln_stats` – Get Lightning Network stats.

#### 🔔 **Alerts**

- `/set_price_alert [price]` – Set a price alert.
- `/set_fee_alert [fee]` – Set a fee alert.

---

## ⚠️ **Security Notice**

- **Keep your seed phrases and private keys secure!**
- Avoid sharing your admin keys and bot tokens.

## 📄 **License**

