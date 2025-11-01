import pandas as pd
import sqlite3
import os

# --- CONFIGURATION ---
USE_SAMPLE = True
SAMPLE_SIZE = 100000

# --- FILE PATHS ---
DATA_FILE = os.path.join('data', 'fraud_dataset.csv')
DB_FILE = 'fraud_dw.db'


def build_data_warehouse():
    """
    Extracts data from the CSV, transforms it into a star schema,
    and loads it into a SQLite database.
    """
    
    # --- 1. EXTRACT ---
    print(f"Loading raw data from {DATA_FILE}...")
    try:
        if USE_SAMPLE:
            print(f"Using a sample of {SAMPLE_SIZE} rows for development.")
            df = pd.read_csv(DATA_FILE, nrows=SAMPLE_SIZE)
        else:
            print("Loading full dataset... (this may take a few minutes)")
            df = pd.read_csv(DATA_FILE)
        print("Raw data loaded successfully.")
    except FileNotFoundError:
        print(f"ERROR: Data file not found at {DATA_FILE}")
        print("Please make sure you downloaded the dataset and named it 'fraud_dataset.csv' inside the 'data' folder.")
        return

    # --- 2. TRANSFORM ---
    
    # Create 'Dim_Account'
    print("Transforming data: Creating 'Dim_Account'...")
    senders = df['nameOrig'].unique()
    receivers = df['nameDest'].unique()
    all_accounts = set(senders) | set(receivers)
    
    dim_account = pd.DataFrame(all_accounts, columns=['Account_ID'])
    dim_account.reset_index(inplace=True)
    dim_account = dim_account.rename(columns={'index': 'Account_Key'})
    print(f"Created {len(dim_account)} unique accounts.")

    # Create 'Dim_Time'
    print("Transforming data: Creating 'Dim_Time'...")
    df['Hour_of_Day'] = df['step'] % 24
    
    dim_time_data = df[['step', 'Hour_of_Day']].drop_duplicates()
    dim_time = dim_time_data.reset_index(drop=True)
    dim_time.reset_index(inplace=True)
    dim_time = dim_time.rename(columns={'index': 'Time_Key'})
    print(f"Created {len(dim_time)} unique time entries.")

    # Create 'Fact_Transaction'
    print("Transforming data: Creating 'Fact_Transaction'...")
    
    df_fact = df.merge(dim_time, on=['step', 'Hour_of_Day'], how='left')
    df_fact = df_fact.merge(dim_account, left_on='nameOrig', right_on='Account_ID', how='left')
    df_fact = df_fact.rename(columns={'Account_Key': 'Sender_Account_Key'})
    df_fact = df_fact.merge(dim_account, left_on='nameDest', right_on='Account_ID', how='left')
    df_fact = df_fact.rename(columns={'Account_Key': 'Receiver_Account_Key'})
    
    fact_columns = [
        'Time_Key',
        'Sender_Account_Key',
        'Receiver_Account_Key',
        'type',
        'amount',
        'oldbalanceOrg',
        'newbalanceOrig',
        'oldbalanceDest',
        'newbalanceDest',
        'isFraud'
    ]
    
    fact_transaction = df_fact[fact_columns]
    
    fact_transaction.reset_index(inplace=True)
    fact_transaction = fact_transaction.rename(columns={'index': 'Transaction_ID'})
    
    print(f"Created {len(fact_transaction)} entries for the fact table.")

    # --- 3. LOAD ---
    print(f"Loading data into warehouse: {DB_FILE}...")
    
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Removed old database file.")
        
    conn = sqlite3.connect(DB_FILE)
    
    try:
        dim_account.to_sql('Dim_Account', conn, index=False)
        dim_time.to_sql('Dim_Time', conn, index=False)
        fact_transaction.to_sql('Fact_Transaction', conn, index=False)
        print("Successfully loaded all tables into the database.")
    except Exception as e:
        print(f"Error loading data into SQL: {e}")
    finally:
        conn.close()

    print("\n--- ETL process complete! ---")
    print(f"Your Data Warehouse '{DB_FILE}' is ready.")


if __name__ == "__main__":
    build_data_warehouse()