import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# การตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Pile Load Calculator", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🏗️ Pile Foundation Design Tool")
st.write("เครื่องมือคำนวณแรงในเสาเข็มรายต้น กรณีรับโมเมนต์และแรงเยื้องศูนย์")

# --- ส่วน Input ---
with st.sidebar:
    st.header("1. น้ำหนักบรรทุก (Loads)")
    V_service = st.number_input("น้ำหนักบรรทุกจากเสา (V) [tons]", value=80.0)
    Mx_ext = st.number_input("โมเมนต์ภายนอกแกน X (Mx) [t-m]", value=0.0)
    My_ext = st.number_input("โมเมนต์ภายนอกแกน Y (My) [t-m]", value=0.0)
    
    st.header("2. ขนาดฐานราก & เสาตอม่อ")
    B = st.number_input("ความกว้างฐานราก (B) [m]", value=2.0)
    L = st.number_input("ความยาวฐานราก (L) [m]", value=2.0)
    Df = st.number_input("ความหนาฐานราก (Df) [m]", value=0.6)
    
    st.subheader("ตำแหน่งเสาตอม่อ (Offset)")
    ex = st.number_input("ระยะเยื้องแกน X (ex) [m]", value=0.0, help="ระยะจากศูนย์กลางฐานถึงกึ่งกลางเสาตอม่อ")
    ey = st.number_input("ระยะเยื้องแกน Y (ey) [m]", value=0.0)

    st.header("3. คุณสมบัติเสาเข็ม")
    num_piles = st.number_input("จำนวนเสาเข็ม (ต้น)", min_value=1, value=4)
    pile_safe_load = st.number_input("Allowable Load/Pile [tons]", value=25.0)

# --- ส่วนกำหนดพิกัดเสาเข็ม ---
st.subheader("📍 กำหนดพิกัดเสาเข็ม (Pile Coordinates)")
st.caption("ระบุระยะ x, y เทียบกับจุดศูนย์กลางฐานราก (0,0)")

pile_coords = []
col_p1, col_p2, col_p3 = st.columns(3)

for i in range(num_piles):
    with [col_p1, col_p2, col_p3][i % 3]:
        st.markdown(f"**เสาเข็มต้นที่ {i+1}**")
        px = st.number_input(f"พิกัด x [{i+1}]", value=0.6 if i%2==0 else -0.6, key=f"px{i}")
        py = st.number_input(f"พิกัด y [{i+1}]", value=0.6 if i<num_piles/2 else -0.6, key=f"py{i}")
        pile_coords.append({'Pile No.': i+1, 'x': px, 'y': py})

# --- ส่วนประมวลผล ---
if st.button("เริ่มการคำนวณ", type="primary", use_container_width=True):
    # 1. คำนวณน้ำหนักฐานราก (Self-weight)
    self_weight = B * L * Df * 2.4  # หน่วย tons (คอนกรีตเสริมเหล็ก 2.4 t/m3)
    V_total = V_service + self_weight
    
    # 2. คำนวณโมเมนต์สุทธิ (Net Moment) รวมถึงที่เกิดจากแรงเยื้องศูนย์
    M_net_x = Mx_ext + (V_service * ey)
    M_net_y = My_ext + (V_service * ex)
    
    # 3. คำนวณคุณสมบัติกลุ่มเข็ม
    df = pd.DataFrame(pile_coords)
    sum_x2 = (df['x']**2).sum()
    sum_y2 = (df['y']**2).sum()
    
    # 4. คำนวณแรงในเข็มแต่ละต้น
    # P = V/n + (Mx*y / sum_y2) + (My*x / sum_x2)
    df['Load (tons)'] = (V_total / num_piles) + \
                        (M_net_x * df['y'] / sum_y2 if sum_y2 != 0 else 0) + \
                        (M_net_y * df['x'] / sum_x2 if sum_x2 != 0 else 0)
    
    df['Status'] = df['Load (tons)'].apply(lambda x: "✅ ผ่าน" if x <= pile_safe_load else "❌ เกิน")

    # --- แสดงผลลัพธ์ ---
    st.divider()
    res_col1, res_col2 = st.columns([6, 4])
    
    with res_col1:
        st.subheader("📝 ผลการคำนวณ")
        st.write(f"**น้ำหนักรวม (V + Self weight):** {V_total:.2f} tons")
        st.dataframe(df.style.background_gradient(subset=['Load (tons)'], cmap='YlOrRd'), use_container_width=True)
        
        max_p = df['Load (tons)'].max()
        if max_p > pile_safe_load:
            st.error(f"แรงสูงสุด {max_p:.2f} tons เกินกำลังเข็ม!")
        else:
            st.success(f"แรงสูงสุด {max_p:.2f} tons ปลอดภัย")

    with res_col2:
        st.subheader("🖼️ ผังการจัดวาง")
        fig, ax = plt.subplots(figsize=(5,5))
        ax.scatter(df['x'], df['y'], s=400, c='#1f77b4', edgecolors='white', zorder=3)
        for i, row in df.iterrows():
            ax.annotate(int(row['Pile No.']), (row['x'], row['y']), ha='center', va='center', color='white', weight='bold')
        
        # วาดเสาตอม่อ (Column)
        ax.scatter(ex, ey, s=200, c='red', marker='s', label='Column', zorder=4)
        # วาดขอบฐานราก
        rect = plt.Rectangle((-L/2, -B/2), L, B, linewidth=1.5, edgecolor='#333', facecolor='#eee', zorder=1)
        ax.add_patch(rect)
        
        ax.axhline(0, color='black', lw=0.5, ls='--')
        ax.axvline(0, color='black', lw=0.5, ls='--')
        ax.set_xlim(-L, L); ax.set_ylim(-B, B)
        ax.set_aspect('equal')
        ax.legend()
        st.pyplot(fig)
