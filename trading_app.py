import streamlit as st
import pandas as pd
import os
import ta
from datetime import datetime, timedelta
from kiteconnect import KiteConnect
import pytz # Import pytz for timezone handling
import numpy as np

# --- Zerodha Kite Connect API Configuration ---
# It's recommended to handle API keys securely, e.g., via Streamlit secrets.
# For this example, they are hardcoded as in your original script.
API_KEY = "d44i0hr892a4lpsc"
ACCESS_TOKEN = "rotkBsDho469YMju3f85qGdJubsV7FXZ"

# Initialize KiteConnect (once per session if possible, or handle re-initialization)
@st.cache_resource
def get_kite_instance():
    try:
        kite = KiteConnect(api_key=API_KEY)
        kite.set_access_token(ACCESS_TOKEN)
        st.success("KiteConnect initialized successfully.")
        return kite
    except Exception as e:
        st.error(f"Error initializing KiteConnect: {e}")
        st.stop() # Stop the app if KiteConnect fails
        return None

kite = get_kite_instance()

# Stock symbol mapping (Expanded list from previous conversation)
STOCKS_TO_DOWNLOAD = {
    "Indian Hotels Company Limited": "INDHOTEL",
    "Union Bank of India": "UNIONBANK",
    "Canara Bank": "CANBK",
    "Yes Bank": "YESBANK",
    "SKF India Ltd": "SKFIND",
    "Bharat Forge Ltd": "BHARATFORG",
    "Ola Electric": None,
    "Protean eGov Technologies Ltd": "PROTEAN",
    "Asian Paints Ltd": "ASIANPAINT",
    "Venky's India Ltd": "VENKEYS",
    "TTK Prestige Ltd": "TTKPRESTIG",
    "Ksolves India Ltd": "KSOLVES",
    "Jio fin": "JIOFIN",
    "Delhivery": "DELHIVERY",
    "Cello World": "CELLO",
    "Bharath Bijlee": "BBL",
    "BASF": "BASF",
    "Kirloskar Industries": "KIRLOSIND",
    "Pidilite Industries": "PIDILITIND",
    "Crompton Greaves Consumer": "CROMPTON",
    "Deepak Nitrite": "DEEPAKNTR",
    "Astral Ltd": "ASTRAL",
    "Aarti Industries": "AARTIIND",
    "Kajaria Ceramics": "KAJARIACER",
    "Voltas Ltd": "VOLTAS",
    "Trent Ltd": "TRENT",
    "Blue Star Ltd": "BLUESTARCO",
    "Thermax Ltd": "THERMAX",
    # --- ADDITIONAL STOCKS ADDED BELOW ---
    "Reliance Industries Ltd": "RELIANCE",
    "HDFC Bank Ltd": "HDFCBANK",
    "ICICI Bank Ltd": "ICICIBANK",
    "State Bank of India": "SBIN",
    "Infosys Ltd": "INFY",
    "Tata Consultancy Services Ltd": "TCS",
    "Maruti Suzuki India Ltd": "MARUTI",
    "Tata Motors Ltd": "TATAMOTORS",
    "Larsen & Toubro Ltd": "LT",
    "Axis Bank Ltd": "AXISBANK",
    "Kotak Mahindra Bank Ltd": "KOTAKBANK",
    "Hindustan Unilever Ltd": "HINDUNILVR",
    "ITC Ltd": "ITC",
    "Bajaj Finance Ltd": "BAJFINANCE",
    "Titan Company Ltd": "TITAN",
    "Nestle India Ltd": "NESTLEIND",
    "Dabur India Ltd": "DABUR",
    "IndusInd Bank Ltd": "INDUSINDBK",
    "Wipro Ltd": "WIPRO",
    "Tech Mahindra Ltd": "TECHM",
    "Power Grid Corporation of India Ltd": "POWERGRID",
    "NTPC Ltd": "NTPC",
    "Adani Ports and Special Economic Zone Ltd": "ADANIPORTS",
    "Adani Enterprises Ltd": "ADANIENT",
    "Bharat Petroleum Corporation Ltd": "BPCL",
    "Indian Oil Corporation Ltd": "IOC",
    "Coal India Ltd": "COALINDIA",
    "Steel Authority of India Ltd": "SAIL",
    "JSW Steel Ltd": "JSWSTEEL",
    "Tata Steel Ltd": "TATASTEEL",
    "Sun Pharmaceutical Industries Ltd": "SUNPHARMA",
    "Dr. Reddy's Laboratories Ltd": "DRREDDY",
    "Cipla Ltd": "CIPLA",
    "Apollo Hospitals Enterprise Ltd": "APOLLOHOSP",
    "Max Healthcare Institute Ltd": "MAXHEALTH",
    "Siemens Ltd": "SIEMENS",
    "ABB India Ltd": "ABB",
    "Honeywell Automation India Ltd": "HONAUT",
    "Tata Consumer Products Ltd": "TATACONSUM",
    "Britannia Industries Ltd": "BRITANNIA",
    "United Breweries Ltd": "UBL",
    "Page Industries Ltd": "PAGEIND",
    "Dixon Technologies (India) Ltd": "DIXON",
    "Amber Enterprises India Ltd": "AMBER",
    "Zomato Ltd": "ZOMATO",
    "Paytm (One 97 Communications Ltd)": "PAYTM",
    "Nykaa (FSN E-Commerce Ventures Ltd)": "NYKAA",
    "LIC Housing Finance Ltd": "LICHSGFIN",
    "Piramal Enterprises Ltd": "PEL",
    "IRCTC": "IRCTC",
    "Mazagon Dock Shipbuilders Ltd": "MAZDOCK",
    "Garden Reach Shipbuilders & Engineers Ltd": "GRSE",
    "Data Patterns (India) Ltd": "DATAPATTNS",
    "Paras Defence and Space Technologies Ltd": "PARAS",
    "Mphasis Ltd": "MPHASIS",
    "Persistent Systems Ltd": "PERSISTENT",
    "Coforge Ltd": "COFORGE",
    "L&T Technology Services Ltd": "LTTS",
    "KPIT Technologies Ltd": "KPITTECH",
    "Tata Elxsi Ltd": "TATAELXSI",
    "Mindtree Ltd": "MINDTREE",
    "Polycab India Ltd": "POLYCAB",
    "Havells India Ltd": "HAVELLS",
    "Torrent Power Ltd": "TORNTPOWER",
    "Jindal Steel & Power Ltd": "JINDALSTEL",
    "Hindalco Industries Ltd": "HINDALCO",
    "Vedanta Ltd": "VEDL",
    "Ambuja Cements Ltd": "AMBUJACEM",
    "UltraTech Cement Ltd": "ULTRACEMCO",
    "Dalmia Bharat Ltd": "DALMIABHAR",
    "ACC Ltd": "ACC",
    "Grasim Industries Ltd": "GRASIM",
    "Shree Cement Ltd": "SHREECEM",
}

# Define the Indian Standard Time (IST) timezone
IST = pytz.timezone('Asia/Kolkata')

# ----------------------------
# Data Download Function (from data_5.py, adapted for Streamlit)
# ----------------------------
def update_historical_data(kite_instance, stocks_map, data_folder_path):
    """
    Updates historical 5-minute data for a list of stocks.
    Fetches new data since the last available bar or downloads full data if not present.
    Displays progress using Streamlit.
    """
    interval = "5minute"
    end_date = datetime.now(IST)
    default_start_date = end_date - timedelta(days=180)
    chunk_size = 30  # days per chunk for 5-minute data

    os.makedirs(data_folder_path, exist_ok=True)
    st.info(f"Starting data update for {len(stocks_map)} stocks...")

    # Fetch instrument tokens
    instrument_map = {}
    try:
        instruments = kite_instance.instruments("NSE")
        for instrument in instruments:
            if instrument['exchange'] == 'NSE':
                instrument_map[instrument['tradingsymbol']] = instrument['instrument_token']
        st.success("Instrument tokens mapped.")
    except Exception as e:
        st.error(f"Error fetching instrument list: {e}")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, (company_name, symbol) in enumerate(stocks_map.items()):
        progress_bar.progress((i + 1) / len(stocks_map))
        status_text.text(f"Processing: {company_name} ({symbol})")

        if symbol is None:
            st.warning(f"Skipping {company_name}: Not tradable or symbol not provided.")
            continue

        token = instrument_map.get(symbol)
        if token is None:
            st.warning(f"Instrument token not found for {symbol}")
            continue

        file_path = os.path.join(data_folder_path, f"{symbol}.csv")
        current_start_fetch = default_start_date

        existing_df = pd.DataFrame() # Initialize as empty DataFrame

        if os.path.exists(file_path):
            try:
                existing_df = pd.read_csv(file_path, parse_dates=['date'], index_col='date')
                if existing_df.index.tz is None:
                    existing_df.index = existing_df.index.tz_localize(IST)
                else:
                    existing_df.index = existing_df.index.tz_convert(IST)

                last_bar_time = existing_df.index.max()
                current_start_fetch = last_bar_time
                st.info(f"  Existing data found for {symbol}. Last bar at: {last_bar_time}. Fetching new data from this point.")
            except Exception as e:
                st.warning(f"  Error reading existing file {file_path}: {e}. Starting fresh download for {symbol}.")
                current_start_fetch = default_start_date
        else:
            st.info(f"  No existing data found for {symbol}. Downloading from {default_start_date.strftime('%Y-%m-%d %H:%M:%S %Z%z')}.")

        # Add a small buffer to end_date to ensure we fetch current incomplete bar if needed
        # Kite historical data for '5minute' interval will return data up to the last *completed* 5-min bar.
        # To get the latest possible data (which might include the current incomplete bar),
        # we can fetch slightly beyond the current time, or just up to current time and rely on deduplication.
        # Let's stick to 'end_date' for 'to_date' as Kite typically handles it this way.
        fetch_until = end_date # Fetch up to the current time in IST

        if current_start_fetch >= fetch_until:
            st.info(f"  {symbol} is already up-to-date or last bar is too recent. Skipping download for this stock.")
            continue

        all_new_data = []
        temp_start = current_start_fetch

        while temp_start < fetch_until:
            temp_end = temp_start + timedelta(days=chunk_size)
            if temp_end > fetch_until:
                temp_end = fetch_until

            if temp_start >= temp_end:
                break

            try:
                from_date_str = temp_start.strftime('%Y-%m-%d %H:%M:%S')
                to_date_str = temp_end.strftime('%Y-%m-%d %H:%M:%S')
                #st.write(f"  Fetching chunk: {from_date_str} to {to_date_str}") # Too verbose for Streamlit
                chunk = kite_instance.historical_data(
                    instrument_token=token,
                    from_date=from_date_str,
                    to_date=to_date_str,
                    interval=interval,
                    continuous=False
                )
                all_new_data.extend(chunk)
            except Exception as e:
                st.warning(f"  Failed to fetch chunk for {symbol}: {e}")
                break

            temp_start = temp_end

        if all_new_data:
            new_df = pd.DataFrame(all_new_data)
            new_df['date'] = pd.to_datetime(new_df['date'])

            if new_df['date'].dt.tz is None:
                new_df['date'] = new_df['date'].dt.tz_localize(IST)
            else:
                new_df['date'] = new_df['date'].dt.tz_convert(IST)

            new_df.set_index('date', inplace=True)
            new_df.sort_index(inplace=True)
            new_df.rename(columns={
                'open': 'open', 'high': 'high', 'low': 'low',
                'close': 'close', 'volume': 'volume'
            }, inplace=True)

            if not existing_df.empty: # Check if existing_df was successfully loaded and is not empty
                combined_df = pd.concat([existing_df, new_df])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df.sort_index(inplace=True)
                df_to_save = combined_df
                st.success(f"  Updated existing data for {symbol} with {len(new_df)} raw new entries.")
            else:
                df_to_save = new_df
                st.success(f"  Downloaded initial {len(new_df)} entries for {symbol}.")

            df_to_save.to_csv(file_path)
            st.info(f"✅ Saved/Updated: {file_path} (Data from {df_to_save.index.min()} → {df_to_save.index.max()})")
        else:
            if not os.path.exists(file_path):
                st.warning(f"⚠️ No data fetched for {symbol} in the selected period and no existing file found.")
            else:
                st.info(f"✅ {symbol} is already up-to-date or no new data available.")

    status_text.text("✅ All data downloads/updates completed.")


# ----------------------------
# Feature Calculation (from live.py)
# ----------------------------
def compute_indicators(df):
    df = df.copy()
    # Ensure there's enough data for indicator calculation (e.g., 14 periods for RSI/ADX)
    if len(df) < 20: # Z-score uses 20-period rolling mean/std
        return df # Not enough data for meaningful indicators

    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["adx"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14).adx()
    df["stoch_k"] = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"]).stoch()
    bb = ta.volatility.BollingerBands(df["close"])
    df["bbw"] = bb.bollinger_wband()
    df["zscore"] = (df["close"] - df["close"].rolling(20).mean()) / df["close"].rolling(20).std()
    return df

# ----------------------------
# Signal Evaluation (from live.py)
# ----------------------------
# CONFIGURATION
DATA_FOLDER = "data_5min" # Use the same data folder

BEST_PARAMS = {
    "rsi_thr": 52,
    "adx_thr": 22,
    "zscore_thr": 2,
    "stoch_k_thr": 80,
    "bbw_max": 5,
    "trailing_sl_pct": 0.02 # Not used in signal generation, but useful for strategy
}

def evaluate_stock(symbol):
    path = os.path.join(DATA_FOLDER, f"{symbol}.csv")
    if not os.path.exists(path):
        return None

    try:
        df = pd.read_csv(path, parse_dates=["date"], index_col='date') # Add index_col='date'
        
        # Ensure consistency in timezone for comparison if needed, though indicators don't care
        # If your CSV is already tz-aware, parse_dates handles it.
        # If it's naive and supposed to be IST, localize it.
        if df.index.tz is None:
            df.index = df.index.tz_localize(IST)

        df = df.sort_index() # Sort by index (date)
        df = compute_indicators(df)

        # Drop rows with NaN values introduced by indicator calculation
        df.dropna(inplace=True)

        if df.empty:
            st.warning(f"[{symbol}] Not enough data to compute all indicators after dropping NaNs.")
            return None

        latest = df.iloc[-1]

        # Check for NaN values in latest indicators before comparison
        if pd.isna(latest["rsi"]) or pd.isna(latest["adx"]) or \
           pd.isna(latest["zscore"]) or pd.isna(latest["stoch_k"]) or \
           pd.isna(latest["bbw"]):
            # st.info(f"[{symbol}] Latest indicator values contain NaNs. Skipping.") # Too verbose
            return None

        if (
            latest["rsi"] > BEST_PARAMS["rsi_thr"] and
            latest["adx"] > BEST_PARAMS["adx_thr"] and
            abs(latest["zscore"]) > BEST_PARAMS["zscore_thr"] and
            latest["stoch_k"] > BEST_PARAMS["stoch_k_thr"] and
            latest["bbw"] < BEST_PARAMS["bbw_max"]
        ):
            return {
                "symbol": symbol,
                "rsi": round(latest["rsi"], 2),
                "adx": round(latest["adx"], 2),
                "zscore": round(latest["zscore"], 2),
                "stoch_k": round(latest["stoch_k"], 2),
                "bbw": round(latest["bbw"], 2),
                "signal": "BUY",
                "latest_close": round(latest["close"], 2),
                "latest_time": latest.name.strftime('%Y-%m-%d %H:%M:%S %Z%z')
            }
    except Exception as e:
        st.warning(f"[{symbol}] Error during evaluation: {e}")
    return None

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="📈 Intraday Buy Signal Generator")
st.title("📊 Intraday Buy Signal Generator")

st.write("Click the button below to update stock data and generate a buy signal.")

# Initialize session state for analysis results
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

if st.button("🚀 Update Data & Generate Signal"):
    st.session_state.analysis_results = None # Clear previous results

    # 1. Update data
    with st.spinner("Updating historical stock data... This may take a while depending on the number of stocks and data gaps."):
        update_historical_data(kite, STOCKS_TO_DOWNLOAD, DATA_FOLDER)

    # 2. Analyze data
    st.subheader("Running Signal Analysis...")
    symbols_in_data_folder = [f.replace(".csv", "") for f in os.listdir(DATA_FOLDER) if f.endswith(".csv")]
    st.write(f"📂 Found {len(symbols_in_data_folder)} stocks with data for analysis.")

    qualified = []
    analysis_progress_bar = st.progress(0)
    analysis_status_text = st.empty()

    for i, sym in enumerate(symbols_in_data_folder):
        analysis_progress_bar.progress((i + 1) / len(symbols_in_data_folder))
        analysis_status_text.text(f"Analyzing: {sym}")
        result = evaluate_stock(sym)
        if result:
            qualified.append(result)

    analysis_status_text.text("Analysis complete.")

    # 3. Display the best stock
    if qualified:
        # Sort by zscore (or any other metric you prefer for "best")
        # Higher absolute zscore indicates larger deviation from mean, which could mean a stronger movement
        # If looking for BUY, positive zscore might be preferred for momentum, or negative for mean reversion.
        # Here, BEST_PARAMS['zscore_thr'] is abs(zscore), so we sort by absolute zscore to find the "strongest" signal.
        best = sorted(qualified, key=lambda x: abs(x["zscore"]), reverse=True)[0]
        st.success(f"✅ Best BUY SIGNAL for: **{best['symbol']}**")
        st.json(best)
        st.session_state.analysis_results = best
    else:
        st.warning("🚫 No stock satisfied the signal criteria after updating and analyzing data.")
        st.session_state.analysis_results = "None"

# Display last analysis result if available
if st.session_state.analysis_results and st.session_state.analysis_results != "None":
    st.subheader("Last Generated Buy Signal:")
    st.success(f"✅ **{st.session_state.analysis_results['symbol']}**")
    st.json(st.session_state.analysis_results)
elif st.session_state.analysis_results == "None":
    st.subheader("Last Analysis Result:")
    st.info("No stock satisfied the signal criteria in the previous run.")

st.markdown("---")
st.markdown("### Data Folder:")
st.code(os.path.abspath(DATA_FOLDER))
st.info("Ensure you have a 'data_5min' folder in the same directory as this script.")

