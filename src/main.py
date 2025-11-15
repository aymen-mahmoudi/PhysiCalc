# src/main.py
import sys
import math
from functools import partial
from PyQt6 import QtWidgets
from utils import load_stylesheet
from gui import Ui_MainWindow


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Setup UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # APPLY MODERN FLAT STYLESHEET
        self.setStyleSheet(load_stylesheet())

        # Beautify operator labels (visual only)
        try:
            self.ui.b_mult.setText("×")
            self.ui.b_divise.setText("÷")
        except AttributeError:
            pass

        # ---------- STATE ----------
        self.ok = True          # True = ready to append, False = after result
        self.ans = 0.0
        self.history = []       # last three answers
        self.memory = 0.0
        self.deg_mode = True

        # ---- Physics constants (SI) ----
        self.CONSTANTS = {
            "c":     2.99792458e8,
            "h":     6.62607015e-34,
            "hbar":  1.054571817e-34,
            "k_B":   1.380649e-23,
            "eV":    1.602176634e-19,
            "q_e":   1.602176634e-19,
            "N_A":   6.02214076e23,
            "R":     8.314462618,
            "R_m":   8.314462618,
            "R_inf": 1.0973731568160e7,
            "mu0":   4 * math.pi * 1e-7,
            "eps0":  8.8541878128e-12,
            "G":     6.67430e-11,
            "m_e":   9.1093837015e-31,
            "m_p":   1.67262192369e-27,
            "m_n":   1.67492749804e-27,
            "a0":    5.29177210903e-11,
        }

        self._update_history_labels()
        self._connect_buttons()

    # ------------------------------------------------------------------
    # DISPLAY HELPERS – FIXED: RESULT STAYS!
    # ------------------------------------------------------------------
    def append_to_display(self, text: str):
        """Used for digits and operators – keeps result after ="""
        current = self.ui.lineEdit.text()

        # After =, result is shown and ok=False → next input appends
        if not self.ok:
            self.ui.lineEdit.setText(current + text)
            self.ok = True
            return

        if current in ("", "Error"):
            self.ui.lineEdit.setText(text)
        else:
            self.ui.lineEdit.setText(current + text)
        self.ok = True

    def append_literal(self, text: str):
        """Always append – for functions, constants, ANS, etc."""
        current = self.ui.lineEdit.text()
        if current == "Error":
            current = ""
        self.ui.lineEdit.setText(current + text)
        self.ok = True

    def delete_last(self):
        text = self.ui.lineEdit.text()
        self.ui.lineEdit.setText(text[:-1] if text else "")
        self.ok = True

    # ------------------------------------------------------------------
    # Scientific notation (E button)
    # ------------------------------------------------------------------
    def insert_sci_E(self):
        text = self.ui.lineEdit.text()
        if not text or text == "Error":
            self.append_literal("1e")
            return
        last = text[-1]
        if last.isdigit() or last in ").":
            self.append_literal("e")
        else:
            self.append_literal("1e")

    # ------------------------------------------------------------------
    # CALCULATION – RESULT STAYS
    # ------------------------------------------------------------------
    def calculate(self):
        try:
            expr = self.ui.lineEdit.text().strip()
            if not expr:
                return

            safe_dict = {
                "ans": self.ans,
                "ans1": self.history[0] if len(self.history) > 0 else 0,
                "ans2": self.history[1] if len(self.history) > 1 else 0,
                "ans3": self.history[2] if len(self.history) > 2 else 0,
                "pi": math.pi,
                "e": math.e,
                "sin": lambda x: math.sin(math.radians(x) if self.deg_mode else x),
                "cos": lambda x: math.cos(math.radians(x) if self.deg_mode else x),
                "tan": lambda x: math.tan(math.radians(x) if self.deg_mode else x),
                "asin": lambda x: math.degrees(math.asin(x)) if self.deg_mode else math.asin(x),
                "acos": lambda x: math.degrees(math.acos(x)) if self.deg_mode else math.acos(x),
                "atan": lambda x: math.degrees(math.atan(x)) if self.deg_mode else math.atan(x),
                "log": math.log10,
                "ln": math.log,
                "sqrt": math.sqrt,
                "abs": abs,
                "factorial": math.factorial,
            }
            safe_dict.update(self.CONSTANTS)

            result = eval(expr, {"__builtins__": {}}, safe_dict)
            result_str = self._fmt_number(result)
            self.ui.lineEdit.setText(result_str)

            # Update state
            self.ans = float(result)
            self.history.insert(0, self.ans)
            if len(self.history) > 3:
                self.history = self.history[:3]
            self._update_history_labels()

            # RESULT STAYS – next input will append
            self.ok = False
        except Exception:
            self.ui.lineEdit.setText("Error")
            self.ok = True

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------
    def memory_add(self):
        try:
            self.memory += float(self.ui.lineEdit.text())
        except:
            pass

    def memory_recall(self):
        self.append_literal(self._fmt_number(self.memory))

    def memory_clear(self):
        self.memory = 0.0

    # ------------------------------------------------------------------
    # Scientific Helpers
    # ------------------------------------------------------------------
    def insert_constant(self, const: str):
        self.append_literal(const)

    def insert_function(self, func: str):
        self.append_literal(func + "(")

    def square(self):
        self.append_literal("**2")

    def power(self):
        self.append_literal("**")

    def reciprocal(self):
        self.append_literal("1/")

    def toggle_sign(self):
        text = self.ui.lineEdit.text()
        if text and text not in ("0", "Error"):
            if text.startswith("-"):
                self.ui.lineEdit.setText(text[1:])
            else:
                self.ui.lineEdit.setText("-" + text)

    def toggle_deg_rad(self):
        self.deg_mode = not self.deg_mode
        sender = self.sender()
        if sender:
            sender.setText("DEG" if self.deg_mode else "RAD")

    # ------------------------------------------------------------------
    # Formatting + Labels
    # ------------------------------------------------------------------
    def _fmt_number(self, x):
        try:
            return f"{x:.10g}"
        except Exception:
            return str(x)

    def _update_history_labels(self):
        def txt(idx):
            if idx < len(self.history):
                return f" {self._fmt_number(self.history[idx])}"
            return ""
        for name, i in (("label_ans_1", 0), ("label_ans_2", 1), ("label_ans_3", 2)):
            lbl = getattr(self.ui, name, None)
            if lbl:
                lbl.setText(txt(i))

    # ------------------------------------------------------------------
    # Button Connections
    # ------------------------------------------------------------------
    def _connect_buttons(self):
        # Digits
        for i in range(10):
            btn = getattr(self.ui, f"b_{i}", None)
            if btn:
                btn.clicked.connect(partial(self.append_to_display, str(i)))

        # Point
        if hasattr(self.ui, "b_point"):
            self.ui.b_point.clicked.connect(partial(self.append_to_display, "."))

        # Operators
        ops = {
            "b_plus": "+", "b_moins": "-", "b_mult": "*", "b_divise": "/",
            "b_div": "//", "b_mod": "%", "b_po": "(", "b_pf": ")"
        }
        for name, op in ops.items():
            btn = getattr(self.ui, name, None)
            if btn:
                btn.clicked.connect(partial(self.append_to_display, op))

        # Control
        if hasattr(self.ui, "b_del"):
            self.ui.b_del.clicked.connect(self.delete_last)
        if hasattr(self.ui, "b_egale"):
            self.ui.b_egale.clicked.connect(self.calculate)

        # ANS History
        if hasattr(self.ui, "pushButton_ans_1"):
            self.ui.pushButton_ans_1.clicked.connect(lambda: self.append_history_value(0))
        if hasattr(self.ui, "pushButton_ans_2"):
            self.ui.pushButton_ans_2.clicked.connect(lambda: self.append_history_value(1))
        if hasattr(self.ui, "pushButton_ans_3"):
            self.ui.pushButton_ans_3.clicked.connect(lambda: self.append_history_value(2))

        # Memory
        if hasattr(self.ui, "b_mplus"): self.ui.b_mplus.clicked.connect(self.memory_add)
        if hasattr(self.ui, "b_mr"):    self.ui.b_mr.clicked.connect(self.memory_recall)
        if hasattr(self.ui, "b_mc"):    self.ui.b_mc.clicked.connect(self.memory_clear)

        # Scientific Functions
        sci_map = {
            "pushButton_sin":       lambda: self.insert_function("sin"),
            "pushButton_cos":       lambda: self.insert_function("cos"),
            "pushButton_tan":       lambda: self.insert_function("tan"),
            "pushButton_log":       lambda: self.insert_function("log"),
            "pushButton_ln":        lambda: self.insert_function("ln"),
            "pushButton_sqrt":      lambda: self.insert_function("sqrt"),
            "pushButton_pow2":      self.square,
            "pushButton_pow":       self.power,
            "pushButton_inv":       self.reciprocal,
            "pushButton_pm":        self.toggle_sign,
            "pushButton_pi":        lambda: self.append_literal("pi"),
            "pushButton_e":         lambda: self.append_literal("e"),
            "pushButton_deg":       self.toggle_deg_rad,
            "pushButton_E":         self.insert_sci_E,
            "pushButton_factorial": lambda: self.insert_function("factorial"),
        }
        for name, func in sci_map.items():
            btn = getattr(self.ui, name, None)
            if btn:
                btn.clicked.connect(func)

        # Physics Constants
        const_button_map = {
            "pushButton_c":    "c",     "pushButton_h":    "h",
            "pushButton_hbar": "hbar",  "pushButton_kB":   "k_B",
            "pushButton_eV":   "eV",    "pushButton_qe":   "q_e",
            "pushButton_NA":   "N_A",   "pushButton_R":    "R",
            "pushButton_Rm":   "R_m",   "pushButton_Rinf": "R_inf",
            "pushButton_mu0":  "mu0",   "pushButton_eps0": "eps0",
            "pushButton_me":   "m_e",   "pushButton_mp":   "m_p",
            "pushButton_mn":   "m_n",   "pushButton_a0":   "a0",
        }
        for btn_name, const_key in const_button_map.items():
            btn = getattr(self.ui, btn_name, None)
            if btn:
                btn.clicked.connect(partial(self.append_literal, const_key))

    # Helper for ANS history
    def append_history_value(self, index: int):
        if 0 <= index < len(self.history):
            self.append_literal(self._fmt_number(self.history[index]))


# ----------------------------------------------------------------------
# Run App
# ----------------------------------------------------------------------
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()