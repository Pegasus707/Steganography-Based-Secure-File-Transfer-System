import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

import crypto_engine as crypto
import stego_engine as stego


class StegoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Steganography File Transfer System")
        self.geometry("720x680")
        self.minsize(680, 600)

        # Image references to prevent Tkinter garbage collection
        self._enc_carrier_photo = None
        self._enc_stego_photo = None
        self._dec_stego_photo = None

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

    def _create_thumbnail(self, image_path: str, max_size=(130, 130)):
        """Utility to safely load and resize an image into a PhotoImage thumbnail."""
        try:
            with Image.open(image_path) as img:
                resample_mode = getattr(Image, "Resampling", Image).LANCZOS
                img.thumbnail(max_size, resample_mode)
                return ImageTk.PhotoImage(img.convert("RGB"))
        except Exception:
            return None

    # -----------------------------
    # ENCODE TAB
    # -----------------------------
    def _build_encode_tab(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="1. Select Carrier Medium & File:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        row_type = ttk.Frame(frame)
        row_type.pack(fill="x", pady=(2, 2))
        self.enc_carrier_mode = tk.StringVar(value="Image")
        ttk.Radiobutton(row_type, text="Image (PNG / JPG / JPEG)", variable=self.enc_carrier_mode, value="Image", command=self._reset_carrier_view).pack(side="left")
        ttk.Radiobutton(row_type, text="Audio (WAV / MP3)", variable=self.enc_carrier_mode, value="Audio", command=self._reset_carrier_view).pack(side="left", padx=10)

        row_cpath = ttk.Frame(frame)
        row_cpath.pack(fill="x", pady=2)
        self.enc_carrier_path = tk.StringVar()
        ttk.Entry(row_cpath, textvariable=self.enc_carrier_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row_cpath, text="Browse", command=self._browse_encode_carrier).pack(side="right", padx=(5, 0))

        self.capacity_lbl = ttk.Label(frame, text="Carrier Capacity: N/A", foreground="gray")
        self.capacity_lbl.pack(anchor="w", pady=(0, 4))

        # Image Preview Comparison Box
        self.enc_preview_frame = ttk.LabelFrame(frame, text=" Visual Carrier & Output Preview ", padding=6)
        self.enc_preview_frame.pack(fill="x", pady=(0, 8))

        preview_box = ttk.Frame(self.enc_preview_frame)
        preview_box.pack(fill="x", expand=True)

        # Original Carrier Preview
        c_box = ttk.Frame(preview_box)
        c_box.pack(side="left", expand=True, padx=10)
        ttk.Label(c_box, text="Original Carrier", font=("Helvetica", 9, "bold")).pack()
        self.enc_carrier_img_lbl = ttk.Label(c_box, text="[ No Image Loaded ]", anchor="center", relief="solid", borderwidth=1)
        self.enc_carrier_img_lbl.pack(ipadx=10, ipady=10, pady=4)

        # Arrow indicator
        ttk.Label(preview_box, text="➔", font=("Helvetica", 14, "bold"), foreground="gray").pack(side="left", padx=5)

        # Encoded Stego Output Preview
        s_box = ttk.Frame(preview_box)
        s_box.pack(side="left", expand=True, padx=10)
        ttk.Label(s_box, text="Encoded Stego Image", font=("Helvetica", 9, "bold")).pack()
        self.enc_stego_img_lbl = ttk.Label(s_box, text="[ Waiting for Encoding ]", anchor="center", relief="solid", borderwidth=1)
        self.enc_stego_img_lbl.pack(ipadx=10, ipady=10, pady=4)

        self.enc_preview_status = ttk.Label(self.enc_preview_frame, text="", font=("Helvetica", 8, "italic"), foreground="green")
        self.enc_preview_status.pack(pady=(2, 0))

        # Payload Type
        ttk.Label(frame, text="2. Secret Payload:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        row_ptype = ttk.Frame(frame)
        row_ptype.pack(fill="x", pady=(2, 2))
        self.enc_payload_type = tk.StringVar(value="Text")
        ttk.Radiobutton(row_ptype, text="Text Message", variable=self.enc_payload_type, value="Text", command=self._toggle_payload_view).pack(side="left")
        ttk.Radiobutton(row_ptype, text="File", variable=self.enc_payload_type, value="File", command=self._toggle_payload_view).pack(side="left", padx=10)

        self.enc_text_box = tk.Text(frame, height=3)
        self.enc_text_box.pack(fill="x", pady=2)

        self.enc_file_frame = ttk.Frame(frame)
        self.enc_file_path = tk.StringVar()
        ttk.Entry(self.enc_file_frame, textvariable=self.enc_file_path).pack(side="left", fill="x", expand=True)
        ttk.Button(self.enc_file_frame, text="Browse", command=self._browse_payload_file).pack(side="right", padx=(5, 0))

        # Password
        ttk.Label(frame, text="3. Encryption Password:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(4, 2))
        self.enc_pwd_var = tk.StringVar()
        self.enc_pwd_var.trace_add("write", self._on_enc_password_change)
        self.enc_pwd = ttk.Entry(frame, textvariable=self.enc_pwd_var, show="*")
        self.enc_pwd.pack(fill="x", pady=2)

        self.enc_pwd_strength_lbl = ttk.Label(frame, text="", font=("Helvetica", 8, "italic"))
        self.enc_pwd_strength_lbl.pack(anchor="w", pady=(0, 4))

        ttk.Button(frame, text="Encrypt & Embed Data", command=self._execute_encode).pack(pady=10)

    # -----------------------------
    # DECODE TAB
    # -----------------------------
    def _build_decode_tab(self, parent):
        frame = ttk.Frame(parent, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="1. Select Stego Container File:", font=("Helvetica", 10, "bold")).pack(anchor="w")
        row_type = ttk.Frame(frame)
        row_type.pack(fill="x", pady=(2, 2))
        self.dec_carrier_mode = tk.StringVar(value="Image")
        ttk.Radiobutton(row_type, text="Stego Image (.png)", variable=self.dec_carrier_mode, value="Image", command=self._reset_decode_view).pack(side="left")
        ttk.Radiobutton(row_type, text="Stego Audio (.wav)", variable=self.dec_carrier_mode, value="Audio", command=self._reset_decode_view).pack(side="left", padx=10)

        row_spath = ttk.Frame(frame)
        row_spath.pack(fill="x", pady=2)
        self.dec_stego_path = tk.StringVar()
        ttk.Entry(row_spath, textvariable=self.dec_stego_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row_spath, text="Browse", command=self._browse_decode_carrier).pack(side="right", padx=(5, 0))

        # Stego Container Preview Frame
        self.dec_preview_frame = ttk.LabelFrame(frame, text=" Stego Image Preview ", padding=6)
        self.dec_preview_frame.pack(fill="x", pady=6)

        self.dec_img_lbl = ttk.Label(self.dec_preview_frame, text="[ No Image Loaded ]", anchor="center", relief="solid", borderwidth=1)
        self.dec_img_lbl.pack(ipadx=10, ipady=10, pady=2)

        ttk.Label(frame, text="2. Decryption Password:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(4, 2))
        self.dec_pwd = ttk.Entry(frame, show="*")
        self.dec_pwd.pack(fill="x", pady=2)

        ttk.Button(frame, text="Extract & Decrypt", command=self._execute_decode).pack(pady=8)

        ttk.Label(frame, text="Extracted Content:", font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(4, 2))
        self.dec_output = tk.Text(frame, height=4)
        self.dec_output.pack(fill="both", expand=True, pady=2)

    # -----------------------------
    # EVENT HANDLERS
    # -----------------------------
    def _on_enc_password_change(self, *args):
        pwd = self.enc_pwd_var.get()
        label, color = crypto.check_password_strength(pwd)
        self.enc_pwd_strength_lbl.config(text=label, foreground=color)

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
        self._enc_carrier_photo = None
        self._enc_stego_photo = None
        self.enc_carrier_img_lbl.config(image="", text="[ No Image Loaded ]")
        self.enc_stego_img_lbl.config(image="", text="[ Waiting for Encoding ]")
        self.enc_preview_status.config(text="")

        if self.enc_carrier_mode.get() == "Image":
            self.enc_preview_frame.pack(fill="x", pady=(0, 8))
        else:
            self.enc_preview_frame.pack_forget()

    def _reset_decode_view(self):
        self.dec_stego_path.set("")
        self._dec_stego_photo = None
        self.dec_img_lbl.config(image="", text="[ No Image Loaded ]")
        if self.dec_carrier_mode.get() == "Image":
            self.dec_preview_frame.pack(fill="x", pady=6)
        else:
            self.dec_preview_frame.pack_forget()

    def _browse_encode_carrier(self):
        is_img = self.enc_carrier_mode.get() == "Image"
        ftypes = [("Image Files", "*.png *.jpg *.jpeg")] if is_img else [("Audio Files", "*.wav *.mp3")]
        path = filedialog.askopenfilename(filetypes=ftypes)
        if path:
            self.enc_carrier_path.set(path)
            try:
                cap = stego.get_image_capacity(path) if is_img else stego.get_audio_capacity(path)
                self.capacity_lbl.config(text=f"Carrier Capacity: {cap:,} bytes (~{cap / 1024:.1f} KB)")
            except Exception as e:
                self.capacity_lbl.config(text=f"Error reading file: {e}")

            if is_img:
                photo = self._create_thumbnail(path)
                if photo:
                    self._enc_carrier_photo = photo
                    self.enc_carrier_img_lbl.config(image=photo, text="")
                else:
                    self.enc_carrier_img_lbl.config(image="", text="[ Preview Unavailable ]")

                self._enc_stego_photo = None
                self.enc_stego_img_lbl.config(image="", text="[ Waiting for Encoding ]")
                self.enc_preview_status.config(text="")

    def _browse_payload_file(self):
        path = filedialog.askopenfilename(filetypes=[("All Files", "*.*")])
        if path:
            self.enc_file_path.set(path)

    def _browse_decode_carrier(self):
        is_img = self.dec_carrier_mode.get() == "Image"
        ftypes = [("Stego PNG Image", "*.png")] if is_img else [("Stego WAV Audio", "*.wav")]
        path = filedialog.askopenfilename(filetypes=ftypes)
        if path:
            self.dec_stego_path.set(path)
            if is_img:
                photo = self._create_thumbnail(path)
                if photo:
                    self._dec_stego_photo = photo
                    self.dec_img_lbl.config(image=photo, text="")
                else:
                    self.dec_img_lbl.config(image="", text="[ Preview Unavailable ]")

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

        if len(pwd) < 6:
            proceed = messagebox.askyesno(
                "Weak Password Warning",
                "The encryption password is weak (< 6 characters) and vulnerable to brute-force attacks.\n\nDo you wish to proceed anyway?"
            )
            if not proceed:
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
        ftypes = [("Lossless PNG Image", "*.png")] if is_img else [("Lossless WAV Audio", "*.wav")]
        out_path = filedialog.asksaveasfilename(defaultextension=def_ext, filetypes=ftypes)
        if not out_path:
            return

        try:
            encrypted_blob = crypto.encrypt_payload(data, fname, pwd)
            if is_img:
                saved_to = stego.hide_in_image(carrier, encrypted_blob, out_path)
                stego_photo = self._create_thumbnail(saved_to)
                if stego_photo:
                    self._enc_stego_photo = stego_photo
                    self.enc_stego_img_lbl.config(image=stego_photo, text="")
                    self.enc_preview_status.config(text="✓ Visually Identical (Lossless LSB Embedding Verified)")
            else:
                saved_to = stego.hide_in_audio(carrier, encrypted_blob, out_path)

            messagebox.showinfo("Success", f"Data embedded and saved losslessly to:\n{saved_to}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _execute_decode(self):
        stego_path = self.dec_stego_path.get().strip()
        pwd = self.dec_pwd.get()
        is_img = self.dec_carrier_mode.get() == "Image"

        if not stego_path or not os.path.exists(stego_path):
            messagebox.showerror("Error", "Select a valid stego container file.")
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