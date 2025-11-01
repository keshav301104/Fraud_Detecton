import pandas as pd
import sqlite3
import joblib
from flask import Flask, render_template, request, jsonify
import os
import json

# --- CONFIGURATION ---
DB_FILE = 'fraud_dw.db'
MODEL_FILE = 'model.joblib'
ANALYTICS_TABLE = 'analytics_base_table.csv'
STATS_FILE = 'global_stats.json'

# --- LOAD THE MODEL ---
print(f"Loading model from {MODEL_FILE}...")
try:
    pipeline = joblib.load(MODEL_FILE)
    print("Model loaded successfully.")
except FileNotFoundError:
    print(f"ERROR: Model file not found at {MODEL_FILE}")
    print("Please run '2_model_training.py' first.")
    exit()

# --- LOAD THE FEATURE DATA ---
print(f"Loading analytics data from {ANALYTICS_TABLE}...")
df_analytics = None 
SENDER_IDS = [] 
try:
    df_analytics = pd.read_csv(ANALYTICS_TABLE).set_index('Sender_ID')
    df_analytics.fillna(0, inplace=True)
    SENDER_IDS = list(df_analytics.index.unique())
    print("Analytics data loaded successfully.")
except Exception as e:
    print(f"Error loading {ANALYTICS_TABLE}: {e}")
    print("Please RE-RUN '2a_advanced_features.py' and then restart this app.")
    exit() 


# --- INITIALIZE FLASK APP ---
app = Flask(__name__)

# --- DEFINE ROUTES ---

@app.route('/')
def home():
    """Renders the main HTML page."""
    return render_template('index.html', sender_ids=SENDER_IDS[:1000])

@app.route('/get-recent-transactions')
def get_recent_transactions():
    """Gets the last 20 transactions from the DB to display in the table."""
    conn = sqlite3.connect(DB_FILE)
    try:
        query = """
        SELECT T.Transaction_ID, T.type, T.amount, 
               A_sender.Account_ID AS Sender_ID, 
               A_receiver.Account_ID AS Receiver_ID,
               T.isFraud
        FROM Fact_Transaction T
        JOIN Dim_Account A_sender ON T.Sender_Account_Key = A_sender.Account_Key
        JOIN Dim_Account A_receiver ON T.Receiver_Account_Key = A_receiver.Account_Key
        ORDER BY T.Transaction_ID DESC
        LIMIT 20
        """
        df = pd.read_sql_query(query, conn)
        return jsonify(df.to_dict(orient='records'))
    except Exception as e:
        print(f"Error querying database: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/predict-fraud', methods=['POST'])
def predict_fraud():
    """Receives data from the form and returns a fraud prediction."""
    try:
        data = request.json
        print(f"Received data for prediction: {data}")
        
        sender_id = data['sender_id']
        receiver_id = data['receiver_id'] # Note: receiver_id is no longer used
        amount = float(data['amount'])
        tx_type = data['type'].upper()

        try:
            sender_features = df_analytics.loc[sender_id]
            if isinstance(sender_features, pd.DataFrame):
                sender_features = sender_features.iloc[0]
                
        except KeyError:
            # This is a new sender not in our training data
            sender_features = pd.Series({
                'sender_tx_count': 1, 
                'sender_avg_amount': amount
            })
            print(f"Warning: New sender '{sender_id}'. Using default features.")

        # This is the new, cleaner feature list
        input_data = {
            'amount': amount, 
            'type': tx_type,
            'sender_tx_count': sender_features['sender_tx_count'],
            'sender_avg_amount': sender_features['sender_avg_amount'],
            'amount_vs_avg': amount / (sender_features['sender_avg_amount'] + 1)
        }
        
        df_predict = pd.DataFrame([input_data])
        
        df_predict_encoded = pipeline['preprocessor'].transform(df_predict)
        prediction = pipeline['model'].predict(df_predict_encoded)
        probabilities = pipeline['model'].predict_proba(df_predict_encoded)
        
        is_fraud = int(prediction[0])
        risk_score = float(probabilities[0][1]) 

        print(f"Prediction: {is_fraud}, Risk Score: {risk_score}")
        return jsonify({ 'is_fraud': is_fraud, 'risk_score': risk_score })

    except Exception as e:
        print(f"Error during prediction: {e}")
        return jsonify({"error": str(e)}), 500

# --- API ENDPOINT FOR GLOBAL STATS ---
@app.route('/get-global-stats')
def get_global_stats():
    """Loads and returns the pre-calculated global stats from the JSON file."""
    try:
        with open(STATS_FILE, 'r') as f:
            stats = json.load(f)
        return jsonify(stats)
    except FileNotFoundError:
        print(f"ERROR: {STATS_FILE} not found. Please run 3_global_stats.py")
        return jsonify({"error": f"{STATS_FILE} not found. Please run 3_global_stats.py"}), 500
    except Exception as e:
        print(f"Error reading stats file: {e}")
        return jsonify({"error": str(e)}), 500


# --- RUN THE APP ---
if __name__ == "__main__":
    print("Starting Flask server... Go to http://127.0.0.1:5000")
    app.run(debug=True)