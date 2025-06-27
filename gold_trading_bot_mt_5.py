//+------------------------------------------------------------------+
//|                                                      GoldBot.mq5 |
//|                       Custom Expert Advisor for MT5             |
//+------------------------------------------------------------------+
#property strict

input double TradePercent = 80.0;         // % of account balance to use
input double SL_Percent = 2.8;            // Stop Loss %
input double TP_Percent = 1.8;            // Take Profit %
input double TrailingStart_Percent = 0.8; // Profit % to activate trailing
input string TradeSymbol = "XAUUSD";      // Symbol to trade

bool tradeOpen = false;
double lastPivot = 0.0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   if (PositionsTotal() > 0)
   {
      ManageTrailingStop();
      return; // Only one trade at a time
   }

   if (TimeCurrent() - TimeTradeServer() > 10)
      return; // Skip if delay

   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double tradeValue = balance * TradePercent / 100.0;
   double lotSize = CalculateLotSize(tradeValue);

   // Get last 4 candles (current + previous 3)
   MqlRates rates[4];
   if (CopyRates(TradeSymbol, PERIOD_CURRENT, 0, 4, rates) != 4)
      return;

   // Remove wicks (body only)
   double currentBody = MathAbs(rates[0].close - rates[0].open);
   double previousBody = MathAbs(rates[1].close - rates[1].open);

   bool bullish = (rates[0].close > rates[0].open);
   bool bearish = (rates[0].close < rates[0].open);

   // Strategy 1: Reversal with strong momentum
   if (currentBody > 2 * previousBody)
   {
      if (bullish)
         OpenTrade(ORDER_TYPE_BUY, lotSize, tradeValue);
      else if (bearish)
         OpenTrade(ORDER_TYPE_SELL, lotSize, tradeValue);
      lastPivot = rates[1].close;
      return;
   }

   // Strategy 2: Breakout after 2-3 candle continuation
   int breakoutCount = 0;
   for (int i = 1; i <= 3; i++)
   {
      double body = MathAbs(rates[i].close - rates[i].open);
      if ((rates[i].close > lastPivot && rates[i].open > lastPivot) ||
          (rates[i].close < lastPivot && rates[i].open < lastPivot))
      {
         breakoutCount++;
      }
      else break;
   }

   if (breakoutCount >= 2 && breakoutCount <= 3)
   {
      if (rates[0].close > lastPivot)
         OpenTrade(ORDER_TYPE_BUY, lotSize, tradeValue);
      else if (rates[0].close < lastPivot)
         OpenTrade(ORDER_TYPE_SELL, lotSize, tradeValue);
   }
}

//+------------------------------------------------------------------+
//| Open Trade Function                                              |
//+------------------------------------------------------------------+
void OpenTrade(int type, double lotSize, double tradeValue)
{
   double price = SymbolInfoDouble(TradeSymbol, (type == ORDER_TYPE_BUY) ? SYMBOL_ASK : SYMBOL_BID);
   double sl = SL_Percent / 100.0 * tradeValue / lotSize;
   double tp = TP_Percent / 100.0 * tradeValue / lotSize;
   double trailTrigger = TrailingStart_Percent / 100.0 * tradeValue / lotSize;

   double slPrice = (type == ORDER_TYPE_BUY) ? price - sl : price + sl;
   double tpPrice = (type == ORDER_TYPE_BUY) ? price + tp : price - tp;

   MqlTradeRequest request;
   MqlTradeResult result;
   ZeroMemory(request);
   ZeroMemory(result);

   request.action = TRADE_ACTION_DEAL;
   request.symbol = TradeSymbol;
   request.volume = lotSize;
   request.type = type;
   request.price = price;
   request.sl = NormalizeDouble(slPrice, _Digits);
   request.tp = NormalizeDouble(tpPrice, _Digits);
   request.deviation = 20;
   request.magic = 123456;
   request.type_filling = ORDER_FILLING_IOC;

   if (OrderSend(request, result))
   {
      Print("Trade opened successfully: ", result.order);
   }
   else
   {
      Print("Trade failed: ", result.retcode);
   }
}

//+------------------------------------------------------------------+
//| Lot Size Calculator (basic version)                              |
//+------------------------------------------------------------------+
double CalculateLotSize(double amount)
{
   double price = SymbolInfoDouble(TradeSymbol, SYMBOL_ASK);
   double lotStep = SymbolInfoDouble(TradeSymbol, SYMBOL_VOLUME_STEP);
   double minLot = SymbolInfoDouble(TradeSymbol, SYMBOL_VOLUME_MIN);
   double lot = amount / price / 100; // Simple approximation
   lot = MathFloor(lot / lotStep) * lotStep;
   if (lot < minLot)
      lot = minLot;
   return NormalizeDouble(lot, 2);
}

//+------------------------------------------------------------------+
//| Trailing Stop Logic                                              |
//+------------------------------------------------------------------+
void ManageTrailingStop()
{
   for (int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if (PositionGetInteger(POSITION_MAGIC) != 123456)
         continue;

      string sym = PositionGetString(POSITION_SYMBOL);
      double openPrice = PositionGetDouble(POSITION_PRICE_OPEN);
      double volume = PositionGetDouble(POSITION_VOLUME);
      double profit = PositionGetDouble(POSITION_PROFIT);
      int type = (int)PositionGetInteger(POSITION_TYPE);

      double trailTrigger = TrailingStart_Percent / 100.0 * AccountInfoDouble(ACCOUNT_BALANCE) * TradePercent / 100.0 / volume;
      double currentPrice = (type == POSITION_TYPE_BUY) ? SymbolInfoDouble(sym, SYMBOL_BID) : SymbolInfoDouble(sym, SYMBOL_ASK);
      double trailSL = (type == POSITION_TYPE_BUY) ? currentPrice - trailTrigger : currentPrice + trailTrigger;

      if (((type == POSITION_TYPE_BUY) && (currentPrice - openPrice >= trailTrigger)) ||
          ((type == POSITION_TYPE_SELL) && (openPrice - currentPrice >= trailTrigger)))
      {
         MqlTradeRequest request;
         MqlTradeResult result;
         ZeroMemory(request);
         ZeroMemory(result);

         request.action = TRADE_ACTION_SLTP;
         request.symbol = sym;
         request.sl = NormalizeDouble(trailSL, _Digits);
         request.tp = 0.0; // remove TP
         request.position = ticket;
         request.magic = 123456;

         OrderSend(request, result);
         Print("Trailing stop adjusted: ", result.retcode);
      }
   }
}
//+------------------------------------------------------------------+
