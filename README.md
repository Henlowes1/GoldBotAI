# GoldBotAI

This bot connects an AI signal generator in Python to a MetaTrader 5 EA trading Gold CFDs on XAUUSD via Pepperstone.

## Components

- `train_ai_model.py`: Trains an ML model from historical candle data
- `ai_signal_provider.py`: Predicts trade signals using the trained model
- `GoldBot.mq5`: The MT5 Expert Advisor (you place this in `MQL5/Experts`)

## Setup

1. Install required Python packages:
   ```bash
   pip install pandas MetaTrader5 scikit-learn joblib
