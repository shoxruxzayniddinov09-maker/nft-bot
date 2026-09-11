import json
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from TelegramGifts import TelegramGifts
BOT_TOKEN = "8816999822:AAGEMuBg5JeEc7C4ZBJycbnuUE5K94dlWRI"
YOUR_CHAT_ID = 8578796045
CHECK_INTERVAL = 180
PRICE_FILE = "last_prices.json"

gifts = TelegramGifts(cache_mode="http", asset_mode="lazy")

def load_prices():
    if os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_prices(data):
    with open(PRICE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_cheapest_gifts(limit=12):
    popular = [
        "Candy Cane", "Loot Bag", "Jelly Bunny", "Homemade Cake",
        "Precious Peach", "Astral Shard", "Signet Ring", "Durov's Cap",
        "Artisan Brick", "Evil Eye", "Easter Egg", "Crystal Ball"
    ]
    results = []
    for name in popular:
        try:
            info = gifts.get_gift(name)
            if info and "prices" in info:
                prices = info["prices"]
                links = info.get("links", {})
                options = [
                ("Fragment", prices.get("floor_price_ton"), links.get("fragment")),
                ("GetGems", prices.get("getgems_price_ton"), links.get("getgems")),
                ("MRKT", prices.get("tgmrkt_price_ton"), links.get("tgmrkt")),
                ("Portals", prices.get("portal_price_ton"), links.get("portal")),
            ]
            valid = [(m, float(p), l) for m, p, l in options if p is not None and p > 0]
            if not valid:
                continue
            market, price, link = min(valid, key=lambda x: x[1])
            results.append({
                "name": info.get("full_name", name),
                "price": round(price, 2),
                "market": market,
                "link": link or "",
            })
        except Exception:
            continue
    return sorted(results, key=lambda x: x["price"])[:limit]

async def check_prices(context: ContextTypes.DEFAULT_TYPE):
    last_prices = load_prices()
    current = get_cheapest_gifts()
    messages = []

    for item in current:
        name = item["name"]
        price = item["price"]
        old_price = last_prices.get(name)
        should_notify = False
        reason = ""

        if price < 10:
            if old_price is None:
                should_notify = True
                reason = "Yangi arzon chiqdi"
            elif price <= old_price * 0.8:
                should_notify = True
                reason = f"20% arzonlashdi ({old_price} → {price} TON)"
            elif price < old_price:
                should_notify = True
                reason = f"Arzonlashdi ({old_price} → {price} TON)"

        if should_notify:
                                    messages.append(f"🔥 <b>{name}</b>\n💰 {price} TON\n🏪 {item.get('market','')}\n📌 {reason}\n🔗 {item.get('link','')}")
            
            
            

        last_prices[name] = price

    save_prices(last_prices)

    if messages:
        text = "🚨 <b>Yangi arzon NFT topildi!</b>\n\n" + "\n\n".join(messages)
        await context.bot.send_message(
            chat_id=YOUR_CHAT_ID,
            text=text,
            parse_mode="HTML",
        )

async def nfts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = get_cheapest_gifts()
    if not current:
        await update.message.reply_text("Hozircha ma'lumot topilmadi.")
        return
    text = "<b>🏆 Eng arzon Telegram NFT sovg'alari:</b>\n\n"
    for i, item in enumerate(current, 1):
                                text += f"{i}. <b>{item['name']}</b> — {item['price']} TON ({item.get('market','')})\n{item.get('link','')}\n"
            
                
    await update.message.reply_text(text, parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot ishga tushdi.\n"
        "10 TON dan arzon va 20% arzonlashgan NFT lar haqida xabar beraman.\n"
        "/nfts - hozirgi ro'yxat"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("nfts", nfts_command))
    app.job_queue.run_repeating(check_prices, interval=CHECK_INTERVAL, first=15)
    app.run_polling()

if __name__ == "__main__":
    main()
