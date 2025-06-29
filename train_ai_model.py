
import pandas as pd
import MetaTrader5 as mt5
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

SYMBOL = "XAUUSD_SB"
TIMEFRAME = mt5.TIMEFRAME_M5
CANDLES = 1000

def fetch_data():
    if not mt5.initialize():
        raise RuntimeError("MT5 init failed")
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, CANDLES)
    mt5.shutdown()
    df = pd.DataFrame(rates)
    df['body'] = df['close'] - df['open']
    df['direction'] = df['body'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return df

def prepare_data(df):
    df['prev_body'] = df['body'].shift(1)
    df['prev2_body'] = df['body'].shift(2)
    df['label'] = df['direction'].shift(-1).map({1: 'BUY', -1: 'SELL'}).fillna('NONE')
    df = df.dropna()
    X = df[['body', 'prev_body', 'prev2_body']]
    y = df['label']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return train_test_split(X_scaled, y, test_size=0.2), scaler

def train():
    df = fetch_data()
    (X_train, X_test, y_train, y_test), scaler = prepare_data(df)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print("Accuracy:", model.score(X_test, y_test))
    joblib.dump(model, 'ai_model.pkl')
    joblib.dump(scaler, 'scaler.pkl')

if __name__ == "__main__":
    train()
