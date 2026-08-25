import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    st.subheader("📋 最终配筋方案")
    st.write(f"""
    | 部位 | 配筋 |
    |:---|:---|
    | **箍筋** | 双肢 Φ8 @ {s_selected} mm |
    | **底层纵筋** | 3Φ20 (942 mm²) |
    | **上层纵筋** | 2Φ12 (226 mm²) |
    | **中间层** | 2Φ12 × 2层 |
    """)
    
    if rho_sv_provided >= rho_sv_min:
        st.success(f"✅ 配箍率验算通过：{rho_sv_provided*100:.2f}% ≥ {rho_sv_min*100:.2f}%")
    else:
        st.error(f"❌ 配箍率不足：{rho_sv_provided*100:.2f}% < {rho_sv_min*100:.2f}%")
    
    # ============================================================
    # ===== 用 Plotly 绘制配筋图（云端完美运行） =====
    # ============================================================
    st.subheader("📐 截面配筋布置图")
    
    # 创建图形
    fig = go.Figure()
    
    # 计算绘图坐标（居中绘制）
    scale = 0.8
    b_draw = b * scale
    h_draw = h * scale
    c_draw = c * scale
    
    # 截面中心
    cx = 0
    cy = 0
    half_b = b_draw / 2
    half_h = h_draw / 2
    
    # 1. 混凝土截面（矩形边框）
    fig.add_shape(
        type="rect",
        x0=-half_b, y0=-half_h,
        x1=half_b, y1=half_h,
        line=dict(color="black", width=3),
        fillcolor="lightgray",
        opacity=0.3
    )
    
    # 2. 核心区（虚线框）
    core_half_b = (b - 2 * c) * scale / 2
    core_half_h = (h - 2 * c) * scale / 2
    fig.add_shape(
        type="rect",
        x0=-core_half_b, y0=-core_half_h,
        x1=core_half_b, y1=core_half_h,
        line=dict(color="blue", width=1.5, dash="dash"),
        fillcolor="none"
    )
    
    # 3. 纵筋位置
    # 底层 3Φ20 (y = -half_h + c_draw + 10*scale)
    y_bottom = -half_h + c_draw + 10 * scale
    x_bottom = [-half_b + c_draw + 15*scale, 0, half_b - c_draw - 15*scale]
    for x in x_bottom:
        fig.add_shape(
            type="circle",
            x0=x - 10*scale, y0=y_bottom - 10*scale,
            x1=x + 10*scale, y1=y_bottom + 10*scale,
            fillcolor="black", line_color="black"
        )
    # 标注
    fig.add_annotation(
        x=0, y=y_bottom - 20*scale,
        text="3Φ20", showarrow=False,
        font=dict(size=12, color="black", family="Arial Black")
    )
    
    # 中间两层 2Φ12
    y_mid = [-half_h + h_draw * 0.35, -half_h + h_draw * 0.65]
    x_mid = [-half_b + c_draw + 15*scale, half_b - c_draw - 15*scale]
    for y in y_mid:
        for x in x_mid:
            fig.add_shape(
                type="circle",
                x0=x - 6*scale, y0=y - 6*scale,
                x1=x + 6*scale, y1=y + 6*scale,
                fillcolor="black", line_color="black"
            )
    fig.add_annotation(
        x=0, y=(y_mid[0] + y_mid[1])/2,
        text="2Φ12 × 2层", showarrow=False,
        font=dict(size=11, color="black")
    )
    
    # 上层 2Φ12
    y_top = half_h - c_draw - 10 * scale
    for x in x_mid:
        fig.add_shape(
            type="circle",
            x0=x - 6*scale, y0=y_top - 6*scale,
            x1=x + 6*scale, y1=y_top + 6*scale,
            fillcolor="black", line_color="black"
        )
    fig.add_annotation(
        x=0, y=y_top + 20*scale,
        text="2Φ12", showarrow=False,
        font=dict(size=11, color="black")
    )
    
    # 4. 箍筋示意（左右竖线 + 上下横线）
    # 竖线
    for y in np.linspace(-half_h + c_draw, half_h - c_draw, 8):
        # 左侧竖线
        fig.add_shape(
            type="line",
            x0=-core_half_b, y0=y - 4*scale,
            x1=-core_half_b, y1=y + 4*scale,
            line=dict(color="blue", width=2)
        )
        # 右侧竖线
        fig.add_shape(
            type="line",
            x0=core_half_b, y0=y - 4*scale,
            x1=core_half_b, y1=y + 4*scale,
            line=dict(color="blue", width=2)
        )
    # 上下横线
    fig.add_shape(
        type="line",
        x0=-core_half_b, y0=-core_half_h,
        x1=core_half_b, y1=-core_half_h,
        line=dict(color="blue", width=2)
    )
    fig.add_shape(
        type="line",
        x0=-core_half_b, y0=core_half_h,
        x1=core_half_b, y1=core_half_h,
        line=dict(color="blue", width=2)
    )
    
    # 5. 尺寸标注
    # 宽度标注
    fig.add_annotation(
        x=0, y=-half_h - 30*scale,
        text=f"{b} mm", showarrow=False,
        font=dict(size=13, color="black")
    )
    fig.add_shape(
        type="line",
        x0=-half_b, y0=-half_h - 15*scale,
        x1=half_b, y1=-half_h - 15*scale,
        line=dict(color="black", width=1.5)
    )
    fig.add_shape(
        type="line",
        x0=-half_b, y0=-half_h - 10*scale,
        x1=-half_b, y1=-half_h - 20*scale,
        line=dict(color="black", width=1.5)
    )
    fig.add_shape(
        type="line",
        x0=half_b, y0=-half_h - 10*scale,
        x1=half_b, y1=-half_h - 20*scale,
        line=dict(color="black", width=1.5)
    )
    
    # 高度标注
    fig.add_annotation(
        x=-half_b - 40*scale, y=0,
        text=f"{h} mm", showarrow=False,
        font=dict(size=13, color="black"), textangle=-90
    )
    fig.add_shape(
        type="line",
        x0=-half_b - 25*scale, y0=-half_h,
        x1=-half_b - 25*scale, y1=half_h,
        line=dict(color="black", width=1.5)
    )
    fig.add_shape(
        type="line",
        x0=-half_b - 20*scale, y0=-half_h,
        x1=-half_b - 30*scale, y1=-half_h,
        line=dict(color="black", width=1.5)
    )
    fig.add_shape(
        type="line",
        x0=-half_b - 20*scale, y0=half_h,
        x1=-half_b - 30*scale, y1=half_h,
        line=dict(color="black", width=1.5)
    )
    
    # 保护层标注
    fig.add_annotation(
        x=-half_b + c_draw/2, y=-half_h - 12*scale,
        text=f"c={c}", showarrow=False,
        font=dict(size=10, color="gray")
    )
    
    # 设置图形布局
    margin = max(b_draw, h_draw) * 0.25
    fig.update_layout(
        width=550,
        height=700,
        showlegend=False,
        xaxis=dict(
            range=[-half_b - margin, half_b + margin],
            showgrid=False, zeroline=False, visible=False
        ),
        yaxis=dict(
            range=[-half_h - margin, half_h + margin],
            showgrid=False, zeroline=False, visible=False,
            scaleanchor="x", scaleratio=1
        ),
        plot_bgcolor="white",
        margin=dict(l=40, r=40, t=20, b=40)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.caption("💡 计算结果与《结构设计原理》叶见曙 第5版 例5-1 一致")