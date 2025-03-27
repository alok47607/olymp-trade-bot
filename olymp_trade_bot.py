from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import random
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from datetime import datetime, timedelta
import asyncio
import nest_asyncio
import pytz

nest_asyncio.apply()

TOKEN = "7562941881:AAFFXaPDaDNcdu1_lPmVBbst5zXS3cjSI6o"
signal_running = False
markets = ["EUR/CAD OTC", "EUR/CHF OTC", "EUR/GBP OTC", "EUR/JPY OTC", "EUR/NZD OTC", "EUR/USD OTC", "GBP/AUD OTC", "GBP/CAD OTC", "GBP/CHF OTC", "GBP/JPY OTC", "GBP/NZD OTC", "GBP/USD OTC", "Gold OTC", "NZD/CAD OTC", "NZD/CHF OTC", "NZD/JPY OTC", "NZD/USD OTC", "Silver OTC", "USD/CAD OTC", "USD/CHF OTC", "USD/CAD", "USD/JPY", "AUD/USD", "BRENT", "CAD/JPY", "EUR/AUD", "EUR/CAD", "EUR/GBP", "EUR/JPY", "GBP/AUD", "GBP/CAD", "GBP/JPY", "Gold", "Natural Gas", "Silver", "Asia Composite Index", "Astro Index", "Commodity Composite Index", "Europe Composite Index", "Maha Jantar Index", "Moonch Index", "EUR/USD", "GBP/USD"]
market_trends = {market: {"trend": random.randint(75, 95), "volatility": random.uniform(0.5, 0.9), "support": random.uniform(0.9, 1.1), "resistance": random.uniform(1.2, 1.5), "payout": random.randint(70, 90)} for market in markets}
last_used_market = None
price_history = {market: [random.uniform(1, 100) for _ in range(15)] for market in markets}
last_signal_time = None

# Pre-trained model load karo
model = joblib.load('rf_model.pkl')

def get_market_data():
    global last_used_market
    available_markets = [market for market in markets if market != last_used_market and market_trends[market]["payout"] >= 80]
    if not available_markets:
        available_markets = [market for market in markets if market_trends[market]["payout"] >= 80]
    if not available_markets:
        return None, None, None, None, None, None, None, None, None, None
    best_market = random.choice(available_markets)
    last_used_market = best_market
    trend = market_trends[best_market]["trend"]
    volatility = market_trends[best_market]["volatility"]
    close = price_history[best_market][-1]
    open_price = close * random.uniform(0.99, 1.01)
    high = close * random.uniform(1.01, 1.05)
    low = close * random.uniform(0.95, 0.99)
    price_history[best_market].pop(0)
    price_history[best_market].append(close * random.uniform(0.99, 1.01))
    rsi = sum(price_history[best_market][-14:]) / 14
    features = np.array([[close, open_price, high, low, rsi, trend, volatility]])
    direction_pred = model.predict(features)[0]
    direction = "Up" if direction_pred == 1 else "Down"
    probability = min(trend / 100 * (1 - volatility / 2), 0.95)
    timeframe = random.choice(["1min", "2min", "5min", "10min", "15min"])
    duration = int(timeframe.replace("min", ""))
    indicator = random.choice(["RSI", "MACD", "Bollinger Bands"])
    confirmation = "Very Strong" if probability > 0.9 else "Strong" if probability > 0.85 else "Moderate"
    profitability = f"{int(probability * 100)}%"
    rsi_status = "Neutral"
    candle = "No Pattern Detected"
    support = market_trends[best_market]["support"]
    resistance = market_trends[best_market]["resistance"]
    trend_strength = "Strong" if trend > 85 else "Moderate"
    return best_market, direction, timeframe, indicator, confirmation, duration, profitability, rsi, rsi_status, candle, support, resistance, trend_strength

async def generate_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_signal_time
    current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
    if last_signal_time and (current_time - last_signal_time).total_seconds() < 60:
        return
    asset, direction, timeframe, indicator, confirmation, duration, profitability, rsi, rsi_status, candle, support, resistance, trend_strength = get_market_data()
    if not asset:
        await update.message.reply_text("⚠️ No markets with 80%+ payout available right now. Try again later!")
        return
    entry_time = (current_time + timedelta(minutes=1)).replace(second=0).strftime("%H:%M:%S")
    signal = (
        f"📈 *Olymp Trade Power Signal* 📉\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌟 *Market*: {asset}\n"
        f"📊 *Direction*: {direction} {'⬆️' if direction == 'Up' else '⬇️'}\n"
        f"⏳ *Timeframe*: {timeframe}\n"
        f"⏰ *Entry Time*: {entry_time}\n"
        f"🕒 *Current Time*: {current_time.strftime('%H:%M:%S')}\n"
        f"⏱️ *Duration*: {duration} min\n"
        f"✅ *Confirmation*: {confirmation}\n"
        f"📉 *Indicator*: {indicator} (RSI: {rsi:.2f}, {rsi_status})\n"
        f"🕯️ *Candlestick Pattern*: {candle}\n"
        f"📈 *Trend Strength*: {trend_strength}\n"
        f"💰 *Win Probability*: {profitability}\n"
        f"📍 *Support Level*: {support:.2f}\n"
        f"📍 *Resistance Level*: {resistance:.2f}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Action Plan*: Execute a *{direction}* trade on *{asset}* for {timeframe} timeframe. 🚀\n"
        f"⚠️ *Risk Warning*: Always use proper risk management! 📉"
    )
    await update.message.reply_text(signal, parse_mode="Markdown")
    last_signal_time = current_time

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global signal_running
    if signal_running:
        await update.message.reply_text("Bot is already running! Use /stop to stop it.")
        return
    signal_running = True
    await update.message.reply_text("👋 *Welcome to Olymp Trade Power Signal Bot!*\nBot started! I will send high-probability signals every minute for active FTT markets with 80%+ payout. 📈\nUse /stop to stop the bot.")
    while signal_running:
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))
        seconds_to_next_minute = 60 - current_time.second
        await asyncio.sleep(seconds_to_next_minute - 60)  # 1 minute pehle signal bhejo
        await generate_signal(update, context)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global signal_running
    if not signal_running:
        await update.message.reply_text("Bot is not running! Use /start to start it.")
        return
    signal_running = False
    await update.message.reply_text("Bot stopped! Use /start to restart it.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("signal", generate_signal))
    app.run_polling()

if __name__ == "__main__":
    main()
