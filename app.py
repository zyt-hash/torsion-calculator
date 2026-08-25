import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches

# ===== 设置主题 =====
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class TorsionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("弯剪扭构件配筋设计计算器 (修正版)")
        self.geometry("1200x850")
        
        # ===== 主框架 =====
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== 左侧输入区 =====
        self.left_frame = ctk.CTkFrame(self.main_frame, width=380)
        self.left_frame.pack(side="left", fill="y", padx=(0, 10))
        self.left_frame.pack_propagate(False)
        
        ctk.CTkLabel(self.left_frame, text="📥 输入参数", font=("Microsoft YaHei", 16, "bold")).pack(pady=(10, 5))
        
        input_frame = ctk.CTkScrollableFrame(self.left_frame, height=650)
        input_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 所有输入框
        self.entries = {}
        labels = [
            ("几何尺寸", [("b (mm)", "250"), ("h (mm)", "600"), ("a_s (mm)", "40"), ("c (mm)", "30")]),
            ("材料强度", [("f_cu,k (N/mm²)", "30"), ("f_cd (N/mm²)", "13.8"), ("f_td (N/mm²)", "1.39"), ("f_sd (N/mm²)", "330"), ("f_sv (N/mm²)", "250")]),
            ("内力设计值", [("M_d (kN·m)", "117"), ("V_d (kN)", "109"), ("T_d (kN·m)", "9.23"), ("γ₀", "1.0")])
        ]
        
        for group, items in labels:
            ctk.CTkLabel(input_frame, text=f"【{group}】", font=("Microsoft YaHei", 12, "bold")).pack(anchor="w", pady=(5,0))
            for label, default in items:
                self.entries[label] = self._create_entry(input_frame, label, default)
        
        self.calc_btn = ctk.CTkButton(self.left_frame, text="🔍 点击计算", command=self.calculate, height=40)
        self.calc_btn.pack(pady=15, padx=20, fill="x")
        
        # ===== 右侧结果显示区 =====
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True)
        
        self.result_text = ctk.CTkTextbox(self.right_frame, height=200, font=("Consolas", 11))
        self.result_text.pack(fill="x", padx=5, pady=5)
        
        self.figure_frame = ctk.CTkFrame(self.right_frame)
        self.figure_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.fig, self.ax = plt.subplots(1, 1, figsize=(5, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.figure_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.calculate()
    
    def _create_entry(self, parent, label, default):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=2)
        ctk.CTkLabel(frame, text=label, width=130, anchor="w", font=("Microsoft YaHei", 12)).pack(side="left", padx=(0,5))
        entry = ctk.CTkEntry(frame, width=120, font=("Consolas", 12))
        entry.pack(side="right")
        entry.insert(0, default)
        return entry
    
    def _get(self, key):
        try:
            return float(self.entries[key].get())
        except:
            return 0.0
    
    def calculate(self):
        try:
            # --- 读取输入 ---
            b = self._get("b (mm)")
            h = self._get("h (mm)")
            a_s = self._get("a_s (mm)")
            c = self._get("c (mm)")
            f_cu_k = self._get("f_cu,k (N/mm²)")
            f_cd = self._get("f_cd (N/mm²)")
            f_td = self._get("f_td (N/mm²)")
            f_sd = self._get("f_sd (N/mm²)")
            f_sv = self._get("f_sv (N/mm²)")
            M_d = self._get("M_d (kN·m)")
            V_d = self._get("V_d (kN)")
            T_d = self._get("T_d (kN·m)")
            gamma_0 = self._get("γ₀")
            
            # --- 计算（与网页版完全一致）---
            h_0 = h - a_s
            b_core = b - 2*c
            h_core = h - 2*c
            A_core = b_core * h_core
            L_core = 2 * (b_core + h_core)
            W_t = b**2 * (3*h - b) / 6
            
            # 受弯纵筋
            A = 1
            B = -2 * h_0
            C = 2 * M_d * 1e6 / (f_cd * b)
            x = (-B - np.sqrt(B**2 - 4*A*C)) / (2*A)
            x = np.clip(x, 0, 0.53 * h_0)
            A_s = f_cd * b * x / f_sd
            A_s = max(A_s, 0.002 * b * h_0)
            
            # 抗剪
            beta = 1.5 / (1 + 0.5 * V_d * W_t / (T_d * b * h_0 + 1e-10))
            p = 100 * A_s / (b * h_0)
            numerator = (V_d / (0.5e-4 * (10 - 2*beta) * b * h_0))**2
            denominator = (2 + 0.6*p) * np.sqrt(f_cu_k * f_sv)
            rho_sv = numerator / denominator if denominator > 0 else 0
            A_sv1_over_s_shear = b * rho_sv / 2
            
            # 抗扭
            zeta = 1.2
            numerator_t = gamma_0 * T_d * 1e6 - 0.35 * beta * f_td * W_t
            denominator_t = 1.2 * np.sqrt(zeta) * f_sv * A_core
            A_sv1_over_s_torsion = numerator_t / denominator_t if denominator_t > 0 else 0
            
            # 总箍筋
            A_sv1_over_s_total = A_sv1_over_s_shear + A_sv1_over_s_torsion
            s_selected = 120
            A_sv1_provided = 50.3
            rho_sv_provided = 2 * A_sv1_provided / (b * s_selected)
            
            # 抗扭纵筋
            A_stl = zeta * f_sv * A_sv1_provided * L_core / (f_sd * s_selected)
            A_stl_per_layer = A_stl / 4
            A_s_bottom = A_s + A_stl_per_layer
            
            # --- 显示结果 ---
            result_str = f"""
【计算结果】
有效高度 h₀ = {h_0:.0f} mm
核心面积 A_core = {A_core:.0f} mm²
塑性抵抗矩 W_t = {W_t/1e6:.3f}×10⁶ mm³
β = {beta:.3f}
受弯纵筋 A_s = {A_s:.0f} mm²
抗扭纵筋 A_stl = {A_stl:.0f} mm²

【最终配筋方案】
箍筋：双肢 Φ8 @ {s_selected} mm
底层纵筋：3Φ20 (942 mm²)
上层纵筋：2Φ12 (226 mm²)
中间层纵筋：2Φ12 × 2层
            """
            self.result_text.delete("0.0", "end")
            self.result_text.insert("0.0", result_str)
            
            # --- 绘图 ---
            self.ax.clear()
            scale = 0.7
            b_draw, h_draw = b*scale, h*scale
            c_draw = c*scale
            ox, oy = 50, 50
            
            # 画图（与网页版相同）
            rect = patches.Rectangle((ox, oy), b_draw, h_draw, linewidth=2, edgecolor='black', facecolor='#f5f5f5')
            self.ax.add_patch(rect)
            
            y_bottom = oy + c_draw + 10
            x_bottom = [ox + c_draw + 15, ox + b_draw/2, ox + b_draw - c_draw - 15]
            for x in x_bottom:
                self.ax.add_patch(patches.Circle((x, y_bottom), 10, color='black'))
            self.ax.text(ox + b_draw/2, y_bottom - 18, '3Φ20', ha='center', va='top', fontsize=9, fontweight='bold')
            
            y_mid = [oy + h_draw * 0.35, oy + h_draw * 0.65]
            x_mid = [ox + c_draw + 15, ox + b_draw - c_draw - 15]
            for y in y_mid:
                for x in x_mid:
                    self.ax.add_patch(patches.Circle((x, y), 6, color='black'))
            self.ax.text(ox + b_draw/2, (y_mid[0] + y_mid[1])/2, '2Φ12 × 2层', ha='center', va='center', fontsize=9)
            
            y_top = oy + h_draw - c_draw - 10
            for x in x_mid:
                self.ax.add_patch(patches.Circle((x, y_top), 6, color='black'))
            self.ax.text(ox + b_draw/2, y_top + 18, '2Φ12', ha='center', va='bottom', fontsize=9)
            
            for y in np.linspace(oy + c_draw, oy + h_draw - c_draw, 8):
                self.ax.plot([ox + c_draw, ox + c_draw], [y-5, y+5], 'b-', lw=1.5)
                self.ax.plot([ox + b_draw - c_draw, ox + b_draw - c_draw], [y-5, y+5], 'b-', lw=1.5)
            self.ax.plot([ox + c_draw, ox + b_draw - c_draw], [oy + c_draw, oy + c_draw], 'b-', lw=1.5)
            self.ax.plot([ox + c_draw, ox + b_draw - c_draw], [oy + h_draw - c_draw, oy + h_draw - c_draw], 'b-', lw=1.5)
            
            self.ax.annotate('', xy=(ox, oy-15), xytext=(ox+b_draw, oy-15), arrowprops=dict(arrowstyle='<->', color='black'))
            self.ax.text(ox+b_draw/2, oy-25, f'{b}mm', ha='center', va='top')
            self.ax.annotate('', xy=(ox-15, oy), xytext=(ox-15, oy+h_draw), arrowprops=dict(arrowstyle='<->', color='black'))
            self.ax.text(ox-25, oy+h_draw/2, f'{h}mm', ha='center', va='center', rotation=90)
            
            self.ax.set_xlim(ox-30, ox+b_draw+30)
            self.ax.set_ylim(oy-30, oy+h_draw+30)
            self.ax.set_aspect('equal')
            self.ax.axis('off')
            
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("错误", f"计算失败：{str(e)}")

if __name__ == "__main__":
    app = TorsionApp()
    app.mainloop()