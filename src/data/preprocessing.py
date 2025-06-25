import pandas as pd
import os


def load_raw_data(filepath):
    """Load raw data from a CSV file."""
    return pd.read_csv(filepath)


def clean_data(df):
    """Perform basic data cleaning on the DataFrame."""
    # Example: drop rows with missing values
    df = df.dropna()
    # Add more cleaning steps as needed
    return df


def save_processed_data(df, filepath):
    """Save the cleaned DataFrame to a CSV file."""
    df.to_csv(filepath, index=False)


# Example usage
if __name__ == "__main__":
    raw_path = os.path.join("data", "raw", "zomato_restaurants.csv")
    processed_path = os.path.join("data", "processed", "zomato_restaurants_cleaned.csv")
    df = load_raw_data(raw_path)
    df_clean = clean_data(df)
    save_processed_data(df_clean, processed_path)
