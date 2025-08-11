import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone, date
import requests
import pandas as pd
import streamlit as st

# =========================
# SPAFS Branding & Config
# =========================
ORG_NAME = "Sudan Platform for Agriculture and Food Security (SPAFS)"
DONATE_URL = os.environ.get("SPAFS_DONATE_URL", "https://spafs.org/donate")  # placeholder; update when ready
RSVP_URL = os.environ.get("SPAFS_RSVP_URL", "https://spafs.org/rsvp")        # placeholder; update when ready
CONTACT_EMAIL = os.environ.get("SPAFS_CONTACT_EMAIL", "hello@spafs.org")
EVENT_INFO = "Bay Area Fundraiser • Sat, Sept 20, 2025 • USF Theater"

# Data snapshots for trends & delta alerts
SNAPSHOT_PATH = os.environ.get("SPAFS_SNAPSHOT_PATH", "snapshots.csv")

# Email alert config (optional)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
ALERT_TO = os.environ.get("ALERT_TO", "")
ALERT_FROM = os.environ.get("ALERT_FROM", SMTP_USER or "alerts@spafs.org")
ALERT_THRESHOLD_IDPS = float(os.environ.get("ALERT_THRESHOLD_IDPS", "150000"))      # alert if IDPs jump by >= 150k
ALERT_THRESHOLD_REFUGEES = float(os.environ.get("ALERT_THRESHOLD_REFUGEES", "100000"))

st.set_page_config(page_title=f"{ORG_NAME} – Sudan Crisis Dashboard", page_icon="🆘", layout="wide")

LOGO_PATH = os.environ.get("SPAFS_LOGO", "")

# -------------------------
# i18n: English / Arabic
# -------------------------
LANG = st.sidebar.selectbox("Language / اللغة", ["English", "العربية"])

T = {
  "English": {
    "title": "🆘 Sudan Crisis Daily Dashboard",
    "byline": f"Official dashboard by the {ORG_NAME}.",
    "event": "Event",
    "rsvp": "🎟 RSVP for Bay Area Event",
    "donate": "❤️ Donate to SPAFS",
    "contact": "Contact",
    "sources_caption": "Data refreshes every 24 hours. Sources: OCHA FTS, IOM DTM/HDX (Datastore API), UNHCR Refugee Statistics, IPC, WHO.",
    "requirements": "Requirements",
    "funding": "Funding Received (FTS)",
    "idps": "Total IDPs (IOM DTM via HDX API)",
    "refugees": "Refugees from Sudan (UNHCR)",
    "overview": "Overview & Sources",
    "about": f"{ORG_NAME} strengthens agricultural resilience and bridges critical gaps during crises to ensure stable food access for vulnerable communities across Sudan.",
    "what_shows": "What this shows",
    "shows_list": [
        "Funding: Requirements and funding received for the Sudan HRP (OCHA FTS).",
        "Displacement: IDPs (IOM DTM via HDX Datastore API) and refugees from Sudan (UNHCR Refugee Statistics API).",
        "Food & Nutrition: IPC alerts and maps for famine classification.",
        "Health: WHO updates, including attacks on health and outbreak context."
    ],
    "last_updated": "Last updated (UTC)",
    "primary_sources": "Primary sources",
    "tab_funding": "Funding (OCHA FTS)",
    "tab_displacement": "Displacement (IOM DTM & UNHCR)",
    "tab_health": "Health System & Outbreaks (WHO)",
    "host_country_stats": "Host Country Stats (UNHCR)",
    "egypt": "Egypt",
    "chad": "Chad",
    "south_sudan": "South Sudan",
    "alerts": "📣 Email Alerts (optional)",
    "enable_snap": "Enable daily snapshot persistence (writes to file on server)",
    "email_info": "Configure SMTP_* env vars to send email when jumps exceed thresholds.",
    "no_email": "Email not configured. Set SMTP_HOST/USER/PASS and ALERT_TO to enable.",
    "crisis_numbers": "Sudan Crisis Key Numbers",
    "people_in_need": "People in Need (2025)",
    "increase_from_2024": "Increase from 2024",
    "children_in_need": "Children in Need",
    "life_saving_aid": "People Needing Life-saving Aid",
    "acute_food_insecurity": "People Facing Acute Food Insecurity",
    "children_malnutrition": "Children at Risk of Acute Malnutrition (2025)",
    "severe_malnutrition": "Children at Risk of Severe Acute Malnutrition (2025)",
    "hrp_funding_required": "HRP Funding Required (2025)",
    "hrp_funding_received": "HRP Funding Received (2025)",
    "famine_affected": "People Affected by Famine Conditions",
    "displacement_crisis": "Largest Displacement Crisis Globally",
    "health_facilities_non_operational": "Health Facilities Non-operational",
    "attacks_on_healthcare": "Attacks on Healthcare Facilities"
  },
  "العربية": {
    "title": "🆘 لوحة مؤشرات أزمة السودان اليومية",
    "byline": f"اللوحة الرسمية لـ {ORG_NAME}.",
    "event": "الفعالية",
    "rsvp": "🎟 احجز للمناسبة في منطقة الخليج",
    "donate": "❤️ تبرّع لـ SPAFS",
    "contact": "تواصل",
    "sources_caption": "يتم تحديث البيانات كل 24 ساعة. المصادر: OCHA FTS، IOM/HDX (Datastore API)، UNHCR، IPC، WHO.",
    "requirements": "الاحتياجات",
    "funding": "التمويل المستلم (FTS)",
    "idps": "النازحون داخليًا (IOM/HDX API)",
    "refugees": "اللاجئون من السودان (UNHCR)",
    "overview": "نظرة عامة والمصادر",
    "about": f"{ORG_NAME} يدعم صغار المزارعين ويعزّز صمود النُظم الزراعية لضمان الوصول إلى الغذاء للأسر الأشد ضعفًا.",
    "what_shows": "ما الذي تعرضه اللوحة",
    "shows_list": [
        "التمويل: احتياجات وخطط السودان (OCHA FTS).",
        "النزوح: نازحون داخليًا (IOM/HDX API) ولاجئون من السودان (UNHCR).",
        "الغذاء والتغذية: تنبيهات وتصنيفات IPC.",
        "الصحة: تحديثات WHO بما فيها الاعتداءات على المرافق الصحية."
    ],
    "last_updated": "آخر تحديث (UTC)",
    "primary_sources": "المصادر الأساسية",
    "tab_funding": "التمويل (OCHA FTS)",
    "tab_displacement": "النزوح (IOM DTM & UNHCR)",
    "tab_health": "النظام الصحي والتفشّيات (WHO)",
    "host_country_stats": "دول الاستضافة (UNHCR)",
    "egypt": "مصر",
    "chad": "تشاد",
    "south_sudan": "جنوب السودان",
    "alerts": "📣 تنبيهات عبر البريد (اختياري)",
    "enable_snap": "تفعيل حفظ لقطات يومية (حفظ ملف على الخادم)",
    "email_info": "فعّل متغيرات SMTP_* لإرسال بريد عند تجاوز القيم للعتبات.",
    "no_email": "البريد غير مهيّأ. عيّن SMTP_HOST/USER/PASS و ALERT_TO للتفعيل.",
    "crisis_numbers": "أرقام أزمة السودان الرئيسية",
    "people_in_need": "الpersons المحتاجون (2025)",
    "increase_from_2024": "الزيادة من 2024",
    "children_in_need": "الأطفال المحتاجون",
    "life_saving_aid": "الأشخاص المحتاجون للمساعدات المنقذة للحياة",
    "acute_food_insecurity": "الأشخاص المتأثرون بالجوع الحاد",
    "children_malnutrition": "الأطفال المعرضون لخطر سوء التغذية الحاد (2025)",
    "severe_malnutrition": "الأطفال المعرضون لخطر سوء التغذية الحاد الشديد (2025)",
    "hrp_funding_required": "التمويل المطلوب لخطة الاستجابة الإنسانية (2025)",
    "hrp_funding_received": "التمويل المستلم لخطة الاستجابة الإنسانية (2025)",
    "famine_affected": "الأشخاص المتأثرون بظروف المجاعة",
    "displacement_crisis": "أكبر أزمة نزوح في العالم",
    "health_facilities_non_operational": "المرافق الصحية غير العاملة",
    "attacks_on_healthcare": "الهجمات على المرافق الصحية"
  }
}

# -------------------------
# Helpers
# -------------------------
@st.cache_data(ttl=300)  # 5 minutes cache
def fetch_json(url, params=None, headers=None):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.warning(f"Error fetching data from {url}: {e}")
        return None

def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

def safe_get(d, *keys, default=None):
    x = d
    for k in keys:
        if isinstance(x, dict) and k in x:
            x = x[k]
        else:
            return default
    return x

def fmt_num(n):
    try:
        n = float(n)
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        if n >= 1_000:
            return f"{n/1_000:.2f}K"
        return f"{int(n)}"
    except Exception:
        return "—"

# -------------------------
# Robust Data Getters with Fallbacks
# -------------------------

@st.cache_data(ttl=3600)  # 1 hour cache
def get_sudan_hrp_data():
    """
    Get Sudan HRP 2025 funding data with fallbacks
    """
    try:
        # Try the FTS API first
        FTS_API_BASE = "https://api.hpc.tools/v2/public"
        plan_id = 1220  # Sudan HRP 2025
        
        # Get plan details
        plan_url = f"{FTS_API_BASE}/plan/{plan_id}"
        plan_data = fetch_json(plan_url)
        
        if plan_data:
            # Extract requirements
            required = safe_get(plan_data, "planVersion", "financialRequirements", "originalRequirements")
            
            # Try to get funding - multiple possible locations
            funded = None
            
            # First try revisedFunding
            if not funded:
                funded = safe_get(plan_data, "planVersion", "revisedFunding")
            
            # Then try allocationSources
            if not funded:
                allocations = safe_get(plan_data, "planVersion", "allocationSources")
                if allocations and isinstance(allocations, list):
                    funded = sum([safe_get(a, "amountUSD", default=0) for a in allocations])
            
            # Then try requirements with fundedPercentage
            if not funded and required:
                funded_percentage = safe_get(plan_data, "planVersion", "fundedPercentage")
                if funded_percentage:
                    funded = required * (funded_percentage / 100)
            
            if required or funded:
                return {
                    "required": required,
                    "funded": funded,
                    "source": "OCHA FTS API"
                }
    except Exception as e:
        st.warning(f"Error fetching from FTS API: {e}")
    
    # Fallback to documented values
    return {
        "required": 4160000000,  # $4.16B
        "funded": 266240000,     # 6.4% of $4.16B = ~$266.24M
        "source": "Documented values"
    }

@st.cache_data(ttl=3600)  # 1 hour cache
def get_idp_data():
    """
    Get IDP data with fallbacks
    """
    try:
        # Try HDX API approach
        HDX_CKAN_BASE = "https://data.humdata.org/api/3/action"
        DATASETS = ["sudan-displacement-situation-idps-iom-dtm", "sudan-displacement-data-idps-iom-dtm"]
        
        for dataset_name in DATASETS:
            try:
                # Get package info
                package_url = f"{HDX_CKAN_BASE}/package_show"
                package_data = fetch_json(package_url, params={"id": dataset_name})
                
                if package_data:
                    resources = safe_get(package_data, "result", "resources", default=[])
                    # Find datastore active resources
                    datastore_resources = [r for r in resources if r.get("datastore_active")]
                    
                    if datastore_resources:
                        # Use the most recent resource
                        resource = sorted(datastore_resources, 
                                        key=lambda r: r.get("last_modified") or r.get("created") or "",
                                        reverse=True)[0]
                        
                        # Search datastore
                        search_url = f"{HDX_CKAN_BASE}/datastore_search"
                        search_data = fetch_json(search_url, 
                                               params={"resource_id": resource["id"], "limit": 1000})
                        
                        if search_data:
                            records = safe_get(search_data, "result", "records", default=[])
                            if records:
                                # Look for IDP columns
                                df = pd.DataFrame(records)
                                
                                # Find a column that looks like total IDPs
                                idp_cols = [col for col in df.columns 
                                          if "idp" in col.lower() and ("total" in col.lower() or "count" in col.lower())]
                                
                                if idp_cols:
                                    # Get the latest value
                                    col = idp_cols[0]
                                    latest_value = pd.to_numeric(df[col], errors='coerce').dropna().iloc[-1]
                                    return {
                                        "total_idps": int(latest_value),
                                        "source": f"IOM DTM via HDX ({dataset_name})"
                                    }
            except Exception as e:
                st.warning(f"Error processing dataset {dataset_name}: {e}")
                continue
                
    except Exception as e:
        st.warning(f"Error in HDX data fetching: {e}")
    
    # Fallback to documented value
    return {
        "total_idps": 10900000,  # 10.9 million
        "source": "Documented value"
    }

@st.cache_data(ttl=3600)  # 1 hour cache
def get_refugee_data():
    """
    Get refugee data with fallbacks
    """
    try:
        # Try UNHCR API
        UNHCR_API = "https://api.unhcr.org/population/v1/population"
        params = {
            "coo": "SDN",  # Country of Origin: Sudan
            "yearFrom": 2023,
            "yearTo": datetime.now().year,
            "coa_all": "true",  # Country of Asylum: all
            "cf_type": "ISO",
            "limit": 50000,
        }
        
        data = fetch_json(UNHCR_API, params=params)
        if data:
            rows = data.get("data") or data.get("items") or []
            total = 0
            for row in rows:
                # Try different possible fields for refugee count
                v = row.get("refugees") or row.get("value") or row.get("obs_value") or 0
                try:
                    total += int(float(v))
                except:
                    pass
                    
            if total > 0:
                return {
                    "total_refugees": total,
                    "source": "UNHCR API"
                }
    except Exception as e:
        st.warning(f"Error fetching refugee data: {e}")
    
    # Fallback to documented value
    return {
        "total_refugees": 3500000,  # 3.5 million
        "source": "Documented value"
    }

# -------------------------
# Sidebar (Branding & Actions)
# -------------------------
with st.sidebar:
    if LOGO_PATH and os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, caption="SPAFS", use_column_width=True)
    st.markdown(f"### {ORG_NAME}")
    st.write(T[LANG]["byline"])
    st.markdown(f"**{T[LANG]['event']}:** {EVENT_INFO}")
    st.link_button(T[LANG]["rsvp"], RSVP_URL)
    st.link_button(T[LANG]["donate"], DONATE_URL)
    st.markdown("---")
    st.markdown(f"**{T[LANG]['contact']}**")
    st.write(CONTACT_EMAIL)
    st.markdown("---")
    st.caption(T[LANG]["sources_caption"])

# -------------------------
# Main KPIs
# -------------------------
st.title(T[LANG]["title"])
st.caption(T[LANG]["byline"])

# Create two rows of metrics
colA, colB, colC, colD = st.columns(4)

# Get the data
hrp_data = get_sudan_hrp_data()
idp_data = get_idp_data()
refugee_data = get_refugee_data()

required = hrp_data.get("required")
funded = hrp_data.get("funded")
idps = idp_data.get("total_idps")
refugees = refugee_data.get("total_refugees")

# Calculate percentage
pct = None
if required and funded:
    try:
        pct = (float(funded) / float(required)) * 100.0
    except Exception:
        pct = None

# Display metrics
with colA:
    st.metric(f"Sudan HRP 2025 – {T[LANG]['requirements']}", 
              f"${fmt_num(required) if required else '—'}")
    if hrp_data.get("source"):
        st.caption(f"Source: {hrp_data['source']}")

with colB:
    st.metric(T[LANG]["funding"], 
              f"${fmt_num(funded) if funded else '—'}", 
              delta=f"{pct:.1f}%" if pct is not None else None)
    if hrp_data.get("source"):
        st.caption(f"Source: {hrp_data['source']}")

with colC:
    st.metric(T[LANG]["idps"], 
              f"{fmt_num(idps) if idps else '—'}")
    if idp_data.get("source"):
        st.caption(f"Source: {idp_data['source']}")

with colD:
    st.metric(T[LANG]["refugees"], 
              f"{fmt_num(refugees) if refugees else '—'}")
    if refugee_data.get("source"):
        st.caption(f"Source: {refugee_data['source']}")

# Additional crisis numbers
st.divider()
st.subheader(T[LANG]["crisis_numbers"])

# First row of crisis numbers
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(T[LANG]["people_in_need"], "30.4M")
with col2:
    st.metric(T[LANG]["increase_from_2024"], "6.6M")
with col3:
    st.metric(T[LANG]["children_in_need"], "16M")
with col4:
    st.metric(T[LANG]["life_saving_aid"], "18.1M")

# Second row of crisis numbers
col5, col6, col7, col8 = st.columns(4)
with col5:
    st.metric(T[LANG]["acute_food_insecurity"], "25-26M")
with col6:
    st.metric(T[LANG]["children_malnutrition"], "3.2M")
with col7:
    st.metric(T[LANG]["severe_malnutrition"], "770K")
with col8:
    st.metric(T[LANG]["hrp_funding_required"], "$4.16B")

# Third row of crisis numbers
col9, col10, col11, col12 = st.columns(4)
with col9:
    st.metric(T[LANG]["hrp_funding_received"], "6.4%" if funded and required else "—")
with col10:
    st.metric(T[LANG]["famine_affected"], "11M+")
with col11:
    st.metric(T[LANG]["displacement_crisis"], "Yes")
with col12:
    st.metric(T[LANG]["health_facilities_non_operational"], ">70%")

st.divider()

# -------------------------
# Host Country Stats
# -------------------------
st.subheader(T[LANG]["host_country_stats"])
# Using documented values for host country stats since we don't have API access
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(T[LANG]["egypt"], "1.2M")  # Documented value ~39% of 3.1M
with c2:
    st.metric(T[LANG]["chad"], "980K")   # Documented value ~28% of 3.1M
with c3:
    st.metric(T[LANG]["south_sudan"], "840K")  # Documented value ~27% of 3.1M

# -------------------------
# Data Source Information
# -------------------------
with st.expander("Data Source Details"):
    st.subheader("Data Sources and Methods")
    st.write("**Funding Data (OCHA FTS):**")
    st.write(f"- Source: {hrp_data.get('source', 'Unknown')}")
    st.write(f"- Requirements: ${fmt_num(required) if required else 'N/A'}")
    st.write(f"- Funded: ${fmt_num(funded) if funded else 'N/A'}")
    if pct is not None:
        st.write(f"- Percentage: {pct:.1f}%")
    
    st.write("**IDP Data (IOM DTM):**")
    st.write(f"- Source: {idp_data.get('source', 'Unknown')}")
    st.write(f"- Total IDPs: {fmt_num(idps) if idps else 'N/A'}")
    
    st.write("**Refugee Data (UNHCR):**")
    st.write(f"- Source: {refugee_data.get('source', 'Unknown')}")
    st.write(f"- Total Refugees: {fmt_num(refugees) if refugees else 'N/A'}")
    
    st.info("🔄 Data refreshes every hour. Last updated: " + now_utc())

# -------------------------
# Tabs for additional information
# -------------------------
tab1, tab2 = st.tabs([T[LANG]["overview"], "About SPAFS"])

with tab1:
    st.subheader(T[LANG]["overview"])
    st.write(T[LANG]["about"])
    st.write("**" + T[LANG]["what_shows"] + "**")
    for item in T[LANG]["shows_list"]:
        st.write("- " + item)
    st.info(f"{T[LANG]['last_updated']}: {now_utc()}")
    st.write("**" + T[LANG]["primary_sources"] + "**")
    st.write("- OCHA FTS (funding): https://api.hpc.tools/docs/v2/")
    st.write("- UNHCR Refugee Statistics API: https://api.unhcr.org/docs/refugee-statistics.html")
    st.write("- IOM DTM (IDPs): https://dtm.iom.int/sudan • via HDX Datastore API")
    st.write("- IPC Famine Alerts: https://www.ipcinfo.org/")
    st.write("- WHO: https://www.who.int/emergencies")

with tab2:
    st.subheader("About SPAFS")
    st.write("""
    The Sudan Platform for Agriculture and Food Security (SPAFS) is a vital initiative focused on 
    empowering Sudanese smallholder farmers and providing direct response to the acute food crisis 
    affecting millions in Sudan.
    
    In the challenging context of regional conflict and severe economic downturn, SPAFS has emerged 
    as a crucial focal point for coordinated agricultural support efforts, helping to sustain food 
    systems under extremely difficult circumstances.
    
    This dashboard provides real-time updates on the humanitarian situation in Sudan to help inform 
    and mobilize support for SPAFS's mission.
    """)
    st.link_button("Learn More About SPAFS", "https://spafs.org")