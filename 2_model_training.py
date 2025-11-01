import pandas as pd
import sqlite3
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from xgboost import XGBClassifier

# --- FILE PATHS ---
DATA_FILE = 'analytics_base_table.csv' 
MODEL_FILE = 'model.joblib'

def train_model():
    """
    Loads data from the advanced features table, trains an XGBoost model,
    and saves it.
    """
    
    # --- 1. LOAD DATA ---
    print(f"Loading data from Analytics Base Table: {DATA_FILE}...")
    if not os.path.exists(DATA_FILE):
        print(f"ERROR: Analytics file not found at {DATA_FILE}")
        print("Please run '2a_advanced_features.py' first to create it.")
        return

    try:
        df = pd.read_csv(DATA_FILE)
        print(f"Successfully loaded {len(df)} pre-processed transactions.")
    except Exception as e:
        print(f"Error loading data from CSV: {e}")
        return
    
    # --- 2. FEATURE ENGINEERING (DATA MINING) ---
    print("Starting feature engineering...")
    
    # This is the new, cleaner feature list
    features = [
        'amount',
        'type', 
        'sender_tx_count',
        'sender_avg_amount',
        'amount_vs_avg'
    ]
    
    target = 'isFraud'
    
    X = df[features]
    y = df[target]
    
    X = X.fillna(0)
    
    categorical_features = ['type']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
        ],
        remainder='passthrough'
    )

    print("Data defined. Splitting into train and test sets...")
    # --- 3. SPLIT DATA ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    X_train_encoded = preprocessor.fit_transform(X_train)
    X_test_encoded = preprocessor.transform(X_test)
    
    print(f"Original training data shape: {X_train_encoded.shape}")

    # --- 4. HANDLE IMBALANCED DATA ---
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
    print(f"Calculated scale_pos_weight for imbalance: {scale_pos_weight:.2f}")

    # --- 5. TRAIN MODEL (XGBOOST) ---
    print("Training the XGBClassifier...")
    
    model = XGBClassifier(
        random_state=42,
        n_jobs=-1,
        scale_pos_weight=scale_pos_weight,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train_encoded, y_train)
    print("Model training complete.")

    # --- 6. EVALUATE MODEL ---
    print("Evaluating model on the (unseen) test set...")
    y_pred = model.predict(X_test_encoded)
    
    print("\n--- Classification Report (XGBoost) ---")
    print(classification_report(y_test, y_pred, target_names=['Not Fraud (0)', 'Fraud (1)']))
    
    print("\n--- Confusion Matrix (XGBoost) ---")
    print(confusion_matrix(y_test, y_pred))
    
    # --- 7. SAVE MODEL ---
    print(f"\nSaving model to {MODEL_FILE}...")
    pipeline = {
        'preprocessor': preprocessor,
        'model': model
    }
    joblib.dump(pipeline, MODEL_FILE)
    
    print("\n--- Model training process complete! ---")
    print(f"Your trained XGBoost model is saved as '{MODEL_FILE}'.")


if __name__ == "__main__":
    train_model()