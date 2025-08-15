"""
Simulador de Trading (ETH/USD) em Tkinter
----------------------------------------

• Janela 1920x1080 com imagem de fundo opcional (arquivo: background_1550x800.jpg).
• Gráfico tipo candle/barra crescendo da esquerda para a direita, com uma nova barra a cada 5 segundos.
• Atualização do preço do ativo (ETH) a cada 5 segundos, podendo subir ou cair aleatoriamente.
• Botões no canto superior esquerdo para visualizar o saldo em USD ou em ETH (conversão automática pelo preço atual).
• Painel de trade no canto inferior direito com campos de quantidade e botões de Compra/Venda.
• Layout organizado, com comentários em português e código estruturado em classe.

Requisitos:
    pip install pillow

Execução:
    python simulador_trading_eth.py

Observações:
- Se a imagem de fundo não existir, o app usa uma cor sólida no fundo.
- O código é para fins educacionais e simula preços estocásticos simples.
"""

import os
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


class TradingSimulatorTk:
    # Constantes visuais e de simulação
    WIDTH = 1550 # ajustar o comprimento conforme a tela do monitor (ex:1920x1080 pixels)
    HEIGHT = 800 # ajustar a altura conforme a tela do monitor (ex:1920x1080 pixels)
    BG_IMAGE_PATH = "background_1550x800.jpg" # Coloque uma imagem tipo JPG na mesma pasta (Win+E) do arquivo .py e renomie sem o .jpg

    UPDATE_MS = 5000  # 5 segundos
    INITIAL_USD = 10_000.00  # saldo inicial em dólar
    INITIAL_ETH = 0.00       # saldo inicial em ETH

    # Área reservada ao gráfico em pixels
    CHART_LEFT_PAD = 60
    CHART_RIGHT_PAD = 40
    CHART_TOP_PAD = 80
    CHART_BOTTOM_PAD = 160

    CANDLE_WIDTH = 12      # largura da vela
    CANDLE_GAP = 4         # espaçamento entre velas
    GRID_HLINES = 6        # linhas horizontais de grade
    GRID_VLINES = 8        # linhas verticais de grade (apenas para visual)

    # Parâmetros de geração estocástica (simples)
    DRIFT = 0.0            # tendência média
    VOLATILITY = 0.006     # volatilidade (desvio padrão por passo ~0.6%)

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Simulador de Trading ETH/USD – Tkinter")
        self.root.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.root.resizable(False, False)

        # Estado financeiro
        self.balance_usd = float(self.INITIAL_USD)
        self.balance_eth = float(self.INITIAL_ETH)

        # Estado do preço/velas
        self.current_price = 3500.00  # preço inicial do ETH em USD (ajuste livre)
        self.candles = []  # lista de dicionários: {open, high, low, close, color}

        # Preferência de visualização do saldo ("USD" ou "ETH")
        self.balance_view = tk.StringVar(value="USD")

        # --- Fundo ---
        self._build_background()

        # --- Barra superior: preço e relógio ---
        self._build_header()

        # --- Gráfico ---
        self._build_chart()

        # --- Painel de saldo (canto superior esquerdo) ---
        self._build_balance_panel()

        # --- Painel de trade (canto inferior direito) ---
        self._build_trade_panel()

        # Primeira vela (para iniciar histórico)
        self._append_new_candle(initial=True)

        # Loop de atualização
        self._schedule_update()

    # ========================= Construção de UI ===============================
    def _build_background(self):
        """Cria uma imagem de fundo estática 1920x1080, se existir; senão, usa cor sólida."""
        self.bg_container = tk.Frame(self.root, width=self.WIDTH, height=self.HEIGHT)
        self.bg_container.place(x=0, y=0)

        if PIL_AVAILABLE and os.path.exists(self.BG_IMAGE_PATH):
            img = Image.open(self.BG_IMAGE_PATH).resize((self.WIDTH, self.HEIGHT), Image.LANCZOS)
            self.bg_img = ImageTk.PhotoImage(img)
            self.bg_label = tk.Label(self.bg_container, image=self.bg_img)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            # Sem imagem: preenchimento com uma cor neutra
            self.bg_label = tk.Label(self.bg_container, bg="#0f1116")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def _build_header(self):
        """Barra superior com preço atual e horário."""
        self.header = tk.Frame(self.root, bg="#111318")
        self.header.place(x=0, y=0, width=self.WIDTH, height=60)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Price.TLabel", foreground="#e8e8e8", background="#111318", font=("Segoe UI", 18, "bold"))
        style.configure("Time.TLabel", foreground="#c8c8c8", background="#111318", font=("Segoe UI", 11))

        self.price_var = tk.StringVar(value="-")
        self.time_var = tk.StringVar(value="-")

        self.price_label = ttk.Label(self.header, textvariable=self.price_var, style="Price.TLabel")
        self.price_label.place(x=self.WIDTH//2 - 220, y=14)

        self.time_label = ttk.Label(self.header, textvariable=self.time_var, style="Time.TLabel")
        self.time_label.place(x=self.WIDTH//2 + 220, y=20)

    def _build_chart(self):
        """Canvas para o gráfico de candles/barras."""
        self.chart_w = self.WIDTH - self.CHART_LEFT_PAD - self.CHART_RIGHT_PAD
        self.chart_h = self.HEIGHT - self.CHART_TOP_PAD - self.CHART_BOTTOM_PAD
        self.chart = tk.Canvas(self.root, width=self.chart_w, height=self.chart_h, bg="#0e1117", highlightthickness=0)
        self.chart.place(x=self.CHART_LEFT_PAD, y=self.CHART_TOP_PAD)

    def _build_balance_panel(self):
        """Canto superior esquerdo: botões de visualização do saldo e valores."""
        self.balance_frame = tk.Frame(self.root, bg="#151922")
        self.balance_frame.place(x=16, y=70, width=360, height=110)

        ttk.Style().configure("Balance.TLabel", foreground="#e8e8e8", background="#151922", font=("Segoe UI", 12, "bold"))
        ttk.Style().configure("Small.TLabel", foreground="#b0b0b0", background="#151922", font=("Segoe UI", 10))

        lbl = ttk.Label(self.balance_frame, text="Visualizar Saldo:", style="Small.TLabel")
        lbl.place(x=12, y=8)

        # Botões para alternar visualização
        btn_usd = ttk.Button(self.balance_frame, text="USD", command=lambda: self._set_balance_view("USD"))
        btn_eth = ttk.Button(self.balance_frame, text="ETH", command=lambda: self._set_balance_view("ETH"))
        btn_usd.place(x=12, y=36, width=70, height=28)
        btn_eth.place(x=90, y=36, width=70, height=28)

        self.balance_display_var = tk.StringVar(value="-")
        self.balance_display = ttk.Label(self.balance_frame, textvariable=self.balance_display_var, style="Balance.TLabel")
        self.balance_display.place(x=12, y=74)

    def _build_trade_panel(self):
        """Canto inferior direito: painel de compra/venda, inputs e ações."""
        panel_w, panel_h = 520, 260
        self.trade_frame = tk.Frame(self.root, bg="#151922")
        self.trade_frame.place(x=self.WIDTH - panel_w - 20, y=self.HEIGHT - panel_h - 20, width=panel_w, height=panel_h)

        ttk.Style().configure("Trade.TLabel", foreground="#e8e8e8", background="#151922", font=("Segoe UI", 11, "bold"))
        ttk.Style().configure("TradeSmall.TLabel", foreground="#b0b0b0", background="#151922", font=("Segoe UI", 10))

        ttk.Label(self.trade_frame, text="Trading ETH/USD (Mercado)", style="Trade.TLabel").place(x=16, y=12)

        # Preço atual
        self.trade_price_var = tk.StringVar(value="-")
        ttk.Label(self.trade_frame, text="Preço Atual:", style="TradeSmall.TLabel").place(x=16, y=48)
        ttk.Label(self.trade_frame, textvariable=self.trade_price_var, style="Trade.TLabel").place(x=110, y=44)

        # Quantidade de ETH para usar na operação
        ttk.Label(self.trade_frame, text="Quantidade (ETH):", style="TradeSmall.TLabel").place(x=16, y=82)
        self.qty_var = tk.StringVar(value="0.10")
        self.qty_entry = ttk.Entry(self.trade_frame, textvariable=self.qty_var)
        self.qty_entry.place(x=140, y=80, width=120, height=26)

        # Saldo disponível
        self.usd_var = tk.StringVar(value="-")
        self.eth_var = tk.StringVar(value="-")
        ttk.Label(self.trade_frame, text="Saldo USD:", style="TradeSmall.TLabel").place(x=280, y=48)
        ttk.Label(self.trade_frame, textvariable=self.usd_var, style="TradeSmall.TLabel").place(x=350, y=48)
        ttk.Label(self.trade_frame, text="Saldo ETH:", style="TradeSmall.TLabel").place(x=280, y=76)
        ttk.Label(self.trade_frame, textvariable=self.eth_var, style="TradeSmall.TLabel").place(x=350, y=76)

        # Botões de ação
        buy_btn = ttk.Button(self.trade_frame, text="Comprar ETH (Vender USD)", command=self._buy_eth)
        sell_btn = ttk.Button(self.trade_frame, text="Vender ETH (Comprar USD)", command=self._sell_eth)
        buy_btn.place(x=16, y=122, width=220, height=36)
        sell_btn.place(x=260, y=122, width=220, height=36)

        # Feedback da ordem
        self.order_msg_var = tk.StringVar(value="")
        ttk.Label(self.trade_frame, textvariable=self.order_msg_var, style="TradeSmall.TLabel").place(x=16, y=170)

        # Rodapé informativo
        self.valuation_var = tk.StringVar(value="")
        ttk.Label(self.trade_frame, textvariable=self.valuation_var, style="TradeSmall.TLabel").place(x=16, y=200)

    # ========================= Lógica de Negócio ==============================
    def _set_balance_view(self, mode: str):
        """Alterna a visualização do saldo principal (USD ou ETH)."""
        if mode in ("USD", "ETH"):
            self.balance_view.set(mode)
            self._refresh_info_labels()

    def _schedule_update(self):
        """Agendador principal do loop de simulação a cada UPDATE_MS."""
        self._tick()  # executa agora
        self.root.after(self.UPDATE_MS, self._schedule_update)  # agenda próximo ciclo

    def _tick(self):
        """Um passo de simulação: atualiza preço, adiciona candle e redesenha gráfico."""
        self._simulate_next_price()
        self._append_new_candle()
        self._draw_chart()
        self._refresh_info_labels()

    def _simulate_next_price(self):
        """Gera próximo preço via passeio aleatório com volatilidade controlada."""
        # variação percentual ~ Normal(DRIFT, VOLATILITY)
        pct_change = random.gauss(self.DRIFT, self.VOLATILITY)
        new_price = max(1.0, self.current_price * (1.0 + pct_change))  # evita preço <= 0
        self.prev_price = self.current_price
        self.current_price = round(new_price, 2)

    def _append_new_candle(self, initial: bool = False):
        """Adiciona uma nova vela (OHLC). Se initial, cria uma vela neutra."""
        if initial or not self.candles:
            o = self.current_price * (1 + random.uniform(-0.001, 0.001))
            c = self.current_price
        else:
            o = self.candles[-1]["close"]
            c = self.current_price

        # Ruído para high/low
        high = max(o, c) * (1 + abs(random.gauss(0, 0.0015)))
        low = min(o, c) * (1 - abs(random.gauss(0, 0.0015)))
        color = "#22c55e" if c >= o else "#ef4444"  # verde ou vermelho

        candle = {
            "open": round(o, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(c, 2),
            "color": color,
        }
        self.candles.append(candle)

    # ========================= Desenho do Gráfico ============================
    def _draw_chart(self):
        self.chart.delete("all")

        if not self.candles:
            return

        # Determina quantas velas cabem na largura do canvas
        step = self.CANDLE_WIDTH + self.CANDLE_GAP
        max_candles = max(1, self.chart_w // step)
        data = self.candles[-max_candles:]

        # Intervalo de preços para o scaling vertical
        all_high = max(c["high"] for c in data)
        all_low = min(c["low"] for c in data)
        padding = max(1.0, (all_high - all_low) * 0.10)
        top_price = all_high + padding
        bot_price = max(0.1, all_low - padding)

        def yfrom(price: float) -> float:
            # mapeia preço -> y (invertido: preço alto mais para cima)
            norm = (price - bot_price) / (top_price - bot_price)
            return self.chart_h - norm * self.chart_h

        # Grade
        self._draw_grid(top_price, bot_price)

        # Desenha velas da esquerda para a direita
        x = 0
        for c in data:
            o, h, l, cl, color = c["open"], c["high"], c["low"], c["close"], c["color"]
            x_center = x + self.CANDLE_WIDTH // 2

            # Pavios
            self.chart.create_line(x_center, yfrom(h), x_center, yfrom(l), fill=color)

            # Corpo da vela (mínimo 1px de altura para legibilidade)
            y_open = yfrom(o)
            y_close = yfrom(cl)
            top = min(y_open, y_close)
            bottom = max(y_open, y_close)
            if abs(bottom - top) < 1:
                bottom = top + 1

            self.chart.create_rectangle(
                x, top, x + self.CANDLE_WIDTH, bottom,
                fill=color, outline=color
            )

            x += step

        # Eixos simples (labels de preço nas bordas esquerda)
        self.chart.create_text(8, 10, anchor="nw", fill="#c7c7c7", text=f"Máx: {top_price:.2f}")
        self.chart.create_text(8, self.chart_h - 24, anchor="nw", fill="#c7c7c7", text=f"Mín: {bot_price:.2f}")

    def _draw_grid(self, top_price: float, bot_price: float):
        # Linhas horizontais
        for i in range(self.GRID_HLINES + 1):
            y = i * (self.chart_h / self.GRID_HLINES)
            self.chart.create_line(0, y, self.chart_w, y, fill="#23262e")
            # label de preço aproximado
            p = top_price - (top_price - bot_price) * (i / self.GRID_HLINES)
            self.chart.create_text(self.chart_w - 6, y + 2, anchor="ne", fill="#8a8f9a", text=f"{p:.2f}")

        # Linhas verticais (apenas para estética)
        step = self.chart_w / self.GRID_VLINES
        for i in range(1, self.GRID_VLINES):
            x = i * step
            self.chart.create_line(x, 0, x, self.chart_h, fill="#20232b")

    # ========================= Atualização de Labels ==========================
    def _refresh_info_labels(self):
        # Atualiza preço no header e horário
        self.price_var.set(f"ETH/USD: ${self.current_price:,.2f}")
        self.time_var.set(time.strftime("%d/%m/%Y %H:%M:%S"))

        # Atualiza preço no painel de trade
        self.trade_price_var.set(f"$ {self.current_price:,.2f}")

        # Atualiza saldos
        self.usd_var.set(f"$ {self.balance_usd:,.2f}")
        self.eth_var.set(f"{self.balance_eth:.6f} ETH")

        # Valorização total em USD (USD + ETH*preço)
        equity_usd = self.balance_usd + self.balance_eth * self.current_price
        self.valuation_var.set(f"Equity (USD): $ {equity_usd:,.2f}  |  Equity (ETH): {equity_usd / self.current_price:.6f} ETH")

        # Painel de saldo principal (conforme escolha USD/ETH)
        if self.balance_view.get() == "USD":
            self.balance_display_var.set(f"Saldo Principal: $ {self.balance_usd:,.2f}")
        else:
            self.balance_display_var.set(f"Saldo Principal: {self.balance_eth:.6f} ETH")

    # ========================= Ações de Trading ===============================
    def _parse_qty(self) -> float:
        try:
            q = float(self.qty_var.get())
            if q <= 0:
                raise ValueError
            return q
        except Exception:
            messagebox.showerror("Quantidade inválida", "Informe uma quantidade de ETH positiva, ex.: 0.10")
            return 0.0

    def _buy_eth(self):
        qty = self._parse_qty()
        if qty <= 0:
            return
        cost = qty * self.current_price
        if cost > self.balance_usd + 1e-9:
            messagebox.showwarning("Saldo insuficiente", "Você não possui USD suficiente para esta compra.")
            return
        self.balance_usd -= cost
        self.balance_eth += qty
        self.order_msg_var.set(f"Comprado {qty:.6f} ETH por $ {cost:,.2f}")
        self._refresh_info_labels()

    def _sell_eth(self):
        qty = self._parse_qty()
        if qty <= 0:
            return
        if qty > self.balance_eth + 1e-12:
            messagebox.showwarning("Saldo insuficiente", "Você não possui ETH suficiente para esta venda.")
            return
        proceeds = qty * self.current_price
        self.balance_eth -= qty
        self.balance_usd += proceeds
        self.order_msg_var.set(f"Vendido {qty:.6f} ETH por $ {proceeds:,.2f}")
        self._refresh_info_labels()


def main():
    root = tk.Tk()
    app = TradingSimulatorTk(root)
    root.mainloop()


if __name__ == "__main__":
    main()
