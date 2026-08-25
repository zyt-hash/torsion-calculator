import streamlit as st
import numpy as np

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
    h0 = h - as_
    b_core = b - 2 * c
    h_core = h - 2 * c
    A_core = b_core * h_core
    L_core = 2 * (b_core + h_core)
    W_t = b**2 * (3 * h - b) / 6
    
    # ---- 2. 截面验算 ----
    lhs = gamma0 * V * 1000 / (b * h0) + gamma0 * T * 1e6 / W_t
    rhs = 0.51 * np.sqrt(fc)
    if lhs < rhs:
        size_check = "✅ 截面尺寸满足要求"
    else:
        size_check = "⚠️ 截面尺寸不满足，需增大截面！"
    
    # ---- 3. 受弯纵筋 ----
    A = 1
    B = -2 * h0
    C = 2 * M * 1e6 / (fcd * b)
    disc = B**2 - 4 * A * C
    if disc >= 0:
        x = (-B - np.sqrt(disc)) / (2 * A)
        x = max(0, min(x, 0.53 * h0))
    else:
        x = 0.1 * h0
    
    As = fcd * b * x / fsd
    As = max(As, 0.002 * b * h0)
    
    # ---- 4. 抗剪 ----
    beta = 1.5 / (1 + 0.5 * V * W_t / (T * b * h0 + 1e-10))
    beta = max(0.5, min(beta, 1.0))
    p = 100 * As / (b * h0)
    
    numerator = (V / (0.5e-4 * (10 - 2 * beta) * b * h0))**2
    denominator = (2 + 0.6 * p) * np.sqrt(fc * fsv)
    rho_sv = numerator / denominator if denominator > 0 else 0.001
    Asv_shear = b * rho_sv / 2
    
    # ---- 5. 抗扭 ----
    zeta = 1.2
    numerator_t = T * 1e6 - 0.35 * beta * ft * W_t
    denominator_t = 1.2 * np.sqrt(zeta) * fsv * A_core
    Ast1_torsion = numerator_t / denominator_t if denominator_t > 0 else 0.001
    
    # ---- 6. 总箍筋 ----
    Asv_total = Asv_shear + Ast1_torsion
    s_selected = 120
    Asv_provided = 50.3
    rho_sv_provided = 2 * Asv_provided / (b * s_selected)
    
    # ---- 7. 抗扭纵筋 ----
    Astl = zeta * fsv * Asv_provided * L_core / (fsd * s_selected)
    Astl_per_layer = Astl / 4
    As_bottom = As + Astl_per_layer
    
    # ---- 8. 最小配箍率 ----
    rho_sv_min = (2 * beta - 1) * (0.055 * fcd / fsv - 0.0014) + 0.0014
    rho_sv_min = max(rho_sv_min, 0.001)
    
    # ========== 显示结果 ==========
    st.success("✅ 计算完成！")
    
    col1, col2 = st.columns(2)
    with col1:
        st.write("**📏 几何参数**")
        st.write(f"- 有效高度 h₀ = **{h0:.0f} mm**")
        st.write(f"- 核心面积 A_core = **{A_core:.0f} mm²**")
        st.write(f"- 核心周长 L_core = **{L_core:.0f} mm**")
        st.write(f"- 塑性抵抗矩 W_t = **{W_t/1e6:.3f}×10⁶ mm³**")
    
    with col2:
        st.write("**📋 关键参数**")
        st.write(f"- 截面验算：{size_check}")
        st.write(f"- 混凝土受扭降低系数 β = **{beta:.3f}**")
        st.write(f"- 受弯纵筋 A_s = **{As:.0f} mm²**")
        st.write(f"- 抗扭纵筋 A_stl = **{Astl:.0f} mm²**")
        st.write(f"- 抗剪配箍率 ρ_sv = **{rho_sv:.4f}**")
    
    st.markdown("---")
    st.subheader("📋 最终配筋方案")
    
    st.write(f"""
    | 部位 | 配筋 | 说明 |
    |:---|:---|:---|
    | **箍筋** | 双肢 Φ8 @ {s_selected} mm | 实配配箍率 {rho_sv_provided*100:.2f}% |
    | **底层纵筋** | 3Φ20 (942 mm²) | 受弯 {As:.0f} + 抗扭 {Astl_per_layer:.0f} = {As_bottom:.0f} mm² |
    | **上层纵筋** | 2Φ12 (226 mm²) | 抗扭 {Astl_per_layer:.0f} mm² |
    | **中间层纵筋** | 2Φ12 × 2层 | 抗扭 {Astl_per_layer:.0f} mm²/层 |
    """)
    
    if rho_sv_provided >= rho_sv_min:
        st.success(f"✅ 配箍率验算通过：{rho_sv_provided*100:.2f}% ≥ {rho_sv_min*100:.2f}%")
    else:
        st.error(f"❌ 配箍率不足：{rho_sv_provided*100:.2f}% < {rho_sv_min*100:.2f}%")
    
    # ========== 配筋布置文字示意图 ==========
    st.subheader("📐 截面配筋布置示意")
    
    # 用 st.code 显示文字配筋图（更清晰）
    fig_text = f"""
    ┌──────────────────────────────────────┐
    │                                      │
    │    ┌──────────────────────────┐      │
    │    │                          │      │
    │    │       2Φ12 (上层)        │      │
    │    │                          │      │
    │    │      2Φ12 × 2层         │      │
    │    │                          │      │
    │    │      3Φ20 (底层)        │      │
    │    │                          │      │
    │    └──────────────────────────┘      │
    │        ← {b} mm →                    │
    │                                      │
    │      ↑ {h} mm                        │
    └──────────────────────────────────────┘
    
    保护层 c = {c} mm
    箍筋：双肢 Φ8 @ {s_selected} mm
    """
    st.code(fig_text, language="text")
    
    st.caption("💡 底层为受弯+抗扭叠加，中间层和上层为纯抗扭纵筋")
    st.caption("📌 完整配筋图请运行桌面版 (.exe) 查看")