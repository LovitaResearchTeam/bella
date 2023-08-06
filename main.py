from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, PraseMode

import pandas as pd

import consts
from settings import TELEGRAM_TOKEN


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def rarity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        rarity_df = pd.read_csv('rarity.csv')
        rarity_df.sort_values("total", inplace=True)
        msg = "Rarest Ninjas: \n\n"
        for i in range(10):
            row = rarity_df.iloc[i]
            msg += f"{i+1}. Ninja #{row['number']} : {round(row['total'], 2)}%\n\n"
        await update.message.reply_text(msg)
        return
    # else
    if len(args) > 1:
        await update.message.reply_text("You should pass one argument : Ninja number")
        return
    # else
    try:
        number = int(args[0])
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
            await update.message.reply_photo(f, caption, parse_mode=PraseMode.MARKDOWN)

    except TypeError:
        await update.message.reply_text("Ninja number not valid. Try again.")
        return




if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start_cmd))
    app.add_handler(CommandHandler('rarity', rarity_cmd))

    app.run_polling()