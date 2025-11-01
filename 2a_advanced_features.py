import pandas as pd
import sqlite3
import os
import networkx as nx

DB_FILE = 'fraud_dw.db'
OUTPUT_FILE = 'analytics_base_table.csv'

def create_advanced_features():
    """
    Loads data from DW, engineers behavioral features,
    and saves them to a new CSV file for model training.
    """
    
    # --- 1. LOAD DATA ---
    print(f"Loading data from Data Warehouse: {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
        SELECT T.*, 
               A_sender.Account_ID AS Sender_ID, 
               A_receiver.Account_ID AS Receiver_ID
        FROM Fact_Transaction T
        JOIN Dim_Account A_sender ON T.Sender_Account_Key = A_sender.Account_Key
        JOIN Dim_Account A_receiver ON T.Receiver_Account_Key = A_receiver.Account_Key
        """
        df = pd.read_sql_query(query, conn)
        print(f"Successfully loaded {len(df)} transactions.")
    except Exception as e:
        print(f"Error loading data: {e}")
        return
    finally:
        conn.close()

    # --- 2. PERSONALIZED (BEHAVIORAL) FEATURES ---
    print("Engineering personalized behavioral features...")
    
    sender_counts = df['Sender_ID'].value_counts()
    df['sender_tx_count'] = df['Sender_ID'].map(sender_counts)

    sender_avg_amount = df.groupby('Sender_ID')['amount'].mean()
    df['sender_avg_amount'] = df['Sender_ID'].map(sender_avg_amount)
    
    df['amount_vs_avg'] = df['amount'] / (df['sender_avg_amount'] + 1)
    
    # --- 3. REMOVED GRAPH FEATURES ---
    print("Graph features (PageRank) have been removed for a more robust model.")
    
    # --- 4. PREPARE FINAL TABLE ---
    print("Preparing final analytics table...")
    
    # This is the new, cleaner feature list
    final_features = [
        'Sender_ID', 
        'amount',
        'type',
        'sender_tx_count',
        'sender_avg_amount',
        'amount_vs_avg',
        'isFraud' # Keep the target column
    ]
    
    df_final = df[final_features].copy()
    
    df_final.fillna(0, inplace=True)
    
    # --- 5. SAVE ---
    df_final.to_csv(OUTPUT_FILE, index=False)
    print(f"\n--- Advanced Feature Engineering Complete! ---")
    print(f"Master analytics table saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    create_advanced_features()