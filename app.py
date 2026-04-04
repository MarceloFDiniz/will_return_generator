import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import requests
from io import BytesIO
import emoji
import math
from datetime import datetime, date, timedelta

# =====================================================
# Página
# =====================================================

st.set_page_config(page_title="Will Return Generator", layout="centered")

st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; }
    .stButton > button {
        width: 100%;
        height: 3em;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# Estado inicial
# =====================================================

defaults = {
    "fps": 12,
    "fade_ms": 1100,
    "delay_ms": 2800,
    "resolution": "1280x720",
    "font_name": "Oswald Regular 400 (default)",
    "bg_hex": "#000000",
    "text_hex": "#FFFFFF",
    "resolution_mode": "preset",
    "res_width": 1280,
    "res_height": 720,
    "countdown_enabled": False,
    "countdown_date": None,
    "countdown_duration": 3,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

MAX_ANIMATED_PREVIEW_WIDTH = 1280

# =====================================================
# Fontes
# =====================================================

FONT_OPTIONS = {
    "Oswald Regular 400 (default)": {"path": "fonts/Oswald-Regular.ttf", "tracking": 0.22},
    "Roboto Condensed Thin 100": {"path": "fonts/RobotoCondensed-Thin.ttf", "tracking": 0.10},
    "Roboto Condensed Light 300": {"path": "fonts/RobotoCondensed-Light.ttf", "tracking": 0.12},
    "Roboto Condensed Regular Italic 400": {"path": "fonts/RobotoCondensed-Italic.ttf", "tracking": 0.12},
    "Roboto Condensed Black 900": {"path": "fonts/RobotoCondensed-Black.ttf", "tracking": 0.08},
    "Inter Tight Regular 400": {"path": "fonts/InterTight-Regular.ttf", "tracking": 0.05},
    "Inter Tight Medium 500": {"path": "fonts/InterTight-Medium.ttf", "tracking": 0.05},
    "Inter Tight Bold 700": {"path": "fonts/InterTight-Bold.ttf", "tracking": 0.04},
}

# =====================================================
# Presets
# =====================================================

PRESETS = {
    "Marvel Original (Closest Match)": {
        "fps": 12,
        "fade_ms": 1100,
        "delay_ms": 2800,
        "resolution": "1280x720",
        "font": "Oswald Regular 400 (default)",
        "bg": "#000000",
        "text": "#FFFFFF",
    },
    "Zack Snyder Mode": {
        "fps": 6,
        "fade_ms": 2500,
        "delay_ms": 6000,
        "resolution": "1280x720",
        "font": "Oswald Regular 400 (default)",
        "bg": "#000000",
        "text": "#FFFFFF",
    },
    "Alta Qualidade": {
        "fps": 15,
        "fade_ms": 1300,
        "delay_ms": 3200,
        "resolution": "1280x720",
        "font": None,
    },
    "Leve (WhatsApp)": {
        "fps": 8,
        "fade_ms": 700,
        "delay_ms": 1500,
        "resolution": "640x360",
        "font": None,
    },
}

# =====================================================
# Emojis
# =====================================================

EMOJI_CACHE = {}

def split_text_and_emojis(text):
    if not text:
        return []
    tokens = []
    emojis = emoji.emoji_list(text)
    last_idx = 0
    for match in emojis:
        start, end = match['match_start'], match['match_end']
        if start > last_idx:
            tokens.extend(list(text[last_idx:start]))
        tokens.append(match['emoji'])
        last_idx = end
    if last_idx < len(text):
        tokens.extend(list(text[last_idx:]))
    return tokens

def is_emoji(ch):
    return emoji.is_emoji(ch) if hasattr(emoji, 'is_emoji') else ch in emoji.EMOJI_DATA

def load_emoji_image(ch, size):
    key = (ch, size)
    if key in EMOJI_CACHE:
        return EMOJI_CACHE[key]

    codepoints = [f"{ord(c):x}" for c in ch if ord(c) != 0xfe0f]
    if not codepoints:
        return None
    codepoint = "-".join(codepoints)
    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{codepoint}.png"

    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return None

    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    EMOJI_CACHE[key] = img
    return img

# =====================================================
# Texto / fonte
# =====================================================

def measure_text(draw, text, font, tracking):
    width = 0
    tracking_px = int(font.size * tracking)
    for ch in split_text_and_emojis(text):
        if is_emoji(ch):
            width += font.size + tracking_px
        elif ch == " ":
            width += draw.textbbox((0, 0), " ", font=font)[2]
        else:
            cw = draw.textbbox((0, 0), ch, font=font)[2]
            width += cw + tracking_px
    return width

def fit_font(draw, text, font_path, max_width, tracking):
    size = 50
    while size >= 18:
        font = ImageFont.truetype(font_path, size)
        if measure_text(draw, text, font, tracking) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 18)

def fit_timer_font(parts, font_path, max_width, max_height):
    size = 90
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    while size >= 18:
        try:
            val_font = ImageFont.truetype(font_path, size)
            label_font = ImageFont.truetype(font_path, max(10, int(size * 0.35)))
        except Exception:
            break
        
        cols_w = []
        for val, lbl in parts:
            vw = draw.textbbox((0, 0), val, font=val_font)[2] - draw.textbbox((0, 0), val, font=val_font)[0]
            lw = draw.textbbox((0, 0), lbl, font=label_font)[2] - draw.textbbox((0, 0), lbl, font=label_font)[0]
            cols_w.append(max(vw, lw))
            
        colon_vw = draw.textbbox((0, 0), ":", font=val_font)[2] - draw.textbbox((0, 0), ":", font=val_font)[0]
        colon_lw = draw.textbbox((0, 0), ":", font=label_font)[2] - draw.textbbox((0, 0), ":", font=label_font)[0]
        margin = int(size * 0.15)
        sep_w = max(colon_vw, colon_lw) + margin * 2
        total_w = sum(cols_w) + max(0, len(parts) - 1) * sep_w
        
        v_bbox = draw.textbbox((0, 0), "0", font=val_font)
        l_bbox = draw.textbbox((0, 0), "A", font=label_font)
        total_h = (v_bbox[3] - v_bbox[1]) + margin + (l_bbox[3] - l_bbox[1])
        
        if total_w <= max_width and total_h <= max_height:
            return val_font
        size -= 2
    return ImageFont.truetype(font_path, 18)

# =====================================================
# Renderização dos blocos
# =====================================================

def render_blocks(blocks_words, visible_blocks, font, tracking, width, height, bg, color, final_width, fade_alpha=1.0):
    img = Image.new("RGBA", (width, height), bg + (255,))
    draw = ImageDraw.Draw(img)

    text_h = draw.textbbox((0, 0), "X", font=font)[3]
    x = (width - final_width) // 2
    y = (height - text_h) // 2

    cursor = x
    tracking_px = int(font.size * tracking)
    emoji_size = font.size

    for i in range(visible_blocks):
        if i > 0:
            cursor += draw.textbbox((0, 0), " ", font=font)[2]

        alpha = int(255 * fade_alpha) if i == visible_blocks - 1 else 255

        for word in blocks_words[i]:
            for ch in split_text_and_emojis(word):
                if is_emoji(ch):
                    e = load_emoji_image(ch, emoji_size)
                    if e:
                        e = e.copy()
                        e.putalpha(alpha)
                        img.paste(e, (cursor, y), e)
                        cursor += emoji_size + tracking_px
                else:
                    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    od = ImageDraw.Draw(overlay)
                    od.text((cursor, y), ch, font=font, fill=color + (alpha,))
                    img = Image.alpha_composite(img, overlay)
                    cw = draw.textbbox((0, 0), ch, font=font)[2]
                    cursor += cw + tracking_px

            cursor += draw.textbbox((0, 0), " ", font=font)[2]

    return img

# =====================================================
# Renderização da contagem regressiva (MARVEL-like)
# =====================================================

def get_countdown_parts(delta):
    if delta.total_seconds() < 0:
        return [("00", "HOURS"), ("00", "MINUTES"), ("00", "SECONDS")]

    total_days = delta.days
    seconds = delta.seconds

    years = total_days // 365
    rem_days = total_days % 365
    months = rem_days // 30
    days = rem_days % 30

    hours = seconds // 3600
    rem_sec = seconds % 3600
    minutes = rem_sec // 60
    secs = rem_sec % 60

    parts = []
    if years > 0:
        parts.append((f"{years:02}", "YEARS"))
    if months > 0 or years > 0:
        parts.append((f"{months:02}", "MONTHS"))
    if days > 0 or months > 0 or years > 0:
        parts.append((f"{days:02}", "DAYS"))

    parts.append((f"{hours:02}", "HOURS"))
    parts.append((f"{minutes:02}", "MINUTES"))
    parts.append((f"{secs:02}", "SECONDS"))

    return parts

def render_timer_frame(parts, font, font_path, width, height, bg, color):
    img = Image.new("RGBA", (width, height), bg + (255,))
    draw = ImageDraw.Draw(img)

    try:
        label_font = ImageFont.truetype(font_path, max(10, int(font.size * 0.35)))
        val_font = font
    except Exception:
        label_font = font
        val_font = font

    cols = []
    for val, lbl in parts:
        v_box = draw.textbbox((0, 0), val, font=val_font)
        vw = v_box[2] - v_box[0]
        vl = v_box[0]
        
        l_box = draw.textbbox((0, 0), lbl, font=label_font)
        lw = l_box[2] - l_box[0]
        ll = l_box[0]
        
        cols.append({
            "val": val, "lbl": lbl,
            "vw": vw, "vl": vl,
            "lw": lw, "ll": ll,
            "col_w": max(vw, lw)
        })

    c_box_v = draw.textbbox((0, 0), ":", font=val_font)
    colon_vw = c_box_v[2] - c_box_v[0]
    colon_vl = c_box_v[0]
    
    c_box_l = draw.textbbox((0, 0), ":", font=label_font)
    colon_lw = c_box_l[2] - c_box_l[0]
    colon_ll = c_box_l[0]
    
    margin = int(val_font.size * 0.15)
    sep_w = max(colon_vw, colon_lw) + margin * 2
    num_seps = len(parts) - 1

    total_w = sum(c["col_w"] for c in cols) + num_seps * sep_w

    v_bbox = draw.textbbox((0, 0), "0", font=val_font)
    v_top, v_bottom = v_bbox[1], v_bbox[3]
    val_h = v_bottom - v_top

    l_bbox = draw.textbbox((0, 0), "A", font=label_font)
    l_top, l_bottom = l_bbox[1], l_bbox[3]
    lbl_h = l_bottom - l_top

    spacing = int(val_font.size * 0.15)
    total_height = val_h + spacing + lbl_h

    start_x = (width - total_w) // 2
    start_y = (height - total_height) // 2

    curr_x = start_x
    for i, c in enumerate(cols):
        vx = curr_x + (c["col_w"] - c["vw"]) // 2
        draw.text((vx - c["vl"], start_y - v_top), c["val"], font=val_font, fill=color)

        lx = curr_x + (c["col_w"] - c["lw"]) // 2
        lbl_y = start_y + val_h + spacing - l_top
        draw.text((lx - c["ll"], lbl_y), c["lbl"], font=label_font, fill=color)

        curr_x += c["col_w"]

        if i < num_seps:
            svx = curr_x + (sep_w - colon_vw) // 2
            draw.text((svx - colon_vl, start_y - v_top), ":", font=val_font, fill=color)

            slx = curr_x + (sep_w - colon_lw) // 2
            draw.text((slx - colon_ll, lbl_y), ":", font=label_font, fill=color)

            curr_x += sep_w

    return img

def render_countdown_frame(top_text, bottom_text, font, width, height, bg, color):
    img = Image.new("RGBA", (width, height), bg + (255,))
    draw = ImageDraw.Draw(img)

    spacing = int(font.size * 0.35)
    full_text = top_text if not bottom_text else f"{top_text}\n{bottom_text}"

    bbox = draw.multiline_textbbox((0, 0), full_text, font=font, spacing=spacing, align="center")
    x = (width - (bbox[2] - bbox[0])) // 2
    y = (height - (bbox[3] - bbox[1])) // 2

    draw.multiline_text((x, y), full_text, font=font, fill=color, spacing=spacing, align="center")
    return img

# =====================================================
# UI
# =====================================================

st.title("🎬 Will Return Generator")
st.markdown(
    "Gere animações no estilo **“Will Return”** dos filmes da **MARVEL**, com revelação progressiva do texto.  \n"
    "Exporte como **GIF/WebP animado** ou **PNG/JPG estático**."
)

st.markdown(
    """
<div style="background-color:#262730;border-left:4px solid #e62429;
padding:0.75rem 1rem;margin-top:0.75rem;margin-bottom:1.5rem;">
<b>🆕 Novidades</b><br>
• Preset Marvel Original calibrado frame a frame<br>
• Tipografia ajustada para maior fidelidade visual<br>
• Corrigido bug ao usar emojis com tonalidade de pele<br>
• Contagem regressiva animada ao final do GIF (opcional)<br>
• Novas opções de resolução - 1920x1080 e definição manual<br>
</div>
""",
    unsafe_allow_html=True
)

text_a = st.text_input("Bloco 1", "Steve Rogers")
text_b = st.text_input("Bloco 2", "Will Return")
text_c = st.text_input("Bloco 3", "In Avengers: Doomsday")

format_out = st.selectbox("Formato", ["GIF", "WebP", "PNG", "JPG"])

# =====================================================
# Contagem regressiva (somente GIF/WebP)
# =====================================================

if format_out in ["GIF", "WebP"]:
    st.markdown("### Contagem Regressiva")

    st.session_state.countdown_enabled = st.checkbox(
        "Ativar contagem regressiva ao final do GIF",
        value=st.session_state.countdown_enabled
    )

    if st.session_state.countdown_enabled:
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.countdown_date = st.date_input(
                "Data alvo",
                value=st.session_state.countdown_date
            )
        with col2:
            st.session_state.countdown_duration = st.number_input(
                "Duração da tela final (segundos)",
                1, 10, st.session_state.countdown_duration
            )

        st.caption("A contagem regressiva é calculada no momento da geração.")

# =====================================================
# Presets
# =====================================================

if format_out in ["GIF", "WebP"]:
    preset = st.selectbox("Preset", list(PRESETS.keys()), index=0)
    p = PRESETS[preset]
    st.session_state.fps = p["fps"]
    st.session_state.fade_ms = p["fade_ms"]
    st.session_state.delay_ms = p["delay_ms"]
    if p.get("resolution"):
        st.session_state.resolution = p["resolution"]
    if p.get("font"):
        st.session_state.font_name = p["font"]
    if p.get("bg"):
        st.session_state.bg_hex = p["bg"]
    if p.get("text"):
        st.session_state.text_hex = p["text"]

# =====================================================
# Opções Avançadas
# =====================================================

with st.expander("⚙️ Opções Avançadas"):
    st.session_state.font_name = st.selectbox("Fonte", list(FONT_OPTIONS.keys()),
                                              index=list(FONT_OPTIONS.keys()).index(st.session_state.font_name))
    st.session_state.fps = st.slider("FPS", 6, 24, st.session_state.fps)
    st.session_state.fade_ms = st.slider("Velocidade do fade (ms)", 400, 1500, st.session_state.fade_ms)
    st.session_state.delay_ms = st.slider("Delay entre blocos (ms)", 1000, 5000, st.session_state.delay_ms)

    st.markdown("### Resolução")
    mode = st.radio("Modo", ["Usar resolução padrão", "Definir resolução manualmente"],
                    index=0 if st.session_state.resolution_mode == "preset" else 1)
    st.session_state.resolution_mode = "preset" if mode.startswith("Usar") else "manual"

    if st.session_state.resolution_mode == "preset":
        st.session_state.resolution = st.selectbox("Resolução", ["640x360", "1280x720", "1920x1080"],
                                                   index=["640x360", "1280x720", "1920x1080"].index(st.session_state.resolution))
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.res_width = st.number_input("Largura (px)", 320, 3840, st.session_state.res_width, 10)
        with c2:
            st.session_state.res_height = st.number_input("Altura (px)", 180, 2160, st.session_state.res_height, 10)

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.bg_hex = st.color_picker("Fundo", st.session_state.bg_hex)
    with c2:
        st.session_state.text_hex = st.color_picker("Texto", st.session_state.text_hex)

# =====================================================
# Geração
# =====================================================

if st.button("🎞️ Gerar", use_container_width=True):
    blocks = [b.strip() for b in [text_a, text_b, text_c] if b.strip()]
    blocks_words = [b.split() for b in blocks]

    if st.session_state.resolution_mode == "manual":
        w, h = int(st.session_state.res_width), int(st.session_state.res_height)
    else:
        w, h = map(int, st.session_state.resolution.split("x"))

    bg = tuple(int(st.session_state.bg_hex[i:i+2], 16) for i in (1, 3, 5))
    color = tuple(int(st.session_state.text_hex[i:i+2], 16) for i in (1, 3, 5))

    font_cfg = FONT_OPTIONS[st.session_state.font_name]
    dummy = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(dummy)

    final_text = " ".join(blocks)
    font = fit_font(d, final_text, font_cfg["path"], int(w * 0.75), font_cfg["tracking"])
    final_width = measure_text(d, final_text, font, font_cfg["tracking"])

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format_out.lower()}")

    if format_out in ["GIF", "WebP"]:
        frames = []
        fade_frames = max(2, int((st.session_state.fade_ms / 1000) * st.session_state.fps))
        hold = max(1, int((st.session_state.delay_ms / 1000) * st.session_state.fps))

        for i in range(1, len(blocks_words) + 1):
            for f in range(fade_frames):
                t = (f + 1) / fade_frames
                alpha = (1 - math.exp(-5.5 * t)) ** 1.2
                frames.append(render_blocks(blocks_words, i, font, font_cfg["tracking"],
                                             w, h, bg, color, final_width, alpha))
            frames += [render_blocks(blocks_words, i, font, font_cfg["tracking"],
                                     w, h, bg, color, final_width, 1.0)] * max(1, hold - fade_frames)

        if st.session_state.countdown_enabled and st.session_state.countdown_date:
            now = datetime.now()
            target = datetime.combine(st.session_state.countdown_date, datetime.min.time())

            bg_frame = Image.new("RGBA", (w, h), bg + (255,))
            last_frame = frames[-1]

            # Fade out da frase principal
            for f in range(fade_frames):
                alpha = (f + 1) / fade_frames
                frames.append(Image.blend(last_frame, bg_frame, alpha))

            # Data alvo (Fade in -> Hold -> Fade out)
            date_text = st.session_state.countdown_date.strftime("%B %d, %Y").upper()
            date_font = fit_font(d, date_text, font_cfg["path"], int(w * 0.85), font_cfg["tracking"])
            date_img = render_countdown_frame(date_text, "", date_font, w, h, bg, color)

            for f in range(fade_frames):
                alpha = (f + 1) / fade_frames
                frames.append(Image.blend(bg_frame, date_img, alpha))

            frames += [date_img] * hold

            for f in range(fade_frames):
                alpha = (f + 1) / fade_frames
                frames.append(Image.blend(date_img, bg_frame, alpha))

            # Cronômetro animado decrescente frame a frame
            initial_delta = target - now
            initial_parts = get_countdown_parts(initial_delta)
            timer_font = fit_timer_font(initial_parts, font_cfg["path"], int(w * 0.90), int(h * 0.60))

            cd_frames = int(st.session_state.countdown_duration * st.session_state.fps)
            for f in range(cd_frames):
                current_time = now + timedelta(seconds=f / st.session_state.fps)
                delta = target - current_time
                timer_parts = get_countdown_parts(delta)
                timer_img = render_timer_frame(timer_parts, timer_font, font_cfg["path"], w, h, bg, color)
                frames.append(timer_img)

        frames[0].save(
            tmp.name,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / st.session_state.fps),
            loop=0,
            format="WEBP" if format_out == "WebP" else "GIF"
        )

    else:
        img = render_blocks(blocks_words, len(blocks_words), font,
                            font_cfg["tracking"], w, h, bg, color, final_width)
        img.convert("RGB").save(tmp.name, format="JPEG" if format_out == "JPG" else format_out)

    st.markdown("### Preview")

    if format_out in ["GIF", "WebP"] and w <= MAX_ANIMATED_PREVIEW_WIDTH:
        st.image(tmp.name, use_container_width=True)
    else:
        preview_img = Image.open(tmp.name) if format_out in ["PNG", "JPG"] else \
            render_blocks(blocks_words, len(blocks_words), font,
                          font_cfg["tracking"], w, h, bg, color, final_width)
        st.image(preview_img.resize((800, int(800 * h / w))), use_container_width=False)
        if format_out in ["GIF", "WebP"]:
            st.warning("⚠️ Em resoluções altas, o preview é estático. O arquivo baixado mantém a animação.")

    with open(tmp.name, "rb") as f:
        st.download_button("⬇️ Download", f, file_name=f"will_return.{format_out.lower()}",
                           mime=f"image/{format_out.lower()}")

    st.markdown("<div style='text-align:center;opacity:0.6;font-size:0.9em;margin-top:1rem'>"
                "Desenvolvido por Marcelo Diniz</div>", unsafe_allow_html=True)
