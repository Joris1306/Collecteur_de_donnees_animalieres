import io
import os
import numpy as np
from PIL import Image, ImageFile
import cv2

class image_reconstructor:
    @staticmethod
    def jpeg_buff_to_image(buf, width=None, height=None):
        """
        Robustly convert many possible JPEG buffer representations into a PIL Image.
        Handles bytes, bytearray, memoryview, hex strings, lists, numpy arrays,
        corrupted buffers, and truncated JPEGs.
        """

        ImageFile.LOAD_TRUNCATED_IMAGES = True

        def try_open(data: bytes):
            try:
                img = Image.open(io.BytesIO(data))
                img.load()
                return img
            except Exception:
                return None

        try:
            if buf is None:
                return None

            raw_bytes = None

            # ---- Normalize input to bytes ----
            if isinstance(buf, (bytes, bytearray)):
                raw_bytes = bytes(buf)
            elif isinstance(buf, memoryview):
                raw_bytes = buf.tobytes()
            elif isinstance(buf, (list, tuple)):
                raw_bytes = bytes(int(b) & 0xFF for b in buf)
            else:
                try:
                    import numpy as np
                    if isinstance(buf, np.ndarray):
                        raw_bytes = buf.tobytes()
                except Exception:
                    pass

            # ---- Direct JPEG decode ----
            if raw_bytes:
                img = try_open(raw_bytes)
                if img:
                    return img

                # ---- Recover JPEG using SOI/EOI markers ----
                soi = raw_bytes.find(b"\xff\xd8")
                eoi = raw_bytes.rfind(b"\xff\xd9")
                if soi != -1 and eoi != -1 and eoi > soi:
                    img = try_open(raw_bytes[soi:eoi + 2])
                    if img:
                        return img

            # ---- Hex string handling ----
            if isinstance(buf, str):
                hex_string = buf.replace("0x", "").replace("0X", "")
                hex_string = "".join(c for c in hex_string if c in "0123456789abcdefABCDEF")
                if len(hex_string) >= 4:
                    raw_bytes = bytes.fromhex(hex_string)
                    img = try_open(raw_bytes)
                    if img:
                        return img

            # ---- Raw RGB fallback (last resort) ----
            if raw_bytes and width and height:
                expected = width * height * 3
                if len(raw_bytes) >= expected:
                    return Image.frombytes(
                        "RGB",
                        (width, height),
                        raw_bytes[:expected]
                    )

            return None

        except Exception:
            return None
    
    @staticmethod
    def rgb565_buff_to_image(buf, width, height):
        """
        16-bit pixels, 5 bits per channel: RRRRRGGGGGBBBBB (bits 15..0)
        Map 0..31 to 0..255 using integer scaling.
        """
        data = np.frombuffer(buf, dtype=np.uint16).reshape((height, width))

        r = ((data >> 11) & 0x1F) << 3
        g = ((data >> 5) & 0x3F) << 2
        b = (data & 0x1F) << 3

        rgb = np.dstack((r, g, b)).astype(np.uint8)
        return Image.fromarray(rgb, "RGB")
    
    @staticmethod
    def rgb555_buff_to_image(buf, width, height):
        """
        16-bit pixels, 5 bits per channel: RRRRRGGGGGBBBBB (bits 15..0)
        Map 0..31 to 0..255 using integer scaling.
        """
        data = np.frombuffer(buf, dtype=np.uint16).reshape((height, width))
        r = ((data >> 10) & 0x1F) * 255 // 31
        g = ((data >> 5) & 0x1F) * 255 // 31
        b = (data & 0x1F) * 255 // 31
        rgb = np.dstack((r, g, b)).astype(np.uint8)
        return Image.fromarray(rgb, "RGB")

    @staticmethod
    def rgb888_buff_to_image(buf, width, height):
        """
        24-bit RGB, 3 bytes per pixel (R,G,B).
        Expects buf as raw bytes length == width*height*3.
        """
        arr = np.frombuffer(buf, dtype=np.uint8)
        arr = arr.reshape((height, width, 3))
        return Image.fromarray(arr, "RGB")

    @staticmethod
    def rgb444_buff_to_image(buf, width, height):
        """
        12-bit RGB packed into 16-bit units: R(4) G(4) B(4) (upper 4 bits unused or padding).
        Extract 4-bit channels and scale 0..15 -> 0..255.
        """
        data = np.frombuffer(buf, dtype=np.uint16).reshape((height, width))
        r = ((data >> 8) & 0x0F) * 255 // 15
        g = ((data >> 4) & 0x0F) * 255 // 15
        b = (data & 0x0F) * 255 // 15
        rgb = np.dstack((r, g, b)).astype(np.uint8)
        return Image.fromarray(rgb, "RGB")

    @staticmethod
    def yuv422_buff_to_image(buf, width, height):
        yuv = np.frombuffer(buf, dtype=np.uint8).reshape((height, width, 2))
        rgb = cv2.cvtColor(yuv, cv2.COLOR_YUV2RGB_YUYV)
        return Image.fromarray(rgb)

    @staticmethod
    def bayer_buff_to_image(buf, width, height, pattern="BG"):
        raw = np.frombuffer(buf, dtype=np.uint8).reshape((height, width))

        code = {
            "BG": cv2.COLOR_BAYER_BG2RGB,
            "GB": cv2.COLOR_BAYER_GB2RGB,
            "RG": cv2.COLOR_BAYER_RG2RGB,
            "GR": cv2.COLOR_BAYER_GR2RGB
        }[pattern]

        rgb = cv2.cvtColor(raw, code)
        return Image.fromarray(rgb)
    
    @staticmethod
    def gray_buff_to_image(buf, width, height):
        gray = np.frombuffer(buf, dtype=np.uint8).reshape((height, width))
        return Image.fromarray(gray, "L")
    
    @staticmethod
    def buff_to_image(buf,width,heigth,format_):
        format_to_func = {
            "JPEG": image_reconstructor.jpeg_buff_to_image,
            "RGB444": image_reconstructor.rgb444_buff_to_image,
            "RGB555": image_reconstructor.rgb555_buff_to_image,
            "RGB565": image_reconstructor.rgb565_buff_to_image,
            "RGB888": image_reconstructor.rgb888_buff_to_image,
            "YUV422": image_reconstructor.yuv422_buff_to_image,
            "BAYER": image_reconstructor.bayer_buff_to_image,
            "GRAY": image_reconstructor.gray_buff_to_image
        }

        return format_to_func[format_](buf,width,heigth)

    @staticmethod
    def levels_adjustment_filter(img):
        """
        Applies a linear levels adjustment (color scaling) where R=94, G=104, B=114
        is mapped to R=255, G=255, B=255.
        """
        # Target input color to be mapped to 255
        _current = (110, 134, 98)
        _target = (70, 87, 79)
        R_target_in = _current[0]
        G_target_in = _current[1]
        B_target_in = _current[2]
        
        # Calculate scaling factors
        S_R = _target[0] / R_target_in
        S_G = _target[1] / G_target_in
        S_B = _target[2] / B_target_in
        
        # Convert to RGB if not already
        img = img.convert("RGB")
        
        # Load the pixel data for direct manipulation
        pixels = img.load()
        width, height = img.size
        
        # Apply the scaling transformation
        for x in range(width):
            for y in range(height):
                r, g, b = pixels[x, y]
                
                # Apply scaling and clamp at 255 (full white)
                new_r = min(255, int(r * S_R))
                new_g = min(255, int(g * S_G))
                new_b = min(255, int(b * S_B))
                
                pixels[x, y] = (new_r, new_g, new_b)

        return img

    @staticmethod
    def adjust_image(img, brightness=1.0, contrast=1.0, saturation=1.0, sharpness=1.0, gamma=1.0, hue=0):
        """
        Adjust multiple image parameters for optimal correction.
        
        Args:
            img: PIL Image object
            brightness: 0.0-2.0 (1.0 = no change, <1.0 = darker, >1.0 = brighter)
            contrast: 0.0-2.0 (1.0 = no change, <1.0 = lower, >1.0 = higher)
            saturation: 0.0-2.0 (1.0 = no change, 0.0 = grayscale, >1.0 = more color)
            sharpness: 0.0-2.0 (1.0 = no change, <1.0 = blur, >1.0 = sharpen)
            gamma: 0.5-2.0 (1.0 = no change, <1.0 = brighter, >1.0 = darker)
            hue: -180 to 180 (degrees to rotate hue)
        
        Returns:
            Adjusted PIL Image
        """
        from PIL import ImageEnhance
        
        if img is None:
            return None
        
        # Ensure RGB mode
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # 1. Brightness adjustment
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        
        # 2. Contrast adjustment
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)
        
        # 3. Saturation adjustment
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(saturation)
        
        # 4. Sharpness adjustment
        if sharpness != 1.0:
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(sharpness)
        
        # 5. Gamma correction (non-linear brightness)
        if gamma != 1.0:
            img_array = np.array(img, dtype=np.float32) / 255.0
            img_array = np.power(img_array, 1.0 / gamma)
            img_array = (img_array * 255).astype(np.uint8)
            img = Image.fromarray(img_array, "RGB")
        
        # 6. Hue rotation
        if hue != 0:
            img_hsv = img.convert("HSV")
            hsv_array = np.array(img_hsv)
            # Rotate hue (0-255 maps to 0-360 degrees)
            hue_normalized = (hue % 360) * 255 / 360
            hsv_array[:, :, 0] = (hsv_array[:, :, 0] + hue_normalized) % 256
            img = Image.fromarray(hsv_array.astype(np.uint8), "HSV").convert("RGB")
        
        return img
    
    @staticmethod
    def auto_enhance(img):
        """
        Automatically enhance image with optimal defaults for wildlife photography.
        
        Args:
            img: PIL Image object
        
        Returns:
            Enhanced PIL Image
        """
        if img is None:
            return None
        
        # Optimal settings for wildlife: slight brightness boost, better contrast
        return image_reconstructor.adjust_image(
            img,
            brightness=1.1,      # 10% brighter
            contrast=1.2,        # 20% more contrast
            saturation=1.15,     # 15% more color
            sharpness=1.3,       # 30% sharper
            gamma=0.9,           # Slightly brighten shadows
            hue=0                # No hue change
        )
    
    @staticmethod
    def adjust_image_advanced(img, **kwargs):
        """
        Advanced image adjustment with histogram equalization and color correction.
        
        Args:
            img: PIL Image object
            **kwargs: Any parameters from adjust_image()
                    + 'equalize_histogram': bool (apply histogram equalization)
                    + 'denoise': bool (apply bilateral denoise)
                    + 'white_balance': bool (auto white balance)
        
        Returns:
            Adjusted PIL Image
        """
        from PIL import ImageEnhance, ImageOps
        
        if img is None:
            return None
        
        # Convert to RGB
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Extract advanced options
        equalize = kwargs.pop('equalize_histogram', False)
        denoise = kwargs.pop('denoise', False)
        white_balance = kwargs.pop('white_balance', False)
        
        # Apply histogram equalization
        if equalize:
            img_array = np.array(img)
            for i in range(3):
                img_array[:, :, i] = cv2.equalizeHist(img_array[:, :, i])
            img = Image.fromarray(img_array.astype(np.uint8), "RGB")
        
        # Apply denoising
        if denoise:
            img_array = np.array(img)
            img_array = cv2.bilateralFilter(img_array, 9, 75, 75)
            img = Image.fromarray(img_array.astype(np.uint8), "RGB")
        
        # Apply white balance
        if white_balance:
            img_array = np.array(img, dtype=np.float32)
            # Calculate mean for each channel
            mean_r = np.mean(img_array[:, :, 0])
            mean_g = np.mean(img_array[:, :, 1])
            mean_b = np.mean(img_array[:, :, 2])
            
            # Scale channels to equal mean
            img_array[:, :, 0] *= 128 / (mean_r + 1e-5)
            img_array[:, :, 1] *= 128 / (mean_g + 1e-5)
            img_array[:, :, 2] *= 128 / (mean_b + 1e-5)
            
            img_array = np.clip(img_array, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_array, "RGB")
        
        # Apply standard adjustments
        return image_reconstructor.adjust_image(img, **kwargs)

    @staticmethod
    def apply_canva_settings(
        img,
        brightness=-70,
        contrast=-22,
        highlight=-22,
        shadows=9,
        whites=-9,
        vibrance=48,
        saturation=12,
    ):
        """
        Apply adjustments approximating Canva-style parameters.

        Parameters are percentages in range [-100, 100] similar to Canva.
        - brightness: overall luminance change (mapped to PIL Brightness factor)
        - contrast: global contrast change (mapped to PIL Contrast factor)
        - saturation: global saturation change (PIL Color)
        - vibrance: boosts low-saturation pixels more than already saturated ones
        - highlight: compresses bright regions
        - shadows: lifts dark regions
        - whites: adjusts the very top end of brightness
        """

        from PIL import ImageEnhance

        if img is None:
            return None

        # Ensure RGB
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Map percentage to enhancer factors (clip to sane bounds)
        b_factor = float(np.clip(1.0 + (brightness / 100.0), 0.3, 1.7))
        c_factor = float(np.clip(1.0 + (contrast / 100.0), 0.3, 1.7))
        s_factor = float(np.clip(1.0 + (saturation / 100.0), 0.0, 2.0))

        # Apply base adjustments via PIL enhancers
        img = ImageEnhance.Brightness(img).enhance(b_factor)
        img = ImageEnhance.Contrast(img).enhance(c_factor)
        img = ImageEnhance.Color(img).enhance(s_factor)

        # Convert to HSV for vibrance and tone-mapping operations
        hsv = img.convert("HSV")
        hsv_arr = np.array(hsv, dtype=np.float32)
        h = hsv_arr[:, :, 0]
        s = hsv_arr[:, :, 1] / 255.0
        v = hsv_arr[:, :, 2] / 255.0

        # Vibrance: increase saturation more for low-saturated pixels
        vib_amt = np.clip(vibrance / 100.0, -1.0, 1.0)
        if vib_amt != 0:
            s = np.clip(s + vib_amt * (1.0 - s), 0.0, 1.0)

        # Tone mapping thresholds
        shadow_t = 0.25
        highlight_t = 0.75
        whites_t = 0.90

        # Shadows: lift dark regions
        sh_amt = np.clip(shadows / 100.0, -1.0, 1.0)
        if sh_amt != 0:
            mask = v < shadow_t
            v[mask] = np.clip(v[mask] + sh_amt * (shadow_t - v[mask]), 0.0, 1.0)

        # Highlights: compress bright regions (negative values reduce highlights)
        hi_amt = np.clip(-highlight / 100.0, 0.0, 1.0)  # make positive when highlight is negative
        if hi_amt != 0:
            mask = v > highlight_t
            v[mask] = np.clip(v[mask] - hi_amt * (v[mask] - highlight_t), 0.0, 1.0)

        # Whites: adjust very bright end
        # Negative -> reduce whites, Positive -> boost whites
        w_amt = np.clip(whites / 100.0, -1.0, 1.0)
        mask = v > whites_t
        if np.any(mask):
            if w_amt < 0:
                v[mask] = np.clip(v[mask] + w_amt * (v[mask] - whites_t), 0.0, 1.0)
            elif w_amt > 0:
                v[mask] = np.clip(v[mask] + w_amt * (1.0 - v[mask]), 0.0, 1.0)

        # Recompose HSV back to image
        hsv_arr[:, :, 1] = (s * 255.0)
        hsv_arr[:, :, 2] = (v * 255.0)
        out = Image.fromarray(np.clip(hsv_arr, 0, 255).astype(np.uint8), "HSV").convert("RGB")

        return out

    @staticmethod
    def _gray_world_white_balance(img):
        """Simple gray-world white balance in RGB."""
        arr = np.asarray(img).astype(np.float32)
        # Compute per-channel gains to equalize means
        means = arr.reshape(-1, 3).mean(axis=0)
        overall = means.mean() + 1e-6
        gains = overall / (means + 1e-6)
        arr *= gains
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, 'RGB')

    @staticmethod
    def _lab_clahe(img, clipLimit=1.5, tileGridSize=(8,8)):
        """Gentle CLAHE on L channel in LAB to avoid posterization."""
        lab = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2LAB)
        L, A, B = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
        L = clahe.apply(L)
        lab = cv2.merge([L, A, B])
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return Image.fromarray(rgb)

    @staticmethod
    def _lab_tone_curve(img, b_factor=1.0, c_factor=1.0, hi_reduce=0.0, sh_lift=0.0, whites=0.0):
        """Adjust brightness/contrast and soft highlights/shadows in LAB L channel."""
        lab = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2LAB).astype(np.float32)
        L = lab[:, :, 0] / 255.0
        # brightness (scale) and contrast (around mean)
        meanL = L.mean()
        L = np.clip((L * b_factor - meanL) * c_factor + meanL, 0.0, 1.0)

        # smoothstep helper
        def smoothstep(edge0, edge1, x):
            t = np.clip((x - edge0) / (edge1 - edge0 + 1e-6), 0.0, 1.0)
            return t * t * (3.0 - 2.0 * t)

        # reduce highlights softly above 0.75
        if hi_reduce > 0.0:
            t_hi = smoothstep(0.75, 1.0, L)
            L = np.clip(L - hi_reduce * t_hi * (L - 0.75), 0.0, 1.0)

        # lift shadows softly below 0.25
        if sh_lift > 0.0:
            t_sh = smoothstep(0.0, 0.25, 0.25 - L)
            L = np.clip(L + sh_lift * t_sh * (0.25 - L), 0.0, 1.0)

        # whites adjustment on top 10%
        if whites != 0.0:
            mask = L > 0.9
            if np.any(mask):
                if whites < 0:
                    L[mask] = np.clip(L[mask] + whites * (L[mask] - 0.9), 0.0, 1.0)
                else:
                    L[mask] = np.clip(L[mask] + whites * (1.0 - L[mask]), 0.0, 1.0)

        lab[:, :, 0] = (L * 255.0)
        rgb = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
        return Image.fromarray(rgb)

    @staticmethod
    def smooth_colors(img, method='bilateral', strength=2):
        """
        Smooth high-frequency color changes (filter noise) while preserving edges.
        
        Args:
            img: PIL Image
            method: 'bilateral', 'gaussian', 'nlm' (non-local means), 'median'
            strength: 1=light, 2=medium, 3=strong, 4=very strong
        
        Returns:
            Smoothed PIL Image
        """
        if img is None:
            return None
        
        # Ensure RGB mode
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        arr = np.array(img, dtype=np.uint8)
        
        if method == 'bilateral':
            # Bilateral filter: smooths while preserving edges
            # d: diameter of pixel neighborhood
            # sigmaColor: filter sigma in color space (larger = more colors mixed)
            # sigmaSpace: filter sigma in coordinate space (larger = farther pixels influence)
            params = {
                1: (5, 30, 30),
                2: (7, 50, 50),
                3: (9, 75, 75),
                4: (11, 100, 100)
            }
            d, sc, ss = params.get(strength, (7, 50, 50))
            arr = cv2.bilateralFilter(arr, d, sc, ss)
        
        elif method == 'gaussian':
            # Gaussian blur: uniform smoothing
            ksize = {1: 3, 2: 5, 3: 7, 4: 9}.get(strength, 5)
            arr = cv2.GaussianBlur(arr, (ksize, ksize), 0)
        
        elif method == 'nlm':
            # Non-local means: excellent for texture preservation
            h = {1: 3, 2: 6, 3: 10, 4: 15}.get(strength, 6)
            arr = cv2.fastNlMeansDenoisingColored(arr, None, h, h, 7, 21)
        
        elif method == 'median':
            # Median filter: good for salt-and-pepper noise
            ksize = {1: 3, 2: 5, 3: 7, 4: 9}.get(strength, 5)
            arr = cv2.medianBlur(arr, ksize)
        
        return Image.fromarray(arr, 'RGB')

    @staticmethod
    def apply_canva_settings_safe(
        img,
        brightness=-70,
        contrast=-22,
        highlight=-22,
        shadows=9,
        whites=-9,
        vibrance=48,
        saturation=12,
        smooth=2,
    ):
        """
        Safer, artifact-free version of Canva mapping using LAB tone curve,
        gentle CLAHE and mild saturation/vibrance.
        
        Args:
            smooth: 0=off, 1=light, 2=medium, 3=strong, 4=very strong bilateral filtering
        """
        if img is None:
            return None

        # 0) Optional smoothing to remove high-frequency noise
        if smooth > 0:
            img = image_reconstructor.smooth_colors(img, method='bilateral', strength=smooth)

        # 1) White balance (gray-world) to remove color casts
        img = image_reconstructor._gray_world_white_balance(img)

        # 2) Gentle local contrast via CLAHE on L
        img = image_reconstructor._lab_clahe(img, clipLimit=1.3, tileGridSize=(8,8))

        # 3) LAB tone curve for brightness/contrast/highlights/shadows/whites
        # Scale down the adjustments - Canva uses different scale than our implementation
        b_factor = float(np.clip(1.0 + (brightness / 200.0), 0.6, 1.4))  # Less aggressive
        c_factor = float(np.clip(1.0 + (contrast / 150.0), 0.7, 1.5))    # Less aggressive
        hi_reduce = float(np.clip(-highlight / 200.0, 0.0, 0.5))         # Gentler
        sh_lift = float(np.clip(shadows / 200.0, 0.0, 0.5))              # Gentler
        whites_amt = float(np.clip(whites / 200.0, -0.4, 0.4))           # Gentler
        img = image_reconstructor._lab_tone_curve(img, b_factor, c_factor, hi_reduce, sh_lift, whites_amt)

        # 4) Mild saturation + vibrance in HSV (avoid overshoot)
        hsv = img.convert('HSV')
        hsv_arr = np.array(hsv, dtype=np.float32)
        S = hsv_arr[:, :, 1] / 255.0
        # saturation
        s_factor = float(np.clip(1.0 + (saturation / 200.0), 0.8, 1.3))
        S = np.clip(S * s_factor, 0.0, 1.0)
        # vibrance (milder than before)
        vib_amt = float(np.clip(vibrance / 300.0, -0.5, 0.5))
        S = np.clip(S + vib_amt * (1.0 - S), 0.0, 1.0)
        hsv_arr[:, :, 1] = (S * 255.0)
        img = Image.fromarray(hsv_arr.astype(np.uint8), 'HSV').convert('RGB')

        return img

    @staticmethod
    def apply_canva_preset(img, smooth=2):
        """
        Apply user's Canva parameters as a preset (safe pipeline).
        
        Args:
            img: PIL Image
            smooth: 0=no smoothing, 1=light, 2=medium (default), 3=strong, 4=very strong
        """
        return image_reconstructor.apply_canva_settings_safe(
            img,
            brightness=-70,
            contrast=-22,
            highlight=-22,
            shadows=9,
            whites=-9,
            vibrance=48,
            saturation=12,
            smooth=smooth,
        )
    
    @staticmethod
    def apply_balanced_correction(img, smooth=2):
        """
        Apply a balanced correction optimized for washed-out camera images.
        Less aggressive than Canva preset, focuses on recovering details naturally.
        
        Args:
            img: PIL Image
            smooth: 0=no smoothing, 1=light, 2=medium (default), 3=strong, 4=very strong
        """
        return image_reconstructor.apply_canva_settings_safe(
            img,
            brightness=-35,      # Moderate darkening
            contrast=-10,        # Slight contrast reduction to avoid harshness
            highlight=-30,       # Recover highlights
            shadows=15,          # Lift shadows more
            whites=-5,           # Slight white compression
            vibrance=30,         # Moderate color boost
            saturation=8,        # Gentle saturation
            smooth=smooth,
        )
    
    @staticmethod
    def analyze_image_quality(img):
        """
        Analyze image quality and return recommended adjustment parameters.
        
        Args:
            img: PIL Image object
        
        Returns:
            dict with recommended parameters
        """
        if img is None:
            return {}
        
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        # Calculate statistics
        mean_brightness = np.mean(img_array)
        std_brightness = np.std(img_array)
        
        # Calculate per-channel means
        r_mean = np.mean(img_array[:, :, 0])
        g_mean = np.mean(img_array[:, :, 1])
        b_mean = np.mean(img_array[:, :, 2])
        
        # Calculate contrast (using standard deviation)
        contrast_level = std_brightness
        
        # Detect color cast
        max_channel = max(r_mean, g_mean, b_mean)
        min_channel = min(r_mean, g_mean, b_mean)
        color_imbalance = max_channel - min_channel
        
        recommendations = {
            "mean_brightness": float(mean_brightness),
            "contrast": float(contrast_level),
            "color_imbalance": float(color_imbalance),
            "r_mean": float(r_mean),
            "g_mean": float(g_mean),
            "b_mean": float(b_mean)
        }
        
        return recommendations
    
    @staticmethod
    def auto_correct_image(img):
        """
        Automatically correct image based on analysis of overexposure, low contrast, and color imbalance.
        Optimized for washed-out camera feed images.
        
        Args:
            img: PIL Image object
        
        Returns:
            Corrected PIL Image
        """
        if img is None:
            return None
        
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Analyze image
        analysis = image_reconstructor.analyze_image_quality(img)
        
        # Determine adjustment parameters based on analysis
        params = {
            "equalize_histogram": True,  # Better detail recovery
            "denoise": True,             # Reduce noise in poor lighting
            "white_balance": True,       # Correct color cast
        }
        
        # If very washed out (low contrast and high brightness)
        if analysis["mean_brightness"] > 0.65 and analysis["contrast"] < 0.15:
            # Strong overexposure recovery
            params.update({
                "brightness": 0.85,       # Reduce brightness
                "contrast": 1.8,          # Strong contrast boost
                "saturation": 1.3,        # Restore colors
                "sharpness": 1.5,         # Sharpen details
                "gamma": 0.85             # Darken highlights
            })
        # If moderately bright with low contrast
        elif analysis["mean_brightness"] > 0.55 and analysis["contrast"] < 0.18:
            params.update({
                "brightness": 0.9,
                "contrast": 1.5,
                "saturation": 1.2,
                "sharpness": 1.3,
                "gamma": 0.9
            })
        # If dark with low contrast
        elif analysis["mean_brightness"] < 0.4 and analysis["contrast"] < 0.15:
            params.update({
                "brightness": 1.25,       # Boost brightness
                "contrast": 1.6,
                "saturation": 1.15,
                "sharpness": 1.3,
                "gamma": 0.8              # Lift shadows
            })
        # Normal case with mild adjustments
        else:
            params.update({
                "brightness": 1.05,
                "contrast": 1.2,
                "saturation": 1.1,
                "sharpness": 1.2,
                "gamma": 0.95
            })
        
        return image_reconstructor.adjust_image_advanced(img, **params)
    
    @staticmethod
    def apply_presets(img, preset="wildlife"):
        """
        Apply predefined adjustment presets optimized for different scenarios.
        
        Args:
            img: PIL Image object
            preset: "wildlife", "overexposed", "dark", "foggy", "clean"
        
        Returns:
            Adjusted PIL Image
        """
        presets = {
            "wildlife": {
                "brightness": 1.1,
                "contrast": 1.2,
                "saturation": 1.15,
                "sharpness": 1.1,
                "gamma": 0.9,
                "equalize_histogram": False,
                "denoise": False,
                "white_balance": False
            },
            "overexposed": {
                "brightness": 0.8,
                "contrast": 1.8,
                "saturation": 1.25,
                "sharpness": 1.05,
                "gamma": 0.8,
                "equalize_histogram": True,
                "denoise": True,
                "white_balance": True
            },
            "dark": {
                "brightness": 1.3,
                "contrast": 1.4,
                "saturation": 1.1,
                "sharpness": 1.2,
                "gamma": 0.75,
                "equalize_histogram": True,
                "denoise": True,
                "white_balance": False
            },
            "foggy": {
                "brightness": 1.15,
                "contrast": 1.6,
                "saturation": 1.2,
                "sharpness": 1.1,
                "gamma": 0.85,
                "equalize_histogram": False,
                "denoise": False,
                "white_balance": True
            },
            "clean": {
                "brightness": 1.0,
                "contrast": 1.1,
                "saturation": 1.05,
                "sharpness": 1.0,
                "gamma": 1.0,
                "equalize_histogram": False,
                "denoise": False,
                "white_balance": False
            },
            "balanced": {
                "brightness": 0.9,
                "contrast": 1.5,
                "saturation": 1.15,
                "sharpness": 1.0,
                "gamma": 0.85,
                "equalize_histogram": True,
                "denoise": False,
                "white_balance": True
            }
        }
        
        if preset not in presets:
            preset = "wildlife"
        
        return image_reconstructor.adjust_image_advanced(img, **presets[preset])


def main():
    # Import BASE_PATH locally to avoid circular imports
    # (only needed when script runs directly, not when imported)
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utlitaires import BASE_PATH
    
    image_example = Image.open(os.path.join(BASE_PATH, "SAMPLE", "image_src.jpg"))

    image_example.show()

    adjusted_img = image_reconstructor.adjust_image(image_example, brightness=1.2, contrast=1.5)
    adjusted_img.show()
    # Analyze and auto-correct the image
    analysis = image_reconstructor.analyze_image_quality(image_example)
    print("Image Quality Analysis:")
    print(f"  Mean Brightness: {analysis['mean_brightness']:.3f}")
    print(f"  Contrast Level: {analysis['contrast']:.3f}")
    print(f"  Color Imbalance: {analysis['color_imbalance']:.3f}")
    print(f"  RGB Means: R={analysis['r_mean']:.3f}, G={analysis['g_mean']:.3f}, B={analysis['b_mean']:.3f}")
    
    print("\nApplying auto correction...")
    corrected = image_reconstructor.auto_correct_image(image_example)
    # corrected.show()
    # corrected.save(os.path.join(BASE_PATH, "SAMPLE", "corrected_image.jpg"))

    print("Applying balanced preset...")
    preset_corrected = image_reconstructor.apply_presets(image_example, "balanced")
    # preset_corrected.show()

    print("Applying Canva preset...")
    canva_corrected = image_reconstructor.apply_canva_preset(image_example)
    canva_corrected.show()
    canva_corrected.save(os.path.join(BASE_PATH, "SAMPLE", "corrected_image.jpg"))
    canva_corrected_smooth = image_reconstructor.apply_canva_preset(canva_corrected, smooth=3)
    canva_corrected_smooth.show()

    print("Done! Images ready for display.")

if __name__ == "__main__":
    main()