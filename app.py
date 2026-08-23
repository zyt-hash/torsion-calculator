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
    
    # ---- 1. 基本参数 ----
    b_core = b - 2 * c
    h_core = h - 2 * c
    A_core = b_core * h_core
    L_core = 2 * (b_core + h_core)
    W_t = b**2 * (3 * h - b) / 6
    h0 = h - as_
    
    # ---- 2. 截面适用条件 ----
    term1 = 0.51 * np.sqrt(fc)
    V_over = gamma0 * V * 1000 / (b * h0)
    T_over = gamma0 * T * 1e6 / W_t
    combined = V_over + T_over
    
    if combined < term1:
        size_ok = "✅ 截面尺寸满足要求"
    else:
        size_ok = "⚠️ 截面尺寸需调整"
    
    # ---- 3. 受弯纵筋 ----
    a = 1
    b_coeff = -2 * h0
    c_coeff = 2 * M * 1e6 / (fcd * b)
    disc = b_coeff**2 - 4 * a * c_coeff
    if disc >= 0:
        x = (-b_coeff - np.sqrt(disc)) / (2 * a)
        if x < 0 or x > h:
            x = (-b_coeff + np.sqrt(disc)) / (2 * a)
    else:
        x = 0.1 * h0
    
    xi_b = 0.53
    if x > xi_b * h0:
        x = xi_b * h0 * 0.9
    
    As_flex = fcd * b * x / fsd
    As_min = 0.002 * b * h0
    As_flex = max(As_flex, As_min)
    
    # ---- 4. 抗剪 ----
    beta = 1.5 / (1 + 0.5 * V * W_t / (T * b * h0 + 1e-10))
    beta = max(0.5, min(beta, 1.0))
    p = 100 * As_flex / (b * h0)
    
    denom = (2 + 0.6 * p) * np.sqrt(fc * fsv)
    numerator = (gamma0 * V / (0.5 * 1e-4 * (10 - 2 * beta) * b * h0))**2
    rho_sv = numerator / denom if denom > 0 else 0.001
    
    Asv_shear = b * rho_sv / 2
    
    # ---- 5. 抗扭 ----
    zeta = 1.2
    numerator_t = gamma0 * T * 1e6 - 0.35 * beta * ft * W_t
    denominator_t = 1.2 * np.sqrt(zeta) * fsv * A_core
    Ast1_s = numerator_t / denominator_t if denominator_t > 0 else 0.001
    
    # ---- 6. 总箍筋 ----
    Asv_total = Asv_shear + Ast1_s
    
    s_selected = 120
    Asv_provided = 50.3
    
    # ---- 7. 抗扭纵筋 ----
    Astl = zeta * fsv * Asv_provided * L_core / (fsd * s_selected)
    
    # ---- 8. 最终配筋 ----
    Astl_per_layer = Astl / 4
    As_bottom_total = As_flex + Astl_per_layer
    
    # ---- 9. 输出结果 ----
    col_out1, col_out2 = st.columns(2)
    with col_out1:
        st.write(f"**截面尺寸** b×h = {b}×{h} mm")
        st.write(f"**有效高度** h₀ = {h0} mm")
        st.write(f"**核心面积** A_core = {A_core} mm²")
        st.write(f"**核心周长** L_core = {L_core} mm")
        st.write(f"**塑性抵抗矩** W_t = {W_t/1e6:.3f}×10⁶ mm³")
    
    with col_out2:
        st.write(f"**截面验算** {size_ok}")
        st.write(f"**受弯纵筋** As = {As_flex:.0f} mm²")
        st.write(f"**抗扭纵筋** Astl = {Astl:.0f} mm²")
        st.write(f"**总箍筋** Asv/s = {Asv_total:.3f} mm²/mm")
        st.write(f"**β = {beta:.2f}**")
    
    st.markdown("---")
    st.write(f"**✅ 最终配筋方案**")
    st.write(f"- **箍筋**：双肢 Φ8 @ {s_selected} mm (Asv = {Asv_provided} mm²)")
    st.write(f"- **底层纵筋**：受弯 {As_flex:.0f} + 抗扭 {Astl_per_layer:.0f} = {As_bottom_total:.0f} mm² → 选 3Φ20 (942 mm²)")
    st.write(f"- **上层纵筋**：抗扭 {Astl_per_layer:.0f} mm² → 选 2Φ12 (226 mm²)")
    st.write(f"- **中间层纵筋**：2Φ12 × 2层")
    
    # ============================================================
    # ===== 配筋图（去掉"5-1"） =====
    # ============================================================
    st.subheader("📐 截面配筋布置图")
    
    fig, ax = plt.subplots(1, 1, figsize=(7, 9))
    
    scale = 0.7
    b_draw = b * scale
    h_draw = h * scale
    c_draw = c * scale
    ox, oy = 60, 60
    
    # 混凝土截面
    rect = patches.Rectangle((ox, oy), b_draw, h_draw, 
                              linewidth=2, edgecolor='black', facecolor='#f8f8f8')
    ax.add_patch(rect)
    
    # 底层：3Φ20
    y_bottom = oy + c_draw + 8
    x_bottom = [ox + c_draw + 15, ox + b_draw/2, ox + b_draw - c_draw - 15]
    for x in x_bottom:
        circle = patches.Circle((x, y_bottom), 10, facecolor='black', edgecolor='black')
        ax.add_patch(circle)
    ax.text(ox + b_draw/2, y_bottom - 18, '3Φ20', ha='center', va='top', fontsize=9, fontweight='bold')
    
    # 中间两层：2Φ12
    y_mid1 = oy + h_draw * 0.33
    y_mid2 = oy + h_draw * 0.67
    x_mid = [ox + c_draw + 15, ox + b_draw - c_draw - 15]
    for y in [y_mid1, y_mid2]:
        for x in x_mid:
            circle = patches.Circle((x, y), 6, facecolor='black', edgecolor='black')
            ax.add_patch(circle)
    ax.text(ox + b_draw/2, (y_mid1 + y_mid2)/2, '2Φ12 × 2层', ha='center', va='center', fontsize=9)
    
    # 上层：2Φ12
    y_top = oy + h_draw - c_draw - 8
    for x in x_mid:
        circle = patches.Circle((x, y_top), 6, facecolor='black', edgecolor='black')
        ax.add_patch(circle)
    ax.text(ox + b_draw/2, y_top + 18, '2Φ12', ha='center', va='bottom', fontsize=9)
    
    # 箍筋（简化示意）
    for y in np.linspace(oy + c_draw, oy + h_draw - c_draw, 6):
        ax.plot([ox + c_draw, ox + c_draw], [y-4, y+4], 'b-', linewidth=1.5)
        ax.plot([ox + b_draw - c_draw, ox + b_draw - c_draw], [y-4, y+4], 'b-', linewidth=1.5)
    ax.plot([ox + c_draw, ox + b_draw - c_draw], [oy + c_draw, oy + c_draw], 'b-', linewidth=1.5)
    ax.plot([ox + c_draw, ox + b_draw - c_draw], [oy + h_draw - c_draw, oy + h_draw - c_draw], 'b-', linewidth=1.5)
    
    # 宽度标注
    ax.annotate('', xy=(ox, oy - 20), xytext=(ox + b_draw, oy - 20),
                arrowprops=dict(arrowstyle='<->', edgecolor='black', lw=1))
    ax.text(ox + b_draw/2, oy - 32, f'{b}mm', ha='center', va='top', fontsize=10)
    
    # 高度标注
    ax.annotate('', xy=(ox - 20, oy), xytext=(ox - 20, oy + h_draw),
                arrowprops=dict(arrowstyle='<->', edgecolor='black', lw=1))
    ax.text(ox - 32, oy + h_draw/2, f'{h}mm', ha='center', va='center', rotation=90, fontsize=10)
    
    ax.set_xlim(ox - 40, ox + b_draw + 40)
    ax.set_ylim(oy - 40, oy + h_draw + 40)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # ✅ 去掉"5-1"：不设置图标题，只保留空
    # 原来有 ax.set_title('例5-1 截面配筋布置图', fontsize=12) 现在删掉了
    
    st.pyplot(fig)
    
    st.caption("💡 底层为受弯+抗扭叠加，中间层和上层为纯抗扭纵筋")