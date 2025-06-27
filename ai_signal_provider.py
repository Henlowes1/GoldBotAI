
import MetaTrader5 as mt5
import pandas as pd
import joblib

model = joblib.load("ai_model.pkl")
scaler = joblib.load("scaler.pkl")

def get_features():
    mt5.initialize()
    rates = mt5.copy_rates_from_pos("XAUUSD", mt5.TIMEFRAME_M5, 0, 3)
    mt5.shutdown()
    df = pd.DataFrame(rates)
    df['body'] = df['close'] - df['open']
    features = df['body'].values[::-1][:3]
    return scaler.transform([features])

def write_signal(signal):
    with open("signal.txt", "w") as f:
        f.write(signal)

if __name__ == "__main__":
    X = get_features()
    pred = model.predict(X)[0]
    write_signal(pred)
    print("Predicted signal:", pred)
