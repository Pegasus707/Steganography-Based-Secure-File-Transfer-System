import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import crypto_engine as crypto
import stego_engine as stego


class StegoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steganography File Transfer System")
        self.geometry("620x540")
        self.minsize(580, 500)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Encode
        enc_tab = ttk.Frame(notebook)
        notebook.add(enc_tab, text="Encode & Hide")
        self._build_encode_tab(enc_tab)

        # Tab 2: Decode
        dec_tab = ttk.Frame(notebook)
        notebook.add(dec_tab, text="Extract & Decrypt")
        self._build_decode_tab(dec_tab)

    # -----------------------------
    # ENCODE TAB
    # -----------------------------
    def _build_encode_tab(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill="both", expand=True)

        # Carrier Type & Path
        ttk.Label(frame, text="1. Select Carrier Medium & File:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        row_type = ttk.Frame(frame)
        row_type.pack(fill="x", pady=(2, 2))
        self.enc_carrier_mode = tk.StringVar(value="Image")
        ttk.Radiobutton(row_type, text="PNG Image", variable=self.enc_carrier_mode, value="Image", command=self._reset_carrier_view).pack(side="left")
        ttk.Radiobutton(row_type, text="WAV Audio", variable=self.enc_carrier_mode, value="Audio", command=self._reset_carrier_view).pack(side="left", padx=10)

        row_cpath = ttk.Frame(frame)
        row_cpath.pack(fill="x", pady=2)
        self.enc_carrier_path = tk.StringVar()
        ttk.Entry(row_cpath, textvariable=self.enc_carrier_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row_cpath, text="Browse", command=self._browse_encode_carrier).pack(side="right", padx=(5, 0))

        self.capacity_lbl = ttk.Label(frame, text="Carrier Capacity: N/A", foreground="gray")
        self.capacity_lbl.pack(anchor="w", pady=(0, 6))

        # Payload Type
        ttk.Label(frame, text="2. Secret Payload:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        row_ptype = ttk.Frame(frame)
        row_ptype.pack(fill="x", pady=(2, 2))
        self.enc_payload_type = tk.StringVar(value="Text")
        ttk.Radiobutton(row_ptype, text="Text Message", variable=self.enc_payload_type, value="Text", command=self._toggle_payload_view).pack(side="left")
        ttk.Radiobutton(row_ptype, text="File", variable=self.enc_payload_type, value="File", command=self._toggle_payload_view).pack(side="left", padx=10)

        self.enc_text_box = tk.Text(frame, height=4)
        self.enc_text_box.pack(fill="x", pady=2)

        self.enc_file_frame = ttk.Frame(frame)
        self.enc_file_path = tk.StringVar()
        ttk.Entry(self.enc_file_frame, textvariable=self.enc_file_path).pack(side="left", fill="x", expand=True)
        ttk.Button(self.enc_file_frame, text="Browse", command=self._browse_payload_file).pack(side="right", padx=(5, 0))

        # Password
        ttk.Label(frame, text="3. Password:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(6, 2))
        self.enc_pwd = ttk.Entry(frame, show="*")
        self.enc_pwd.pack(fill="x", pady=2)

        ttk.Button(frame, text="Encrypt & Embed Data", command=self._execute_encode).pack(pady=12)

    # -----------------------------
    # DECODE TAB
    # -----------------------------
    def _build_decode_tab(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="1. Select Stego File:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        row_type = ttk.Frame(frame)
        row_type.pack(fill="x", pady=(2, 2))
        self.dec_carrier_mode = tk.StringVar(value="Image")
        ttk.Radiobutton(row_type, text="PNG Image", variable=self.dec_carrier_mode, value="Image").pack(side="left")
        ttk.Radiobutton(row_type, text="WAV Audio", variable=self.dec_carrier_mode, value="Audio").pack(side="left", padx=10)

        row_spath = ttk.Frame(frame)
        row_spath.pack(fill="x", pady=2)
        self.dec_stego_path = tk.StringVar()
        ttk.Entry(row_spath, textvariable=self.dec_stego_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row_spath, text="Browse", command=self._browse_decode_carrier).pack(side="right", padx=(5, 0))

        ttk.Label(frame, text="2. Password:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(6, 2))
        self.dec_pwd = ttk.Entry(frame, show="*")
        self.dec_pwd.pack(fill="x", pady=2)

        ttk.Button(frame, text="Extract & Decrypt", command=self._execute_decode).pack(pady=10)

        ttk.Label(frame, text="Extracted Content:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(6, 2))
        self.dec_output = tk.Text(frame, height=6)
        self.dec_output.pack(fill="both", expand=True, pady=2)

    # -----------------------------
    # EVENT HANDLERS
    # -----------------------------
    def _toggle_payload_view(self):
        if self.enc_payload_type.get() == "Text":
            self.enc_file_frame.pack_forget()
            self.enc_text_box.pack(fill="x", pady=2)
        else:
            self.enc_text_box.pack_forget()
            self.enc_file_frame.pack(fill="x", pady=2)

    def _reset_carrier_view(self):
        self.enc_carrier_path.set("")
        self.capacity_lbl.config(text="Carrier Capacity: N/A")

    def _browse_encode_carrier(self):
        is_img = self.enc_carrier_mode.get() == "Image"
        ftypes = [("PNG Images", "*.png")] if is_img else [("WAV Audio", "*.wav")]
        path = filedialog.askopenfilename(filetypes=ftypes)
        if path:
            self.enc_carrier_path.set(path)
            try:
                cap = stego.get_image_capacity(path) if is_img else stego.get_audio_capacity(path)
                self.capacity_lbl.config(text=f"Carrier Capacity: {cap:,} bytes (~{cap / 1024:.1f} KB)")
            except Exception as e:
                self.capacity_lbl.config(text=f"Error: {e}")

    def _browse_payload_file(self):
        path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
        if path:
            self.enc_file_path.set(path)

    def _browse_decode_carrier(self):
        is_img = self.dec_carrier_mode.get() == "Image"
        ftypes = [("PNG Images", "*.png")] if is_img else [("WAV Audio", "*.wav")]
        path = filedialog.askopenfilename(filetypes=ftypes)
        if path:
            self.dec_stego_path.set(path)

    def _execute_encode(self):
        carrier = self.enc_carrier_path.get().strip()
        pwd = self.enc_pwd.get()
        is_img = self.enc_carrier_mode.get() == "Image"

        if not carrier or not os.path.exists(carrier):
            messagebox.showerror("Error", "Please select a valid carrier file.")
            return
        if not pwd:
            messagebox.showerror("Error", "Password cannot be empty.")
            return

        if self.enc_payload_type.get() == "Text":
            raw_text = self.enc_text_box.get("1.0", tk.END).strip()
            if not raw_text:
                messagebox.showerror("Error", "Please enter a message to hide.")
                return
            data = raw_text.encode("utf-8")
            fname = "__TEXT_PAYLOAD__"
        else:
            p_path = self.enc_file_path.get().strip()
            if not p_path or not os.path.exists(p_path):
                messagebox.showerror("Error", "Please select a valid file to hide.")
                return
            with open(p_path, "rb") as f:
                data = f.read()
            fname = os.path.basename(p_path)

        def_ext = ".png" if is_img else ".wav"
        ftypes = [("PNG Image", "*.png")] if is_img else [("WAV Audio", "*.wav")]
        out_path = filedialog.asksaveasfilename(defaultextension=def_ext, filetypes=ftypes)
        if not out_path:
            return

        try:
            encrypted_blob = crypto.encrypt_payload(data, fname, pwd)
            if is_img:
                stego.hide_in_image(carrier, encrypted_blob, out_path)
            else:
                stego.hide_in_audio(carrier, encrypted_blob, out_path)
            messagebox.showinfo("Success", f"Data embedded and saved to:\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _execute_decode(self):
        stego_path = self.dec_stego_path.get().strip()
        pwd = self.dec_pwd.get()
        is_img = self.dec_carrier_mode.get() == "Image"

        if not stego_path or not os.path.exists(stego_path):
            messagebox.showerror("Error", "Select a valid stego file.")
            return
        if not pwd:
            messagebox.showerror("Error", "Enter the decryption password.")
            return

        try:
            blob = stego.extract_from_image(stego_path) if is_img else stego.extract_from_audio(stego_path)
            fname, data = crypto.decrypt_payload(blob, pwd)

            self.dec_output.delete("1.0", tk.END)
            if fname == "__TEXT_PAYLOAD__":
                self.dec_output.insert(tk.END, data.decode("utf-8", errors="replace"))
                messagebox.showinfo("Success", "Decrypted text recovered successfully.")
            else:
                save_path = filedialog.asksaveasfilename(initialfile=fname, filetypes=[("All Files", "*.*")])
                if save_path:
                    with open(save_path, "wb") as f:
                        f.write(data)
                    self.dec_output.insert(tk.END, f"[Extracted File]\nSaved to: {save_path}\nSize: {len(data):,} bytes")
                    messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        except Exception as e:
            self.dec_output.delete("1.0", tk.END)
            messagebox.showerror("Error", str(e))