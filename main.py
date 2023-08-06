from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.constants import ParseMode

import pandas as pd

import consts
from settings import TELEGRAM_TOKEN


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Hi. I'm bella. I can show you how much an NFT is rare.\n\n"
    msg += "Right now Ninja collection is supported. You can find rarity of a ninja NFT by sending command like below: \n\n"
    msg += "`/rarityNinja <ninja number or custom title>`\n\n"
    msg += "Where number is the number of Ninja NFT."
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)



async def rarity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        msg = "Hey SER. To use this bot you need to call this command like below:\n\n"
        msg += "'/rarityNinja <ninja number or custom title>`"
        await update.message.reply_text(msg)
        return
    # else
    # if len(args) > 1:
    #     await update.message.reply_text("You should pass one argument : Ninja number")
    #     return
    # else
    try:
        int(args[0])
        number = args[0]
        rarity_df = pd.read_csv('rarity.csv')
        filtered_df = rarity_df[rarity_df['number'] == number]
        if not len(filtered_df):
            await update.message.reply_text("Ninja number not found. Try another number: ")
            return
        # else
        row = filtered_df.iloc[0]
        with open(f"media/#{number}.jpg", 'rb') as f:
            caption = f"*Ninja #{number}\n\n*"
            caption += f"*Total rank*: {int(row['rank_total'])}\n\n"
            for col in consts.RARE_COLS:
                caption += f"*{col.capitalize()}*\n{row[col]} : {round(row[f'rarity_{col}'], 2)}% (rank={int(row[f'rank_{col}'])})\n\n"
            await update.message.reply_photo(f, caption, parse_mode=ParseMode.MARKDOWN)

    except ValueError:
        title = " ".join(args)
        rarity_df = pd.read_csv('rarity.csv')
        filtered_df = rarity_df[rarity_df['number'] == title]
        if not len(filtered_df):
            await update.message.reply_text("Ninja title not found. Try another title:")
            return
        row = filtered_df.iloc[0]
        with open(f"media/#{title}.jpg", 'rb') as f:
            caption = f"*{title}\n\n*"
            caption += f"*Total rank*: {int(row['rank_total'])}\n\n"
            for col in consts.RARE_COLS:
                caption += f"*{col.capitalize()}*\n{row[col]} : {round(row[f'rarity_{col}'], 2)}% (rank={int(row[f'rank_{col}'])})\n\n"
            await update.message.reply_photo(f, caption, parse_mode=ParseMode.MARKDOWN)


if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start_cmd))
    app.add_handler(CommandHandler('rarityNinja', rarity_cmd))

    app.run_polling()