# -------------------------------------------------------------------------
# CAR (Cumulative Average) + 30, 50, 200 DMA सुपर ब्रेकआउट स्कैनर
# --- Streamlit Web App Version ---
# अब यह कोड कोलाब में नहीं, बल्कि एक वेब पेज पर चलेगा।
# पिताजी को सिर्फ एक लिंक खोलना है और "Run" बटन दबाना है।
# -------------------------------------------------------------------------

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import warnings
import logging
import io
from datetime import datetime
from io import BytesIO

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
warnings.filterwarnings('ignore')

# -------------------------------------------------------------------------
# NSE की आधिकारिक लिस्ट रोज़ लाइव लाना (Live F&O List from NSE)
# -------------------------------------------------------------------------
# NSE हर दिन यह फाइल अपडेट करता है — इसमें वो सभी स्टॉक्स होते हैं जो
# Futures & Options (F&O) सेगमेंट में ट्रेड होने के लिए Eligible हैं।
# यही वो आधिकारिक सोर्स है जहाँ से हमारी मूल लिस्ट (नीचे FALLBACK_STOCK_LIST) बनी थी।
NSE_FO_LIST_URL = "https://nsearchives.nseindia.com/content/fo/NSE_FO_SosScheme.csv"


def fetch_live_fo_stock_list():
    """
    NSE की साइट से आज की आधिकारिक F&O स्टॉक लिस्ट डाउनलोड करता है।
    अगर यह किसी वजह से फेल हो (NSE डाउन हो, नेटवर्क इशू हो, फॉर्मेट बदल जाए),
    तो यह Exception raise करेगा — और बटन दबाने वाला कोड नीचे दी गई
    FALLBACK_STOCK_LIST पर अपने आप शिफ्ट हो जाएगा, ताकि ऐप कभी टूटे ना।
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
        )
    }
    response = requests.get(NSE_FO_LIST_URL, headers=headers, timeout=15)
    response.raise_for_status()

    # पहली लाइन सिर्फ तारीख होती है (जैसे 12082026), असली डेटा दूसरी लाइन से शुरू होता है
    df = pd.read_csv(io.StringIO(response.text), skiprows=1)
    df.columns = [c.strip() for c in df.columns]

    # 'Symbol Type' == EQUITY वाली रो ही असली स्टॉक्स हैं
    # (NIFTY, BANKNIFTY जैसे इंडेक्स को Symbol Type = INDEX से बाहर कर दिया जाता है)
    equity_symbols = (
        df[df['Symbol Type'].str.strip() == 'EQUITY']['Symbol']
        .str.strip()
        .unique()
        .tolist()
    )

    if len(equity_symbols) < 100:
        # अगर बहुत कम स्टॉक्स मिले तो शायद NSE ने फॉर्मेट बदल दिया — सुरक्षित रहने के लिए फेल मानें
        raise ValueError(f"सिर्फ {len(equity_symbols)} स्टॉक्स मिले, फॉर्मेट बदला हो सकता है")

    return [f"{symbol}.NS" for symbol in equity_symbols]

# -------------------------------------------------------------------------
# पेज सेटअप (Page Setup)
# -------------------------------------------------------------------------
st.set_page_config(page_title="Breakout Scanner", page_icon="📈", layout="centered")

st.title("📈 Daily Stock Breakout Scanner")
st.write(
    "रोज़ सुबह यह पेज खोलिए और नीचे दिया बटन दबाइए। "
    "थोड़ी देर में आपको आज के Positive Breakout स्टॉक्स की लिस्ट "
    "और उसकी Excel फाइल मिल जाएगी।"
)

# -------------------------------------------------------------------------
# बैकअप लिस्ट (Fallback Stock List)
# अगर किसी दिन NSE की साइट से लाइव लिस्ट ना मिल पाए, तो यह वाली इस्तेमाल होगी।
# यह लिस्ट समय के साथ थोड़ी पुरानी हो सकती है (जैसे कोई नया स्टॉक F&O में जुड़ जाए),
# लेकिन ऐप कभी पूरी तरह रुकेगा नहीं।
# -------------------------------------------------------------------------
FALLBACK_STOCK_LIST = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANIPOWER.NS', 'ABCAPITAL.NS',
    'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS',
    'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS',
    'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS',
    'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS',
    'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS',
    'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS',
    'COCHINSHIP.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS',
    'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS',
    'DELHIVERY.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS',
    'EICHERMOT.NS', 'EXIDEIND.NS', 'FORCEMOT.NS', 'NYKAA.NS', 'FORTIS.NS',
    'GAIL.NS', 'GVT&D.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODFRYPHLP.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS',
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS',
    'HYUNDAI.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS',
    'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRFC.NS', 'IREDA.NS',
    'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS',
    'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS',
    'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS',
    'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTM.NS',
    'LT.NS', 'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS',
    'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS',
    'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS', 'MOTILALOFS.NS', 'MPHASIS.NS',
    'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS',
    'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NAM-INDIA.NS', 'NUVAMA.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS',
    'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'POLYCAB.NS',
    'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS', 'PNB.NS',
    'RBLBANK.NS', 'RECLTD.NS', 'RADICO.NS', 'RVNL.NS', 'RELIANCE.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'MOTHERSON.NS',
    'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS',
    'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS',
    'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS',
    'TATAPOWER.NS', 'TATASTEEL.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS',
    'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TIINDIA.NS',
    'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS',
    'VBL.NS', 'VEDL.NS', 'VMM.NS', 'IDEA.NS', 'VOLTAS.NS',
    'WAAREEENER.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# -------------------------------------------------------------------------
# मुख्य स्कैनर फंक्शन (Main Scanner Logic) — लॉजिक बिल्कुल वही है
# बस अब यह प्रोग्रेस बार को अपडेट करता है ताकि पिताजी को स्क्रीन पर
# दिखता रहे कि स्कैन चल रहा है (ठप नहीं हुआ)।
# -------------------------------------------------------------------------
def advanced_stock_scanner(ticker_list, progress_bar, status_text):
    results = []
    today_date = datetime.now().strftime("%d-%m-%Y")
    total = len(ticker_list)

    for i, ticker in enumerate(ticker_list):
        status_text.text(f"जांच रहे हैं: {ticker}  ({i + 1}/{total})")
        progress_bar.progress((i + 1) / total)
        try:
            data = yf.download(ticker, period="2y", interval="1d", progress=False)

            if data.empty or len(data) < 200:
                continue

            close_prices = data['Close'].squeeze()

            dma_30 = close_prices.rolling(window=30).mean().iloc[-1]
            dma_50 = close_prices.rolling(window=50).mean().iloc[-1]
            dma_200 = close_prices.rolling(window=200).mean().iloc[-1]

            cmp = close_prices.iloc[-1]

            dist_200_dma = ((cmp - dma_200) / dma_200) * 100

            last_1y_data = data.tail(252)
            high_date = last_1y_data['High'].squeeze().idxmax()

            car_data = close_prices.loc[high_date:]

            if len(car_data) < 10:
                continue

            car_values = car_data.expanding().mean()
            last_10_car = car_values.tail(10)

            if last_10_car.is_monotonic_increasing:
                car_status = 'Positive'
            else:
                car_status = 'Negative'

            if (cmp > dma_30) and (cmp > dma_50) and (cmp > dma_200) and (car_status == 'Positive'):
                action = '🟢 Positive Breakout'
            else:
                action = '🔴 Avoid/Hold'

            if action == '🟢 Positive Breakout':
                results.append({
                    'Date': today_date,
                    'Stock': ticker.replace('.NS', ''),
                    'CMP': round(cmp, 2),
                    '30 DMA': round(dma_30, 2),
                    '50 DMA': round(dma_50, 2),
                    '200 DMA': round(dma_200, 2),
                    '200 DMA Dist %': round(dist_200_dma, 2),
                    'CAR Status': car_status,
                    'Action': action
                })

        except Exception:
            pass

    df_positive = pd.DataFrame(results)
    if not df_positive.empty:
        df_positive = df_positive.sort_values(by='200 DMA Dist %', ascending=True)

    return df_positive


# -------------------------------------------------------------------------
# बटन दबाने पर क्या होगा (What happens when the button is clicked)
# -------------------------------------------------------------------------
st.caption("बटन दबाते ही सबसे पहले NSE से आज की लाइव F&O स्टॉक लिस्ट लाई जाएगी, फिर स्कैन शुरू होगा।")

if st.button("🔍 आज का स्कैन चलाएं (Run Today's Scan)", type="primary", use_container_width=True):

    # पहला कदम: आज की ताज़ा F&O लिस्ट NSE से लाना (फेल हो तो बैकअप लिस्ट पर जाना)
    with st.spinner("NSE से आज की F&O स्टॉक लिस्ट लाई जा रही है..."):
        try:
            my_stocks = fetch_live_fo_stock_list()
            st.success(f"✅ NSE से लाइव लिस्ट मिल गई — आज कुल {len(my_stocks)} स्टॉक्स")
        except Exception as e:
            my_stocks = FALLBACK_STOCK_LIST
            st.warning(
                f"⚠️ NSE से लाइव लिस्ट नहीं मिल पाई, इसलिए सेव्ड बैकअप लिस्ट "
                f"({len(my_stocks)} स्टॉक्स) इस्तेमाल हो रही है। (वजह: {e})"
            )

    st.caption(f"कुल {len(my_stocks)} शेयर स्कैन होंगे। इसमें लगभग 3-6 मिनट लग सकते हैं।")

    progress_bar = st.progress(0)
    status_text = st.empty()

    result_df = advanced_stock_scanner(my_stocks, progress_bar, status_text)

    progress_bar.empty()
    status_text.empty()

    st.subheader("🟢 फाईनल लिस्ट: केवल POSITIVE BREAKOUT स्टॉक्स")

    if result_df.empty:
        st.info("आज किसी भी शेयर ने सभी शर्तें पार नहीं कीं। (कोई नया ब्रेकआउट नहीं)")
    else:
        st.success(f"आज {len(result_df)} स्टॉक्स मिले!")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

        # Excel फाइल को मेमोरी में बनाना (कोई फाइल डिस्क पर सेव नहीं होती)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Breakout')
        buffer.seek(0)

        file_name = f"Breakout_List_{datetime.now().strftime('%d-%m-%Y')}.xlsx"

        st.download_button(
            label="📥 Excel फाइल डाउनलोड करें",
            data=buffer,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
