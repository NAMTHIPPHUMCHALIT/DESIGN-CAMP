import streamlit as st
import pandas as pd
import numpy as np

# การตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Pile Foundation Design", layout="wide")

st.title("🏗️ โปรแกรมคำนวณแรงในเสาเข็ม (Eccentric Pile Load)")
st.write("คำนวณน้ำหนักลงเสาเข็มรายต้นกรณีรับโมเมนต์และน้ำหนักเยื้องศูนย์")

# --- ส่วน Input Parameters ---
with st.sidebar:
    st.header("1. ข้อมูลน้ำหนักบรรทุก (Loads)")
    V = st.number_input("น้ำหนักแนวดิ่งทั้งหมด (V) [tons]", value=100.0)
    Mx = st.number_input("โมเมนต์รอบแกน X (Mx) [t-m]", value=10.0)
    My = st.number_input("โมเมนต์รอบแกน Y (My) [t-m]", value=5.0)
    
    st.header("2. ข้อมูลฐานราก (Foundation)")
    B = st.number_input("ความกว้างฐานราก (B) [m]", value=2.5)
    L = st.number_input("ความยาวฐานราก (L) [m]", value=2.5)
    Df = st.number_input("ความลึกฐานราก (Df) [m]", value=1.5)
    pile_capacity = st.number_input("กำลังรับน้ำหนักปลอดภัยของเข็ม/ต้น [tons]", value=30.0)

# --- ส่วนการจัดการตำแหน่งเสาเข็ม ---
st.header("3. กำหนดตำแหน่งเสาเข็ม (Pile Coordinates)")
st.info("ระบุตำแหน่ง (x, y) ของเสาเข็มแต่ละต้นเทียบกับจุดศูนย์กลางของกลุ่มเสาเข็ม (Centroid)")

num_piles = st.number_input("จำนวนเสาเข็ม (ต้น)", min_value=1, value=4)

# สร้างตาราง Input สำหรับตำแหน่งเข็ม
pile_data = []
cols = st.columns(2)
for i in range(num_piles):
    with cols[0 if i < num_piles/2 else 1]:
        st.subheader(f"เสาเข็มต้นที่ {i+1}")
        x = st.number_input(f"พิกัด x ตันที่ {i+1} [m]", value=0.75 if i % 2 == 0 else -0.75, key=f"x{i}")
        y = st.number_input(f"พิกัด y ตันที่ {i+1} [m]", value=0.75 if i < num_piles/2 else -0.75, key=f"y{i}")
        pile_data.append({'Pile No.': i+1, 'x': x, 'y': y})

df_piles = pd.DataFrame(pile_data)

# --- ส่วนการคำนวณ ---
if st.button("ประมวลผลการคำนวณ"):
    # คำนวณผลรวมกำลังสองของระยะทาง
    sum_x2 = (df_piles['x']**2).sum()
    sum_y2 = (df_piles['y']**2).sum()
    
    # คำนวณแรงลงเข็มรายต้น
    # P = V/n + (Mx*y / sum_y2) + (My*x / sum_x2)
    df_piles['Load (tons)'] = (V / num_piles) + \
                              (Mx * df_piles['y'] / sum_y2 if sum_y2 != 0 else 0) + \
                              (My * df_piles['x'] / sum_x2 if sum_x2 != 0 else 0)
    
    # ตรวจสอบการผ่านเงื่อนไข
    df_piles['Status'] = df_piles['Load (tons)'].apply(lambda x: "✅ Pass" if x <= pile_capacity else "❌ Overloaded")

    # --- แสดงผลลัพธ์ ---
    st.divider()
    col_res1, col_res2 = st.columns([1, 1])
    
    with col_res1:
        st.subheader("📊 ตารางสรุปผลแรงในเสาเข็ม")
        st.dataframe(df_piles.style.highlight_max(axis=0, subset=['Load (tons)'], color='#ff4b4b66'))
        
        max_load = df_piles['Load (tons)'].max()
        min_load = df_piles['Load (tons)'].min()
        
        st.metric("แรงสูงสุด (Max Load)", f"{max_load:.2f} tons")
        st.metric("แรงต่ำสุด (Min Load)", f"{min_load:.2f} tons")

    with col_res2:
        st.subheader("📍 ผังตำแหน่งเสาเข็ม")
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots()
        ax.scatter(df_piles['x'], df_piles['y'], s=500, c='brown', alpha=0.6)
        for i, txt in enumerate(df_piles['Pile No.']):
            ax.annotate(txt, (df_piles['x'][i], df_piles['y'][i]), ha='center', va='center', color='white', weight='bold')
        
        # วาดขอบเขตฐานราก
        rect = plt.Rectangle((-L/2, -B/2), L, B, linewidth=2, edgecolor='black', facecolor='none', linestyle='--')
        ax.add_patch(rect)
        
        ax.set_xlabel("Distance X (m)")
        ax.set_ylabel("Distance Y (m)")
        ax.axhline(0, color='black', lw=1)
        ax.axvline(0, color='black', lw=1)
        ax.grid(True, linestyle=':')
        st.pyplot(fig)

    if max_load > pile_capacity:
        st.error(f"⚠️ คำเตือน: แรงสูงสุด ({max_load:.2f} t) เกินกว่ากำลังรับน้ำหนักของเสาเข็มที่ยอมรับได้ ({pile_capacity} t)!")
    else:
        st.success("✅ เสาเข็มทุกต้นสามารถรับน้ำหนักได้ปลอดภัย")
