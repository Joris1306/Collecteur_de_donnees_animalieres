import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import os
import threading
from typing import List

BASE_PATH = os.path.dirname(__file__)

# =========================
# Blur detection functions
# =========================


def laplacian_method(img_gray):
    lap = cv2.Laplacian(img_gray, cv2.CV_64F)
    return lap.var()


def tenengrad_method(img_gray):
    gx = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0)
    gy = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1)
    g = gx**2 + gy**2
    return np.mean(g)


def fft_method(img_gray, radius=10):
    f = np.fft.fft2(img_gray)
    fshift = np.fft.fftshift(f)
    magnitude_spectrum = np.abs(fshift)
    rows, cols = img_gray.shape
    crow, ccol = rows // 2, cols // 2
    mask = np.ones((rows, cols), np.uint8)
    cv2.circle(mask, (ccol, crow), radius, 0, -1)
    high_freq = magnitude_spectrum * mask
    total_energy = np.sum(magnitude_spectrum)
    high_freq_energy = np.sum(high_freq)
    return high_freq_energy / total_energy


# =========================
# GUI Class
# =========================


class BlurHMI:
    def __init__(self, root, static_images=None, initial_threshold=None):
        self.root = root
        self.root.title("Blur Detection HMI")

        # busy flag
        self._busy = False
        # keep refs to controls to disable/enable
        self.load_buttons: List[tk.Button] = []
        self.combobox = None
        self.scale = None
        # store previous combobox state for restore
        self._combobox_prev_state = "readonly"

        # Images
        self.img_paths = [None, None]
        self.img_gray = [None, None]
        self.tk_images = [None, None]

        # Method and threshold
        self.method_var = tk.StringVar(value="Laplacian")
        self.threshold_var = tk.DoubleVar(value=100)

        # react to programmatic changes as well
        self.method_var.trace_add("write", lambda *args: self.check_blur())
        # Do NOT call check_blur on every threshold change while dragging.
        # We'll apply the threshold on release to avoid repeated heavy calls.
        self._pending_threshold = float(self.threshold_var.get())

        # optionally apply initial values / static images
        if initial_threshold is not None:
            self.threshold_var.set(float(initial_threshold))
        self.create_widgets()
        if static_images:
            # static_images expected as iterable of paths, e.g. [path1, path2]
            for i, p in enumerate(static_images[:2]):
                if p:
                    self.set_static_image(i, p)
        else:
            # ensure initial check (will show "Not loaded")
            self.check_blur()

    def create_widgets(self):
        # Top frame: Load buttons
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=5)
        btn1 = tk.Button(
            top_frame, text="Load Image 1", command=lambda: self.load_image(0)
        )
        btn1.pack(side=tk.LEFT, padx=5)
        btn2 = tk.Button(
            top_frame, text="Load Image 2", command=lambda: self.load_image(1)
        )
        btn2.pack(side=tk.LEFT, padx=5)
        self.load_buttons = [btn1, btn2]

        # Method selection
        method_frame = tk.Frame(self.root)
        method_frame.pack(pady=5)
        tk.Label(method_frame, text="Method:").pack(side=tk.LEFT)
        self.combobox = ttk.Combobox(
            method_frame,
            textvariable=self.method_var,
            values=["Laplacian", "Tenengrad", "FFT"],
            state="readonly",
        )
        self.combobox.pack(side=tk.LEFT, padx=5)
        # Call check_blur when user selects a new item
        self.combobox.bind("<<ComboboxSelected>>", lambda event: self.check_blur())
        # Optional: also react when the variable changes programmatically
        self.method_var.trace_add("write", lambda *args: self.check_blur())
        self.root.bind("<Return>", lambda event: self.check_blur())

        # Threshold slider
        threshold_frame = tk.Frame(self.root)
        threshold_frame.pack(pady=5)
        tk.Label(threshold_frame, text="Threshold:").pack(side=tk.LEFT)
        # Create scale and update a pending value during drag via command.
        self.scale = tk.Scale(
            threshold_frame,
            from_=1,
            to=1000,
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            length=300,
            command=self._on_threshold_change,
        )
        self.scale.pack(side=tk.LEFT)
        # Call check_blur only when the user releases the mouse button
        self.scale.bind("<ButtonRelease-1>", lambda e: self._apply_threshold())
        # Also apply when user changes value with keyboard
        self.scale.bind("<KeyRelease>", lambda e: self._apply_threshold())

        # Images display
        self.img_frame = tk.Frame(self.root)
        self.img_frame.pack(pady=10)
        self.labels = []
        for i in range(2):
            lbl = tk.Label(self.img_frame, text=f"Image {i+1} not loaded")
            lbl.pack(side=tk.LEFT, padx=10)
            self.labels.append(lbl)

        # Result label
        self.result_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.result_label.pack(pady=5)

    def load_image(self, index):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.png *.jpeg")]
        )
        if path:
            self._load_image_from_path(index, path)

    def _load_image_from_path(self, index, path):
        """Load image from given path (used by file dialog and for static images)."""
        try:
            img = cv2.imread(path)
            if img is None:
                return False
            self.img_paths[index] = path
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            self.img_gray[index] = img_gray

            # Convert to PIL and display
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            pil_img = pil_img.resize((300, 300))  # Resize for display
            tk_img = ImageTk.PhotoImage(pil_img)
            self.tk_images[index] = tk_img
            self.labels[index].config(image=tk_img, text="")
            self.check_blur()
            return True
        except Exception:
            return False

    def set_static_image(self, index, path):
        """Public setter to load an image programmatically (static image)."""
        return self._load_image_from_path(index, path)

    def set_threshold(self, value):
        """Programmatically set threshold (will trigger check_blur via trace)."""
        # Programmatic changes should apply immediately
        self.threshold_var.set(float(value))
        self.check_blur()

    def _on_threshold_change(self, val):
        """Called continuously while dragging: store pending value but don't run heavy check."""
        try:
            self._pending_threshold = float(val)
        except Exception:
            pass

    def _apply_threshold(self):
        """Apply the pending threshold and run the expensive check (called on release)."""
        self.threshold_var.set(self._pending_threshold)
        self.check_blur()

    def set_method(self, method_name):
        """Programmatically set method (will trigger check_blur via trace)."""
        self.method_var.set(method_name)

    def check_blur(self):
        # Start background computation to avoid freezing UI.
        if self._busy:
            return
        method = self.method_var.get()
        threshold = self.threshold_var.get()
        imgs = list(self.img_gray)  # shallow copy
        self._start_busy()
        thread = threading.Thread(
            target=self._compute_blur_thread,
            args=(method, threshold, imgs),
            daemon=True,
        )
        thread.start()

    def _compute_blur_thread(self, method, threshold, imgs):
        results_text = []
        try:
            for i, img in enumerate(imgs):
                if img is None:
                    results_text.append(f"Image {i+1}: Not loaded")
                    continue
                if method == "Laplacian":
                    score = laplacian_method(img)
                elif method == "Tenengrad":
                    score = tenengrad_method(img)
                else:
                    score = fft_method(img)
                    score *= 1000
                blurry = score < threshold
                results_text.append(
                    f"Image {i+1}: {'Blurry' if blurry else 'Sharp'} (Score={score:.2f})"
                )
        except Exception as e:
            results_text = [f"Error: {e}"]
        # Update UI in main thread
        self.root.after(0, lambda: self._on_blur_done(results_text))

    def _on_blur_done(self, results_text):
        if hasattr(self, "result_label"):
            self.result_label.config(text="\n".join(results_text))
        self._stop_busy()

    def _start_busy(self):
        """Disable controls and show busy cursor/grab input."""
        self._busy = True
        # disable buttons
        for b in self.load_buttons:
            b.config(state="disabled")
        # disable combobox
        if self.combobox:
            try:
                self._combobox_prev_state = self.combobox.cget("state")
            except Exception:
                self._combobox_prev_state = "readonly"
            self.combobox.config(state="disabled")
        # disable scale
        if self.scale:
            self.scale.config(state="disabled")
        # busy cursor and grab
        try:
            self.root.config(cursor="watch")
            self.root.update_idletasks()
            self.root.grab_set()
        except Exception:
            pass

    def _stop_busy(self):
        """Restore controls and cursor."""
        # restore UI
        for b in self.load_buttons:
            b.config(state="normal")
        if self.combobox:
            self.combobox.config(state=self._combobox_prev_state or "readonly")
        if self.scale:
            self.scale.config(state="normal")
        try:
            self.root.config(cursor="")
            self.root.update_idletasks()
            try:
                self.root.grab_release()
            except Exception:
                pass
        except Exception:
            pass
        self._busy = False


# =========================
# Run GUI
# =========================

if __name__ == "__main__":
    root = tk.Tk()
    app = BlurHMI(
        root,
        [os.path.join(BASE_PATH, "CIBLE.PNG"), os.path.join(BASE_PATH, "IMG_6897.png")],
        initial_threshold=100,
    )
    root.mainloop()
