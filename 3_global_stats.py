import pandas as pd
import json
import os

# --- FILE PATHS ---
DATA_FILE = os.path.join('data', 'fraud_dataset.csv')
OUTPUT_FILE = 'global_stats.json'

def calculate_global_stats():
    """
    Reads the ENTIRE, original CSV to calculate global stats for the dashboard.
    This only needs to be run once.
    """
    print(f"Loading full dataset from {DATA_FILE}...")
    try:
        # Load the full dataset (this will use more memory and time)
        df = pd.read_csv(DATA_FILE)
    except FileNotFoundError:
        print(f"ERROR: Full data file not found at {DATA_FILE}")
        return
    
    print("Calculating stats...")

    # --- KPIs ---
    total_transactions = int(len(df))
    total_volume = float(df['amount'].sum())
    total_fraud_count = int(df['isFraud'].sum())
    fraud_rate = (total_fraud_count / total_transactions) * 100

    # --- Chart 1: Transaction Types ---
    type_stats = df['type'].value_counts()
    type_chart_data = {
        'labels': type_stats.index.tolist(),
        'data': type_stats.values.tolist()
    }

    # --- Chart 2: Fraud vs. Safe ---
    fraud_stats = df['isFraud'].value_counts()
    fraud_chart_data = {
        'labels': ['Safe Transactions', 'Fraud Transactions'],
        # Ensure we handle the case where one key might be missing
        'data': [int(fraud_stats.get(0, 0)), int(fraud_stats.get(1, 0))]
    }

    # --- Compile all stats into one object ---
    final_stats = {
        'kpis': {
            'total_transactions': total_transactions,
            'total_volume': total_volume,
            'total_fraud': total_fraud_count,
            'fraud_rate': fraud_rate
        },
        'charts': {
            'type_chart': type_chart_data,
            'fraud_chart': fraud_chart_data
        }
    }

    # --- Save to JSON file ---
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_stats, f, indent=4)

    print("\n--- Global Stats Calculation Complete! ---")
    print(f"Stats saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    calculate_global_stats()