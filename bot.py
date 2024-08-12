import logging
import os
import requests
import argparse
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import pandas as pd

# Set up argument parser to get the API token from the terminal
parser = argparse.ArgumentParser(description="Telegram bot for NFT rarity lookup.")
parser.add_argument('api_token', type=str, help="Your Telegram bot's API token.")
args = parser.parse_args()

# Use the API token passed as a terminal argument
API_TOKEN = args.api_token

# Set up logging to help with debugging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load all CSV files in the specified directory
folder_path = '/home/ubuntu/inj_test/bella/csvs'
csv_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('_metadatas_with_rarity.csv')]

# Load each CSV into a list of DataFrames
dataframes = [pd.read_csv(csv_file) for csv_file in csv_files]

def get_rarity(dataframes, name):
    """
    Searches for the given name across all DataFrames and returns all columns
    for the matching NFT in a header-agnostic format.

    Parameters:
    dataframes (list of pd.DataFrame): List of DataFrames containing NFT data, including 'rarity_score' and 'rarity_rank'.
    name (str): The name to search for (case insensitive).

    Returns:
    dict: A dictionary containing all the columns for the matching NFT, otherwise None.
    """
    name_lower = name.lower()
    
    for df in dataframes:
        for index, row in df.iterrows():
            if any(name_lower == str(value).lower() for value in row):
                return row.to_dict()
    
    return None

def get_ipfs_from_address(ipfs_address: str) -> str:
    """Convert an IPFS address to an HTTP address."""
    return ipfs_address.replace("ipfs://", "https://ipfs.io/ipfs/")

def get_media_url(row) -> str:
    """
    Extract the media URL from the row if it contains an image or video URL.
    
    Parameters:
    row (pd.Series): A row from the DataFrame.

    Returns:
    str: The URL to the media file, or None if no valid media is found.
    """
    for value in row:
        value_str = str(row[value])
        if any(value_str.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']):
            return get_ipfs_from_address(value_str)
    return None

async def rarity_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /rarity command. Calls the get_rarity function and sends the result back to the user with the media attached.
    """
    # Get the search term from the command
    if len(context.args) > 0:
        search_term = ' '.join(context.args)
        rarity_info = get_rarity(dataframes, search_term)
        
        if rarity_info:
            response = f"Information for '{search_term}':\n"
            for key, value in rarity_info.items():
                if key.lower() not in ['tags', 'media', 'rarity_score', 'rarity_rank']:
                    response += f"{key}: {value}\n"
                elif key.lower() == 'rarity_rank':
                    response += f"{key}: {int(value)}\n"
            
            # Attempt to retrieve the media URL
            media_url = get_media_url(rarity_info)
            if media_url:
                media_response = requests.get(media_url)
                if media_response.status_code == 200:
                    # Convert image to JPG format and save it
                    image = Image.open(BytesIO(media_response.content))
                    jpg_file_path = 'temp_media_file.jpg'
                    image = image.convert("RGB")  # Ensure the image is in RGB mode
                    image.save(jpg_file_path, format='JPEG')
                    with open(jpg_file_path, 'rb') as ph:
                        # Send the NFT information
                        await update.message.reply_photo(photo=ph, caption=response)
                    
                    # Remove the temporary media file
                    os.remove(jpg_file_path)
                else:
                    await update.message.reply_text(f"Media not found, but here is the info:\n{response}")
            else:
                await update.message.reply_text(f"No valid media found, but here is the info:\n{response}")
        else:
            response = f"No match found for '{search_term}'."
            await update.message.reply_text(response)
    else:
        response = "Please provide a name to search for after the /rarity command."
        await update.message.reply_text(response)

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token
    application = Application.builder().token(API_TOKEN).build()

    # Register the /rarity command handler
    application.add_handler(CommandHandler("rarity", rarity_command))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
