import logging
import requests
import json
import random
import difflib
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIG =================
TELEGRAM_BOT_TOKEN = "8659082673:AAFkqGMuenhC2L34hhcKhEne6-Fg82Xo6RM"

USER_KEYS = {}
USERNAMES = {}
BLOCKED_USERS = set()

BLOCK_FILE = "blocked.json"

# ================= LOAD BLOCKED =================
try:
    BLOCKED_USERS = set(json.load(open(BLOCK_FILE)))
except:
    BLOCKED_USERS = set()

def save_blocked():
    json.dump(list(BLOCKED_USERS), open(BLOCK_FILE, "w"))

# ================= EMOTIONS =================
MOODS = ["🟢 Calm", "🟡 Thinking", "🔵 Focused", "🟣 Curious", "🟠 Smart Mode"]

# ================= KNOWLEDGE MEMORY =================
KNOWLEDGE = {
    "what is ai": "AI means Artificial Intelligence, systems that simulate human thinking.",
    "what is python": "Python is a programming language used for apps, AI and automation.",
    "capital of nigeria": "Abuja is the capital of Nigeria."
}

# ================= FUZZY MATCH (FEATURE 2) =================
def fuzzy_match(query):
    keys = list(KNOWLEDGE.keys())
    match = difflib.get_close_matches(query, keys, n=1, cutoff=0.6)

    if match:
        return KNOWLEDGE[match[0]], 0.85
    return None, 0

# ================= SEARCH =================
def search_google(query, api_key):
    url = "https://serpapi.com/search"

    params = {
        "q": query,
        "api_key": api_key,
        "engine": "google"
    }

    r = requests.get(url, params=params, timeout=10)
    data = r.json()

    if "answer_box" in data:
        return data["answer_box"].get("answer") or data["answer_box"].get("snippet")

    if "organic_results" in data:
        return data["organic_results"][0].get("snippet")

    return None

# ================= START + COLOR GUIDE (FEATURE 3) =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERNAMES[user.id] = user.username or "NoUsername"

    context.user_data["awaiting_key"] = True

    await update.message.reply_text(
        "🤖 SYSTEM BOOTING...\n\n"
        "🔐 Paste your API key to activate AI core."
    )

# ================= COLOR GUIDE AFTER KEY =================
async def show_color_guide(update: Update):
    await update.message.reply_text(
        "🎨 AI INTELLIGENCE COLORS:\n\n"
        "🟢 Calm → Normal answer\n"
        "🟡 Thinking → Processing deeper meaning\n"
        "🔵 Focused → High confidence answer\n"
        "🟣 Curious → Exploring idea\n"
        "🟠 Smart Mode → Strong analytical response\n"
    )

# ================= DASHBOARD SEARCH (FEATURE 7) =================
async def find_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("admin"):
        return

    try:
        name = context.args[0]

        for uid, uname in USERNAMES.items():
            if uname == name:
                status = "🔴 BLOCKED" if uid in BLOCKED_USERS else "🟢 ACTIVE"
                await update.message.reply_text(
                    f"👤 {uname}\n🆔 {uid}\n📌 Status: {status}"
                )
                return

        await update.message.reply_text("❌ User not found.")
    except:
        await update.message.reply_text("⚠️ Usage: /find username")

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["admin_login"] = True
    await update.message.reply_text("🔐 Admin password:")

# ================= MAIN HANDLER =================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    text = update.message.text.lower()

    USERNAMES[uid] = user.username or "NoUsername"

    if uid in BLOCKED_USERS:
        return

    # ================= ADMIN LOGIN =================
    if context.user_data.get("admin_login"):
        if text == "iloveyou":
            context.user_data["admin"] = True
            await update.message.reply_text("👑 Admin unlocked.")
        else:
            await update.message.reply_text("❌ Wrong password.")
        context.user_data["admin_login"] = False
        return

    # ================= API KEY INPUT =================
    if context.user_data.get("awaiting_key"):
        USER_KEYS[uid] = text
        context.user_data["awaiting_key"] = False

        await update.message.reply_text("⚙️ Connecting AI core...")
        await show_color_guide(update)  # FEATURE 3

        return

    if uid not in USER_KEYS:
        await update.message.reply_text("⚠️ Send /start first.")
        return

    # ================= FUZZY + CONFIDENCE (FEATURE 2) =================
    mood = random.choice(MOODS)

    fuzzy_answer, confidence = fuzzy_match(text)

    if fuzzy_answer:
        await update.message.reply_text(
            f"{mood}\n\n📌 Answer: {fuzzy_answer}\n"
            f"📊 Confidence: {int(confidence * 100)}%\n\n💡 Related insight available."
        )
        return

    # ================= GOOGLE SEARCH =================
    try:
        result = search_google(text, USER_KEYS[uid])

        if result:
            confidence = random.choice([0.6, 0.7, 0.8, 0.9])

            await update.message.reply_text(
                f"{mood}\n\n📌 Answer: {result}\n"
                f"📊 Confidence: {int(confidence * 100)}%\n\n💡 Extra insight available."
            )
        else:
            await update.message.reply_text(
                f"{mood}\n\n🤔 No strong answer found."
            )

    except:
        await update.message.reply_text("⚠️ Error occurred.")

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("find", find_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

    print("🚀 Smart AI Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
