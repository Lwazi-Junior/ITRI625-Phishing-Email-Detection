import queue
import sys
import threading

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import tkinter as tk

import requests


# ============================================================
# Configuration
# ============================================================
API_BASE_URL = "http://127.0.0.1:8000"
HEALTH_URL = f"{API_BASE_URL}/health"
PREDICT_URL = f"{API_BASE_URL}/predict"
REQUEST_TIMEOUT = 30

PHISHING_EXAMPLE = (
    "URGENT: Your account has been locked. Verify your "
    "password immediately by clicking this link."
)

LEGITIMATE_EXAMPLE = (
    "Hi Lwazi, please remember that our project meeting "
    "is scheduled for tomorrow at 10:00. The agenda is "
    "attached. Regards, Michael."
)

BG = "#0f172a"
CARD = "#1e293b"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
PHISHING = "#fb7185"
LEGITIMATE = "#4ade80"
BUTTON = "#2563eb"
BUTTON_TEXT = "#f8fafc"


# ============================================================
# Application
# ============================================================
class PhishGuardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        try:
            self.tk.call("tk", "scaling", 1.0)
        except tk.TclError:
            pass

        self.title(
            "PhishGuard AI - Phishing Email Detection"
        )
        self.geometry("1180x760")
        self.minsize(1050, 700)
        self.configure(bg=BG)

        self.api_online = False
        self.analysis_in_progress = False
        self.last_error = ""
        self.ui_queue = queue.Queue()

        self._build_layout()
        self.after(200, self.refresh_api_status)
        self.after(50, self._poll_ui_queue)

    def _post_to_ui(self, callback):
        self.ui_queue.put(callback)

    def _poll_ui_queue(self):
        try:
            while True:
                callback = self.ui_queue.get_nowait()
                callback()
        except queue.Empty:
            pass
        self.after(50, self._poll_ui_queue)

    def _build_layout(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(18, 8))

        tk.Label(
            header,
            text="PhishGuard AI",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 24, "bold")
        ).pack(side="left")

        tk.Label(
            header,
            text="Phishing Email Detection",
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 12)
        ).pack(side="left", padx=(12, 0), pady=(10, 0))

        self.api_status = tk.StringVar(value="Checking API...")
        self.api_status_label = tk.Label(
            header,
            textvariable=self.api_status,
            bg=BG,
            fg=MUTED,
            font=("Segoe UI", 12, "bold")
        )
        self.api_status_label.pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=8)

        input_card = tk.Frame(body, bg=CARD)
        input_card.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(
            input_card,
            text="Email message",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=16, pady=(14, 6))

        self.email_box = tk.Text(
            input_card,
            wrap="word",
            bg="#020617",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 11),
            padx=12,
            pady=12
        )
        self.email_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        buttons = tk.Frame(input_card, bg=CARD)
        buttons.pack(fill="x", padx=16, pady=(0, 16))

        self._button(
            buttons, "Load Phishing Example", self.load_phishing_example
        ).pack(side="left", padx=(0, 8))
        self._button(
            buttons, "Load Legitimate Example", self.load_legitimate_example
        ).pack(side="left", padx=(0, 8))
        self._button(
            buttons, "Clear", self.clear_email
        ).pack(side="left")

        self.analyse_button = self._button(
            buttons,
            "ANALYSE EMAIL",
            self.analyse_email,
            bg="#0284c7"
        )
        self.analyse_button.pack(side="right")

        self.refresh_button = self._button(
            buttons, "Refresh", self.refresh_api_status
        )
        self.refresh_button.pack(side="right", padx=(0, 8))

        result_card = tk.Frame(body, bg=CARD, width=460)
        result_card.pack(side="right", fill="y", padx=(12, 0))
        result_card.pack_propagate(False)

        tk.Label(
            result_card,
            text="Analysis result",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).pack(anchor="w", padx=16, pady=(14, 8))

        self.prediction_var = tk.StringVar(value="Waiting for analysis")
        self.prediction_label = tk.Label(
            result_card,
            textvariable=self.prediction_var,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 18, "bold"),
            wraplength=380,
            justify="left"
        )
        self.prediction_label.pack(anchor="w", padx=16, pady=(0, 12))

        self.detail_vars = {
            "Model": tk.StringVar(value="—"),
            "Risk Level": tk.StringVar(value="—"),
            "Confidence": tk.StringVar(value="—"),
            "Phishing Probability": tk.StringVar(value="—"),
            "Legitimate Probability": tk.StringVar(value="—"),
            "Decision Threshold": tk.StringVar(value="—")
        }

        for label, variable in self.detail_vars.items():
            row = tk.Frame(result_card, bg=CARD)
            row.pack(fill="x", padx=16, pady=4)
            tk.Label(
                row,
                text=label,
                bg=CARD,
                fg=MUTED,
                font=("Segoe UI", 10),
                width=22,
                anchor="w"
            ).pack(side="left")
            tk.Label(
                row,
                textvariable=variable,
                bg=CARD,
                fg=TEXT,
                font=("Segoe UI", 11, "bold"),
                anchor="w"
            ).pack(side="left", fill="x", expand=True)

        tk.Label(
            result_card,
            text="Phishing risk meter",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=16, pady=(18, 6))

        self.meter = tk.Canvas(
            result_card,
            height=28,
            bg="#020617",
            highlightthickness=0
        )
        self.meter.pack(fill="x", padx=16, pady=(0, 8))
        self.meter_fill = self.meter.create_rectangle(
            0, 0, 0, 28, fill=MUTED, width=0
        )
        self.meter_text = tk.StringVar(value="0%")
        tk.Label(
            result_card,
            textvariable=self.meter_text,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(anchor="w", padx=16)

        self.message_var = tk.StringVar(value="")
        tk.Label(
            result_card,
            textvariable=self.message_var,
            bg=CARD,
            fg="#fbbf24",
            font=("Segoe UI", 10),
            wraplength=380,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(16, 12))

    def _button(self, parent, text, command, bg=BUTTON):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=BUTTON_TEXT,
            activebackground="#1d4ed8",
            activeforeground=BUTTON_TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=12,
            pady=8,
            cursor="hand2"
        )

    def load_phishing_example(self):
        self._set_email_text(PHISHING_EXAMPLE)

    def load_legitimate_example(self):
        self._set_email_text(LEGITIMATE_EXAMPLE)

    def clear_email(self):
        self._set_email_text("")
        self._reset_result("Waiting for analysis")
        self.message_var.set("")

    def _set_email_text(self, text):
        self.email_box.delete("1.0", "end")
        if text:
            self.email_box.insert("1.0", text)

    def refresh_api_status(self):
        self.api_status.set("Checking API...")
        self.api_status_label.configure(fg=MUTED)
        threading.Thread(
            target=self._check_health,
            daemon=True
        ).start()

    def _check_health(self):
        try:
            response = requests.get(
                HEALTH_URL,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            payload = response.json()
            threshold = float(payload["decision_threshold"])
            self._post_to_ui(lambda: self._set_online(threshold))
        except requests.RequestException:
            self._post_to_ui(self._set_offline)

    def _set_online(self, threshold):
        self.api_online = True
        self.api_status.set(
            f"API ONLINE | Threshold {threshold:.2f}"
        )
        self.api_status_label.configure(fg=LEGITIMATE)

    def _set_offline(self):
        self.api_online = False
        self.api_status.set("API OFFLINE")
        self.api_status_label.configure(fg=PHISHING)

    def analyse_email(self):
        if self.analysis_in_progress:
            return

        email_text = self.email_box.get("1.0", "end").strip()
        if not email_text:
            self._show_error(
                "Enter or paste an email before analysing."
            )
            return

        self.analysis_in_progress = True
        self.analyse_button.configure(state="disabled")
        self.prediction_var.set("Analysing...")
        self.prediction_label.configure(fg=ACCENT)
        self.message_var.set("")

        threading.Thread(
            target=self._request_prediction,
            args=(email_text,),
            daemon=True
        ).start()

    def _request_prediction(self, email_text):
        try:
            response = requests.post(
                PREDICT_URL,
                json={"email_text": email_text},
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code >= 400:
                self._post_to_ui(
                    lambda: self._show_error(
                        "The API rejected this email. "
                        "Check that the message is not empty."
                    )
                )
                return

            payload = response.json()
            self._post_to_ui(lambda: self._show_result(payload))
        except requests.RequestException:
            self._post_to_ui(
                lambda: self._show_error(
                    "Could not reach the PhishGuard API. "
                    "Start the FastAPI service, then press Refresh."
                )
            )

    def _show_result(self, payload):
        prediction = payload["prediction"]
        phishing_probability = float(payload["phishing_probability"])
        legitimate_probability = float(
            payload["legitimate_probability"]
        )
        confidence = float(payload["confidence"])
        threshold = float(payload["threshold"])

        if prediction == "Phishing":
            headline = "PHISHING DETECTED"
            colour = PHISHING
        else:
            headline = "LEGITIMATE EMAIL"
            colour = LEGITIMATE

        self.prediction_var.set(headline)
        self.prediction_label.configure(fg=colour)
        self.detail_vars["Model"].set(payload["model"])
        self.detail_vars["Risk Level"].set(payload["risk_level"])
        self.detail_vars["Confidence"].set(
            f"{confidence * 100:.4f}%"
        )
        self.detail_vars["Phishing Probability"].set(
            f"{phishing_probability * 100:.4f}%"
        )
        self.detail_vars["Legitimate Probability"].set(
            f"{legitimate_probability * 100:.4f}%"
        )
        self.detail_vars["Decision Threshold"].set(f"{threshold:.2f}")
        self.update_idletasks()
        self._update_meter(phishing_probability)
        self.message_var.set("")
        self.last_error = ""
        self._finish_analysis()

    def _show_error(self, message):
        self.last_error = message
        self.prediction_var.set("Analysis unavailable")
        self.prediction_label.configure(fg=PHISHING)
        self.message_var.set(message)
        self._finish_analysis()

    def _finish_analysis(self):
        self.analysis_in_progress = False
        self.analyse_button.configure(state="normal")

    def _reset_result(self, headline):
        self.prediction_var.set(headline)
        self.prediction_label.configure(fg=MUTED)
        for variable in self.detail_vars.values():
            variable.set("—")
        self._update_meter(0)

    def _update_meter(self, probability):
        probability = max(0.0, min(1.0, float(probability)))
        width = max(self.meter.winfo_width(), 360)
        if probability >= 0.75:
            colour = PHISHING
        elif probability >= 0.54:
            colour = "#fbbf24"
        else:
            colour = LEGITIMATE
        self.meter.coords(
            self.meter_fill,
            0,
            0,
            width * probability,
            28
        )
        self.meter.itemconfigure(self.meter_fill, fill=colour)
        self.meter_text.set(f"{probability * 100:.4f}%")


def main():
    app = PhishGuardApp()
    app.mainloop()


if __name__ == "__main__":
    main()
