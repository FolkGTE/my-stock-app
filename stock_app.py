import streamlit as st
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from streamlit_quill import st_quill

# --- 1. ตั้งค่าหน้าเพจ ---
st.set_page_config(page_title="Stock Portfolio Web", layout="wide", initial_sidebar_state="expanded")

# --- การตั้งค่า CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Itim&display=swap');
    
    .ql-editor { 
        font-family: 'Itim', cursive; 
        font-size: 20px;
    }
    
    .ql-toolbar .ql-picker-label, .ql-toolbar .ql-picker-item {
        font-family: 'Itim', cursive;
    }

    [data-testid="stAppViewContainer"] { background-color: #FDF7E3; color: #1A1A1A; }
    [data-testid="stSidebar"] { background-color: #F3EACE; }
    div[data-baseweb="input"] > div { background-color: #ffffff; border: 1px solid #E3CDA4; }
    
    .stElementContainer:has(> iframe) { min-height: 500px; }
    
    .ql-toolbar { background-color: #F3EACE !important; border: 1px solid #E3CDA4 !important; }
    .stButton>button { background-color: #FDF9E8; border: 1px solid #E3CDA4; color: #1A1A1A; font-weight: bold; }
    .stButton>button:hover { background-color: #E3CDA4; }
    .stTextInput label { display: none; }
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- แถบเครื่องมือ Quill Editor ---
CUSTOM_TOOLBAR = [
    [{'font': []}, {'size': ['small', False, 'large', 'huge']}], 
    ['bold', 'italic', 'underline', 'strike'],                    
    [{'color': []}, {'background': []}],                          
    [{'align': []}],                                              
    [{'list': 'ordered'}, {'list': 'bullet'}],                    
    ['clean']                                                     
]

DATA_FILE = "stock_data_v2.json"

# --- 2. ระบบจัดการข้อมูล ---
def load_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, DATA_FILE)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "other_assets" not in data: data["other_assets"] = {}
            return data
    return {"total_assets": 1000000, "cash": 200000, "held_stocks": {}, "other_assets": {}, "watchlist": [], "details": {}}

def save_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, DATA_FILE)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=4)

if 'data' not in st.session_state:
    st.session_state.data = load_data()
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'home'
if 'current_item' not in st.session_state:
    st.session_state.current_item = None

data = st.session_state.data

def get_clean_float(val):
    s = str(val).replace("฿", "").replace("$", "").replace(",", "").replace(" ", "").strip()
    try: return float(s)
    except ValueError: return 0.0

# --- 3. แถบเมนูด้านซ้าย (Sidebar) ---
with st.sidebar:
    if st.button("🏠 กลับหน้าแรก", use_container_width=True):
        st.session_state.current_view = 'home'
        st.rerun()

    st.markdown("### สรุปสินทรัพย์")
    new_ta = st.text_input("สินทรัพย์ทั้งหมด (฿)", value=f"{data['total_assets']:,.0f}")
    new_cash = st.text_input("เงินสดทั้งหมด (฿)", value=f"{data['cash']:,.0f}")
    
    if get_clean_float(new_ta) != data['total_assets'] or get_clean_float(new_cash) != data['cash']:
        data['total_assets'] = get_clean_float(new_ta)
        data['cash'] = get_clean_float(new_cash)
        save_data()

    total_assets = data['total_assets'] if data['total_assets'] > 0 else 1

    def render_sidebar_list(title, cat_key, dict_data):
        st.markdown(f"**{title}**")
        
        with st.expander("➕ เพิ่มข้อมูล"):
            new_name = st.text_input("ชื่อ:", key=f"new_name_{cat_key}")
            if cat_key in ['held_stocks', 'other_assets']:
                new_amt = st.number_input("จำนวนเงิน:", min_value=0.0, step=1000.0, key=f"new_amt_{cat_key}")
            if st.button("บันทึก", key=f"save_btn_{cat_key}"):
                if new_name:
                    if cat_key in ['held_stocks', 'other_assets']:
                        data[cat_key][new_name.upper()] = {"amount": new_amt}
                    else:
                        if new_name.upper() not in data[cat_key]: data[cat_key].append(new_name.upper())
                    save_data()
                    st.rerun()

        if cat_key in ['held_stocks', 'other_assets']:
            sorted_data = dict(sorted(dict_data.items(), key=lambda item: item[1]['amount'], reverse=True))
            for item, info in sorted_data.items():
                pct = (info['amount'] / total_assets) * 100
                label = f"{item} ({pct:.1f}%) ฿{info['amount']:,.0f}"
                if st.button(label, key=f"btn_{cat_key}_{item}", use_container_width=True):
                    st.session_state.current_view = 'detail'
                    st.session_state.current_item = item
                    st.session_state.current_cat = cat_key
                    st.rerun()
        else:
            for item in dict_data:
                if st.button(item, key=f"btn_{cat_key}_{item}", use_container_width=True):
                    st.session_state.current_view = 'detail'
                    st.session_state.current_item = item
                    st.session_state.current_cat = cat_key
                    st.rerun()
        st.markdown("---")

    render_sidebar_list("หุ้นที่ถือ", "held_stocks", data['held_stocks'])
    render_sidebar_list("สินทรัพย์อื่นๆ", "other_assets", data['other_assets'])
    render_sidebar_list("หุ้นสนใจ", "watchlist", data['watchlist'])

# --- 4. พื้นที่แสดงผลหลัก (Main Content) ---
if st.session_state.current_view == 'home':
    st.markdown("<h1 style='color:#1A1A1A; text-align: center;'>ภาพรวมพอร์ตโฟลิโอ</h1>", unsafe_allow_html=True)
    
    if data['held_stocks'] or data['other_assets']:
        combined = {**data["held_stocks"], **data["other_assets"]}
        sorted_combined = dict(sorted(combined.items(), key=lambda item: item[1]['amount'], reverse=True))
        
        labels = list(sorted_combined.keys())
        sizes = [i["amount"] for i in sorted_combined.values()]
        
        if data['cash'] > 0:
            labels.append("CASH")
            sizes.append(data['cash'])

        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor('#FDF7E3') 
        
        patches, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        for i, patch in enumerate(patches):
            color = patch.get_facecolor()
            texts[i].set_color(color)
            texts[i].set_fontsize(12)
            texts[i].set_fontweight('bold')
            autotexts[i].set_color('#FFFFFF')
            autotexts[i].set_fontsize(10)
            autotexts[i].set_fontweight('bold')
            
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.pyplot(fig)
    else:
        st.info("กรุณาเพิ่มข้อมูลหุ้น/สินทรัพย์ เพื่อดูวงกลมสัดส่วนพอร์ต")

elif st.session_state.current_view == 'detail':
    item = st.session_state.current_item
    cat = st.session_state.current_cat
    
    # อัปเดตโครงสร้าง JSON ให้รองรับฟีเจอร์ใหม่
    if item not in data["details"]:
        data["details"][item] = {
            "target_invest": 0, "info": "", "thesis": "", "monitor": "",
            "val_data": [["","","",""], ["","","",""], ["","","",""]],
            "sr_s": ["", "", "", ""], "sr_r": ["", "", "", ""],
            "next_earnings": "", "sr_action": ["", "", "", ""]
        }
    details = data["details"][item]
    
    # ป้องกันแอปพังจากไฟล์เซฟเก่าที่ไม่มี key เหล่านี้
    if "next_earnings" not in details: details["next_earnings"] = ""
    if "sr_action" not in details: details["sr_action"] = ["", "", "", ""]

    col_title, col_edit, col_del = st.columns([1, 4, 1.5])
    col_title.markdown("<h2 style='margin-top:0px;'>ชื่อ:</h2>", unsafe_allow_html=True)
    
    new_item_name = col_edit.text_input("edit_name", value=item, key=f"edit_name_{item}")
    if new_item_name and new_item_name.upper() != item.upper():
        new_name = new_item_name.upper()
        if new_name in data["details"]:
            st.error("ชื่อนี้มีอยู่แล้วในระบบ!")
        else:
            if cat in ['held_stocks', 'other_assets']: data[cat][new_name] = data[cat].pop(item)
            else: 
                idx = data[cat].index(item)
                data[cat][idx] = new_name
            data["details"][new_name] = data["details"].pop(item)
            st.session_state.current_item = new_name
            save_data()
            st.rerun()

    if col_del.button("🗑️ ลบรายการนี้", type="primary", use_container_width=True):
        if cat in ['held_stocks', 'other_assets']: data[cat].pop(item, None)
        else: data[cat].remove(item)
        st.session_state.current_view = 'home'
        save_data()
        st.rerun()

    # 🛠️ ฟีเจอร์ 1: เพิ่มกล่องวันที่ประกาศงบถัดไป
    col_earn_title, col_earn_edit, _ = st.columns([1, 4, 1.5])
    col_earn_title.markdown("<div style='margin-top:8px;'><b>วันประกาศงบฯ:</b></div>", unsafe_allow_html=True)
    new_earnings = col_earn_edit.text_input("next_earnings", value=details["next_earnings"], key=f"earn_{item}", label_visibility="collapsed", placeholder="เช่น Q3 2026 หรือ วันที่ 15 พ.ย.")
    if new_earnings != details["next_earnings"]:
        details["next_earnings"] = new_earnings
        save_data()

    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

    if cat in ['held_stocks', 'other_assets']:
        amt = data[cat][item]['amount']
        tgt = details.get('target_invest', 0)
        
        c1, c2, c3, c4, c5, c6 = st.columns([1.2, 2.5, 1, 2.5, 1, 3])
        c1.markdown("<div style='margin-top: 8px; font-size: 18px;'>ลงทุนไปแล้ว:</div>", unsafe_allow_html=True)
        new_amt = c2.text_input("invested", value=f"฿ {amt:,.0f}", key=f"inv_{item}", label_visibility="collapsed")
        
        c3.markdown("<div style='margin-top: 8px; font-size: 18px;'>เป้าหมาย:</div>", unsafe_allow_html=True)
        new_tgt = c4.text_input("target", value=f"฿ {tgt:,.0f}", key=f"tgt_{item}", label_visibility="collapsed")
        
        pct = min(amt / tgt, 1.0) if tgt > 0 else 0
        c5.markdown(f"<div style='margin-top: 8px; font-size: 18px; text-align: right;'>{pct*100:.1f}%</div>", unsafe_allow_html=True)
        with c6:
            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            st.progress(pct)

        clean_amt = get_clean_float(new_amt)
        clean_tgt = get_clean_float(new_tgt)
        changed = False
        if clean_amt != amt:
            data[cat][item]['amount'] = clean_amt
            changed = True
        if clean_tgt != tgt:
            details['target_invest'] = clean_tgt
            changed = True
            
        if changed:
            save_data()
            st.rerun()

    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📝 ข้อมูล", "🎯 Thesis & Monitor", "📈 Valuation & S/R"])

    with tab1:
        st.markdown("<h3 style='margin-top: 10px;'>รายละเอียดข้อมูลหุ้น</h3>", unsafe_allow_html=True)
        new_info = st_quill(value=details['info'], html=True, toolbar=CUSTOM_TOOLBAR, key=f"q_info_{item}")
        if new_info != details['info']:
            details['info'] = new_info
            save_data()

    with tab2:
        st.markdown("<h3 style='margin-top: 10px;'>Thesis Killer</h3>", unsafe_allow_html=True)
        new_thesis = st_quill(value=details['thesis'], html=True, toolbar=CUSTOM_TOOLBAR, key=f"q_thesis_{item}")
        
        st.markdown("<br><hr><br>", unsafe_allow_html=True) 
        
        st.markdown("<h3 style='margin-top: 10px;'>สิ่งที่ต้องติดตามในไตรมาสถัดไป</h3>", unsafe_allow_html=True)
        new_mon = st_quill(value=details['monitor'], html=True, toolbar=CUSTOM_TOOLBAR, key=f"q_monitor_{item}")
        
        if new_thesis != details['thesis'] or new_mon != details['monitor']:
            details['thesis'] = new_thesis
            details['monitor'] = new_mon
            save_data()

    with tab3:
        st.markdown("#### Valuation")
        # 🛠️ ฟีเจอร์ 2: ปรับลดความกว้าง WACC กับ Value ($) แล้วเพิ่มให้ Growth & FCF
        val_widths = [1.5, 2.5, 2.5, 1.2, 1.2]
        v_cols = st.columns(val_widths)
        headers = ["", "Growth", "FCF Margin", "WACC", "Value ($)"]
        for i, h in enumerate(headers): v_cols[i].markdown(f"**{h}**")
        
        cases = ["Bear case", "Base case", "Bull case"]
        changed = False
        for r, case in enumerate(cases):
            c_cols = st.columns(val_widths)
            c_cols[0].write(case)
            for c in range(4):
                # แก้บั๊ก: ใส่ {item} เข้าไปใน key เพื่อกันไม่ให้โหลดข้อมูลผิดช่อง
                val = c_cols[c+1].text_input("val", value=details['val_data'][r][c], key=f"v_{item}_{r}_{c}", label_visibility="collapsed")
                if val != details['val_data'][r][c]:
                    details['val_data'][r][c] = val
                    changed = True
        
        st.markdown("---")
        
        st.markdown("#### แนวรับ-แนวต้าน (Support & Resistance)")
        sr_r_inputs = []
        sr_s_inputs = []
        
        # 🛠️ ฟีเจอร์ 3: สัดส่วนคอลัมน์ใหม่ (เพิ่มคอลัมน์แผนซื้อไว้ซ้ายสุด)
        sr_widths = [2.5, 1.5, 1.2, 1.2, 1.2, 1.2] 
        
        r_cols = st.columns(sr_widths)
        r_cols[0].markdown("<div style='text-align:center; color:#555555; font-weight:bold;'>แผนการซื้อเพิ่ม 📝</div>", unsafe_allow_html=True)
        r_cols[1].markdown("<div style='text-align:center; color:#E2B714; font-weight:bold;'>แนวต้าน 🎯</div>", unsafe_allow_html=True)
        for i in range(4):
            # แก้บั๊ก: ใส่ {item}
            val = r_cols[i+2].text_input(f"R{i+1}", value=details['sr_r'][i], key=f"R_{item}_{i}", label_visibility="collapsed")
            sr_r_inputs.append(val)
            if val != details['sr_r'][i]: 
                details['sr_r'][i] = val
                changed = True

        for r in range(4):
            s_cols = st.columns(sr_widths)
            
            # กล่องข้อความแผนซื้อเพิ่ม
            action_val = s_cols[0].text_input(f"Action{r+1}", value=details['sr_action'][r], key=f"Action_{item}_{r}", placeholder="เช่น ไม้ 1 ซื้อ 100 หุ้น...", label_visibility="collapsed")
            if action_val != details['sr_action'][r]:
                details['sr_action'][r] = action_val
                changed = True

            # กล่องตัวเลขแนวรับ
            val = s_cols[1].text_input(f"S{r+1}", value=details['sr_s'][r], key=f"S_{item}_{r}", label_visibility="collapsed")
            sr_s_inputs.append(val)
            if val != details['sr_s'][r]: 
                details['sr_s'][r] = val
                changed = True

            # คำนวณส่วนต่าง
            s_num = get_clean_float(val)
            for c in range(4):
                r_num = get_clean_float(sr_r_inputs[c])
                if s_num == 0:
                    s_cols[c+2].markdown("<div style='text-align:center; color:#777777; padding-top:10px;'>-</div>", unsafe_allow_html=True)
                else:
                    diff = r_num - s_num
                    pct = (diff / s_num) * 100
                    sign = "+" if diff >= 0 else ""
                    color = "#02C076" if diff >= 0 else "#F6465D"
                    s_cols[c+2].markdown(f"<div style='text-align:center; color:{color}; padding-top:5px;'><b>{sign}${diff:,.0f}</b><br>({sign}{pct:.2f}%)</div>", unsafe_allow_html=True)
        
        if changed: save_data()
