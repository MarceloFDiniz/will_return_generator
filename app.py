import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import requests
from io import BytesIO
import emoji
import math

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
# Estado inicial (Marvel default)
# =====================================================

defaults = {
    "fps": 12,
    "fade_ms": 1100,
    "delay_ms": 2800,
    "resolution": "1280x720",
    "font_name": "Oswald Regular 400 (default)",
    "bg_hex": "#000000",
    "text_hex": "#FFFFFF",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
# Emojis (Twemoji)
# =====================================================

EMOJI_CACHE = {}

def is_emoji(ch):
    return ch in emoji.EMOJI_DATA


def load_emoji_image(ch, size):
    key = (ch, size)
    if key in EMOJI_CACHE:
        return EMOJI_CACHE[key]

    codepoint = "-".join(f"{ord(c):x}" for c in ch)
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
    for ch in text:
        if ch == " ":
            width += draw.textbbox((0, 0), " ", font=font)[2]
        else:
            cw = draw.textbbox((0, 0), ch, font=font)[2]
            width += cw + tracking_px
    return width


def fit_font(draw, text, font_path, max_width, tracking):
    size = 96
    while size >= 18:
        font = ImageFont.truetype(font_path, size)
        if measure_text(draw, text, font, tracking) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 18)

# =====================================================
# Renderização
# =====================================================

def render_blocks(
    blocks_words,
    visible_blocks,
    font,
    tracking,
    width,
    height,
    bg,
    color,
    final_width,
    fade_alpha=1.0
):
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
            for ch in word:
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
# UI
# =====================================================

st.title("🎬 Will Return Generator")

st.markdown(
    """
    <p style="font-size:1.05em; opacity:0.85">
    Gere animações no estilo <b>“Will Return”</b> da Marvel, com revelação progressiva do texto.
    Exporte como <b>GIF/WebP animado</b> ou <b>PNG/JPG estático</b>.
    </p>
    """,
    unsafe_allow_html=True
)

text_a = st.text_input("Bloco 1", "Steve Rogers")
text_b = st.text_input("Bloco 2", "Will Return")
text_c = st.text_input("Bloco 3", "In Avengers: Doomsday")

format_out = st.selectbox("Formato", ["GIF", "WebP", "PNG", "JPG"])

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

with st.expander("⚙️ Opções Avançadas"):
    font_name = st.selectbox(
        "Fonte",
        list(FONT_OPTIONS.keys()),
        index=list(FONT_OPTIONS.keys()).index(st.session_state.font_name)
    )

    fps = st.slider("FPS", 6, 24, st.session_state.fps)
    fade_ms = st.slider("Velocidade do fade (ms)", 400, 1500, st.session_state.fade_ms)
    delay_ms = st.slider("Delay entre blocos (ms)", 1000, 5000, st.session_state.delay_ms)
    resolution = st.selectbox(
        "Resolução",
        ["640x360", "1280x720"],
        index=["640x360", "1280x720"].index(st.session_state.resolution)
    )

    col1, col2 = st.columns(2)
    with col1:
        bg_hex = st.color_picker("Fundo", st.session_state.bg_hex)
    with col2:
        text_hex = st.color_picker("Texto", st.session_state.text_hex)

    st.session_state.fps = fps
    st.session_state.fade_ms = fade_ms
    st.session_state.delay_ms = delay_ms
    st.session_state.resolution = resolution
    st.session_state.font_name = font_name
    st.session_state.bg_hex = bg_hex
    st.session_state.text_hex = text_hex

gerar = st.button("🎞️ Gerar", use_container_width=True)
preview = st.empty()
download = st.empty()
st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.9em'>"
    "Desenvolvido por Marcelo Diniz"
    "</div>",
    unsafe_allow_html=True
)

# =====================================================
# Geração
# =====================================================

if gerar:
    blocks = [b.strip() for b in [text_a, text_b, text_c] if b.strip()]
    blocks_words = [b.split() for b in blocks]

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

    if format_out in ["PNG", "JPG"]:
        img = render_blocks(blocks_words, len(blocks_words), font,
                            font_cfg["tracking"], w, h, bg, color, final_width)
        img.convert("RGB").save(tmp.name, format="JPEG" if format_out == "JPG" else format_out)
    else:
        frames = []
        fade_frames = max(2, int((st.session_state.fade_ms / 1000) * st.session_state.fps))
        hold = max(1, int((st.session_state.delay_ms / 1000) * st.session_state.fps))

        for i in range(1, len(blocks_words) + 1):
            for f in range(fade_frames):
                t = (f + 1) / fade_frames
                fade_alpha = (1 - math.exp(-5.5 * t)) ** 1.2

                frames.append(
                    render_blocks(
                        blocks_words,
                        i,
                        font,
                        font_cfg["tracking"],
                        w,
                        h,
                        bg,
                        color,
                        final_width,
                        fade_alpha
                    )
                )

            frames += [
                render_blocks(
                    blocks_words,
                    i,
                    font,
                    font_cfg["tracking"],
                    w,
                    h,
                    bg,
                    color,
                    final_width,
                    1.0
                )
            ] * max(1, hold - fade_frames)

        frames[0].save(
            tmp.name,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / st.session_state.fps),
            loop=0,
            format="WEBP" if format_out == "WebP" else "GIF"
        )

    preview.image(tmp.name, caption="Preview", use_container_width=True)

    with open(tmp.name, "rb") as f:
        download.download_button(
            "⬇️ Download",
            f,
            file_name=f"will_return.{format_out.lower()}",
            mime={
                "GIF": "image/gif",
                "WebP": "image/webp",
                "PNG": "image/png",
                "JPG": "image/jpeg"
            }[format_out],
            use_container_width=True
        )
