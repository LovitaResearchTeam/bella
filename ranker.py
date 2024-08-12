import pandas as pd
import numpy as np

# Load the CSV file into a DataFrame
df = pd.read_csv('metadatas.csv')

# Initialize a DataFrame to store the log probabilities
log_prob_df = pd.DataFrame()
df.fillna("Nan", inplace=True)
# Calculate the log probability for each feature in each column
for column in df.columns:
    # Skip non-feature columns (like 'media', 'tags' etc.)
    if df[column].dtype == 'object':
        # Calculate the probability of each feature
        value_counts = df[column].value_counts(normalize=True)
        
        # Calculate the log probability of each feature
        log_probs = df[column].map(lambda x: np.log(value_counts[x]))
        
        # Store the log probabilities in the new DataFrame
        log_prob_df[column] = log_probs

# Calculate the rarity score as the negative sum of log probabilities across all columns
df['rarity_score'] = -log_prob_df.sum(axis=1)

# Sort the DataFrame by rarity score in descending order to rank the NFTs
df['rarity_rank'] = df['rarity_score'].rank(ascending=False, method='dense')

# Sort the DataFrame by the rarity rank
df = df.sort_values('rarity_rank')

# Save the updated DataFrame to a new CSV file
df.to_csv('csvs/new_metadatas_with_rarity.csv', index=False)