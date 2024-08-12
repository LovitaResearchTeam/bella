# Bella Telegram Bot

Bella is a Telegram bot designed to compute and display the rarity of an NFT within its collection.

**Default Collections:**  
The Ninjas Collection
Cult of Anons Collection

## Usage

To interact with the bot, visit the following address: [Bella Ninja Bot](https://t.me/bellaninjabot).

## Fetching Data

### Collecting Information for New NFT Collections

To gather information for a new NFT collection, you can use the `contract_crawler.py` script. This script requires the minter and collection addresses as arguments. 

For example, to collect data for "The Ninjas" collection, you would use:

```bash
python contract_crawler.py inj1rlyp66l2macpfqer2tg57a6alvgv7ydvrlfwrh inj19ly43dgrr2vce8h02a8nw0qujwhrzm9yv8d75c
```

### Fetching Rarity Data

Once the collection data has been gathered, you can use the `ranker.py` script to calculate the rarity rankings:

```bash
python ranker.py
```

### Running the Bot

To start the bot, use the `bot.py` script. You need to provide your API token as an argument:

```bash
python bot.py <api_token>
```

## Contribution

We welcome and appreciate any contributions to our project, whether it’s reporting bugs, suggesting features, writing code, or anything else that can improve our project.

If you want to contribute to our project, please follow these steps:

1. **Fork** the repository and **clone** it to your local machine.
2. **Create a new branch** for your changes and ensure it is up to date with the main branch.
3. **Make your changes** and commit them with clear and descriptive messages.
4. **Push your changes** to your forked repository and create a **pull request** to the main branch.
5. **Wait for review** by the maintainers and for your pull request to be merged.

Thank you for your interest and support in our project! We are grateful for every contribution, no matter how big or small. 😊