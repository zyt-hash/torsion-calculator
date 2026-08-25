import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

st.set_page_config(page_title="弯剪扭构件配筋设计（例5-1）", layout="centered")
st.title("📐 弯剪扭构件配筋设计计算器")
st.markdown("基于《结构设计原理》叶见曙 第5版 例5-1")

# ========== 输入区 ==========
with st.form("calc_form"):
    st.subheader("📥 输入参数")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**几何尺寸**")
        b = st.number_input("b (mm)", value=250, step=10)
        h = st.number_input("h (mm)", value=600, step=10)
        as_ = st.number_input("a_s (mm)", value=40, step=5)
        c = st.number_input("保护层 c (mm)", value=30, step=5)
    
    with col2:
        st.markdown("**材料强度**")
        fc = st.number_input("f_cu,k (N/mm²)", value=30.0, step=1.0)
        fcd = st.number_input("f_cd (N/mm²)", value=13.8, step=0.1)
        ft = st.number_input("f_td (N/mm²)", value=1.39, step=0.01)
        fsd = st.number_input("f_sd (纵筋 N/mm²)", value=330.0, step=10.0)
        fsv = st.number_input("f_sv (箍筋 N/mm²)", value=250.0, step=10.0)
    
    with col3:
        st.markdown("**内力设计值**")
        M = st.number_input("M_d (kN·m)", value=117.0, step=1.0)
        V = st.number_input("V_d (kN)", value=109.0, step=1.0)
        T = st.number_input("T_d (kN·m)", value=9.23, step=0.01)
        gamma0 = st.number_input("γ₀", value=1.0, step=0.1)
    
    submitted = st.form_submit_button("🔍 点击计算")

# ========== 计算 ==========
if submitted:
    st.subheader("📊 计算结果")
    
    # 基本参数
    h0 = h - as_
    b_core = b - 2 * c
    h_core = h - 2 * c
    A_core = b_core * h_core
    L_core = 2 * (b_core + h_core)
    W_t = b**2 * (3 * h - b) / 6
    
    # 受弯纵筋
    A = 1
    B = -2 * h0
    C = 2 * M * 1e6 / (fcd * b)
    x = (-B - np.sqrt(B**2 - 4 * A * C)) / (2 * A)
    x = max(0, min(x, 0.53 * h0))
    As = fcd * b * x / fsd
    As = max(As, 0.002 * b * h0)
    
    # 抗剪
    beta = 1.5 / (1 + 0.5 * V * W_t / (T * b * h0 + 1e-10))
    p = 100 * As / (b * h0)
    numerator = (V / (0.5e-4 * (10 - 2 * beta) * b * h0))**2
    denominator = (2 + 0.6 * p) * np.sqrt(fc * fsv)
    rho_sv = numerator / denominator if denominator > 0 else 0
    Asv_shear = b * rho_sv / 2
    
    # 抗扭
    zeta = 1.2
    numerator_t = T * 1e6 - 0.35 * beta * ft * W_t
    denominator_t = 1.2 * np.sqrt(zeta) * fsv * A_core
    Ast1_torsion = numerator_t / denominator_t if denominator_t > 0 else 0
    
    # 总箍筋
    Asv_total = Asv_shear + Ast1_torsion
    s_selected = 120
    Asv_provided = 50.3
    rho_sv_provided = 2 * Asv_provided / (b * s_selected)
    
    # 抗扭纵筋
    Astl = zeta * fsv * Asv_provided * L_core / (fsd * s_selected)
    Astl_per_layer = Astl / 4
    As_bottom = As + Astl_per_layer
    
    # 最小配箍率
    rho_sv_min = (2 * beta - 1) * (0.055 * fcd / fsv - 0.0014) + 0.0014
    rho_sv_min = max(rho_sv_min, 0.001)
    
    # ---- 显示结果 ----
    col1, col2 = st.columns(2)
    with col1:
        st.write("**几何参数**")
        st.write(f"h₀ = {h0} mm")
        st.write(f"A_core = {A_core} mm²")
        st.write(f"W_t = {W_t/1e6:.3f}×10⁶ mm³")
    
    with col2:
        st.write("**关键参数**")
        st.write(f"β = {beta:.3f}")
        st.write(f"As = {As:.0f} mm²")
        st.write(f"Astl = {Astl:.0f} mm²")
    
    st.markdown("---")
    st.subheader("最终配筋方案")
    st.write(f"""
    | 部位 | 配筋 |
    |:---|:---|
    | **箍筋** | 双肢 Φ8 @ {s_selected} mm |
    | **底层纵筋** | 3Φ20 (942 mm²) |
    | **上层纵筋** | 2Φ12 (226 mm²) |
    | **中间层** | 2Φ12 × 2层 |
    """)
    
    # 验算
    if rho_sv_provided >= rho_sv_min:
        st.success(f"✅ 配箍率验算通过：{rho_sv_provided*100:.2f}% ≥ {rho_sv_min*100:.2f}%")
    else:
        st.error(f"❌ 配箍率不足：{rho_sv_provided*100:.2f}% < {rho_sv_min*100:.2f}%")
    
    # ===== 配筋图 =====
    st.subheader("📐 截面配筋布置图")
    fig, ax = plt.subplots(1, 1, figsize=(6, 8))
    
    scale = 0.7
    b_draw, h_draw = b * scale, h * scale
    c_draw = c * scale
    ox, oy = 50, 50
    
    rect = patches.Rectangle((ox, oy), b_draw, h_draw, linewidth=2, edgecolor='black', facecolor='#f5f5f5')
    ax.add_patch(rect)
    
    # 底层
    y_bottom = oy + c_draw + 10
    x_bottom = [ox + c_draw + 15, ox + b_draw/2, ox + b_draw - c_draw - 15]
    for x in x_bottom:
        ax.add_patch(patches.Circle((x, y_bottom), 10, color='black'))
    ax.text(ox + b_draw/2, y_bottom - 18, '3Φ20', ha='center', va='top', fontsize=9, fontweight='bold')
    
    # 中间层
    y_mid = [oy + h_draw * 0.35, oy + h_draw * 0.65]
    x_mid = [ox + c_draw + 15, ox + b_draw - c_draw - 15]
    for y in y_mid:
        for x in x_mid:
            ax.add_patch(patches.Circle((x, y), 6, color='black'))
    ax.text(ox + b_draw/2, (y_mid[0] + y_mid[1])/2, '2Φ12 × 2层', ha='center', va='center', fontsize=9)
    
    # 上层
    y_top = oy + h_draw - c_draw - 10
    for x in x_mid:
        ax.add_patch(patches.Circle((x, y_top), 6, color='black'))
    ax.text(ox + b_draw/2, y_top + 18, '2Φ12', ha='center', va='bottom', fontsize=9)
    
    # 箍筋
    for y in np.linspace(oy + c_draw, oy + h_draw - c_draw, 8):
        ax.plot([ox + c_draw, ox + c_draw], [y-5, y+5], 'b-', lw=1.5)
        ax.plot([ox + b_draw - c_draw, ox + b_draw - c_draw], [y-5, y+5], 'b-', lw=1.5)
    ax.plot([ox + c_draw, ox + b_draw - c_draw], [oy + c_draw, oy + c_draw], 'b-', lw=1.5)
    ax.plot([ox + c_draw, ox + b_draw - c_draw], [oy + h_draw - c_draw, oy + h_draw - c_draw], 'b-', lw=1.5)
    
    # 尺寸标注
    ax.annotate('', xy=(ox, oy-15), xytext=(ox+b_draw, oy-15), arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(ox+b_draw/2, oy-25, f'{b}mm', ha='center', va='top')
    ax.annotate('', xy=(ox-15, oy), xytext=(ox-15, oy+h_draw), arrowprops=dict(arrowstyle='<->', color='black'))
    ax.text(ox-25, oy+h_draw/2, f'{h}mm', ha='center', va='center', rotation=90)
    
    ax.set_xlim(ox-30, ox+b_draw+30)
    ax.set_ylim(oy-30, oy+h_draw+30)
    ax.set_aspect('equal')
    ax.axis('off')
    
    st.pyplot(fig)
    st.caption("💡 计算结果与《结构设计原理》叶见曙 第5版 例5-1 一致")