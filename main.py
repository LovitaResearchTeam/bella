from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

import pandas as pd

from settings import TELEGRAM_TOKEN


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pass


async def rarity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        df = pd.read_csv('rarity.csv')
        df.sort_values("total", inplace=True)
        msg = "Rarest Ninjas: \n\n"
        for i, row in enumerate(df[:10], start=1):
            msg += f"{i}. Ninja #{row['number']} : {round(row['total'], 2)}%"
        await update.message.reply_text(msg)
        return
    # else
    if len(args) > 1:
        await update.message.reply_text("You should pass one argument : Ninja number")
        return
    # else
    try:
        number = int(args[0])
        df = pd.read_csv('rarity.csv')
        filtered_df = df[df['number'] == number]
        if not len(filtered_df):
            await update.message.reply_text("Ninja number not found. Try another number: ")
            return
        # else
        row = filtered_df.iloc[0]

    except TypeError:
        await update.message.reply_text("Ninja number not valid. Try again.")
        return




if __name__ == "__main__":
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start_cmd))
    app.add_handler(CommandHandler('rarity', rarity_cmd))

    app.run_polling()