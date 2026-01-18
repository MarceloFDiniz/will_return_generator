import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import requests
from io import BytesIO
import emoji

# =====================================================
# Configuração da página
# =====================================================

st.set_page_config(
    page_title="Will Return Generator",
    layout="centered"
)

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
# Fontes disponíveis (whitelist)
# =====================================================

FONT_OPTIONS = {
    "Oswald Regular 400 (default)": {
        "path": "fonts/Oswald-Regular.ttf",
        "tracking": 0.15
    },

    "Roboto Condensed Thin 100": {
        "path": "fonts/RobotoCondensed-Thin.ttf",
        "tracking": 0.10
    },
    "Roboto Condensed Light 300": {
        "path": "fonts/RobotoCondensed-Light.ttf",
        "tracking": 0.12
    },
    "Roboto Condensed Regular Italic 400": {
        "path": "fonts/RobotoCondensed-Italic.ttf",
        "tracking": 0.12
    },
    "Roboto Condensed Black 900": {
        "path": "fonts/RobotoCondensed-Black.ttf",
        "tracking": 0.08
    },

    "Inter Tight Regular 400": {
        "path": "fonts/InterTight-Regular.ttf",
        "tracking": 0.05
    },
    "Inter Tight Medium 500": {
        "path": "fonts/InterTight-Medium.ttf",
        "tracking": 0.05
    },
    "Inter Tight Bold 700": {
        "path": "fonts/InterTight-Bold.ttf",
        "tracking": 0.04
    },
}

# =====================================================
# Emoji helpers (Twemoji)
# =====================================================

EMOJI_CACHE = {}

def is_emoji(char: str) -> bool:
    return char in emoji.EMOJI_DATA


def load_emoji_image(char: str, size: int):
    key = (char, size)
    if key in EMOJI_CACHE:
        return EMOJI_CACHE[key]

    codepoint = "-".join(f"{ord(c):x}" for c in char)
    url = f"https://cdnjs.cloudflare.com/ajax/libs/twemoji/14.0.2/72x72/{codepoint}.png"

    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        EMOJI_CACHE[key] = img
        return img
    except Exception:
        return None

# =====================================================
# Texto / Layout helpers
# =====================================================

def measure_text_width_with_tracking(draw, text, font, tracking_factor):
    width = 0
    tracking_px = int(font.size * tracking_factor)

    for ch in text:
        if ch == " ":
            width += draw.textbbox((0, 0), " ", font=font)[2]
        else:
            char_w = draw.textbbox((0, 0), ch, font=font)[2]
            width += char_w + tracking_px

    return width


def fit_font_single_line(draw, text, font_path, max_width, tracking_factor):
    size = 96
    while size >= 18:
        font = ImageFont.truetype(font_path, size)
        measured_width = measure_text_width_with_tracking(
            draw, text, font, tracking_factor
        )
        if measured_width <= max_width:
            return font
        size -= 2

    return ImageFont.truetype(font_path, 18)

def classify_words(words):
    """
    A = antes de WILL RETURN IN
    B = WILL RETURN IN
    C = depois
    """
    classes = []
    state = "A"

    for w in words:
        if w == "WILL":
            state = "B"
        elif state == "B" and w == "IN":
            classes.append("B")
            state = "C"
            continue

        classes.append(state)

    return classes


def render_text(words, classes, visible, font, tracking_factor, width, height, bg, color):
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    full_text = " ".join(words)
    bbox = draw.textbbox((0, 0), full_text, font=font)
    x = (width - (bbox[2] - bbox[0])) // 2
    y = (height - (bbox[3] - bbox[1])) // 2

    cursor = x
    emoji_size = font.size
    tracking_px = int(font.size * tracking_factor)

    for word, cls in zip(words, classes):
        if cls not in visible:
            cursor += draw.textbbox((0, 0), word + " ", font=font)[2]
            continue

        for ch in word:
            if is_emoji(ch):
                emoji_img = load_emoji_image(ch, emoji_size)
                if emoji_img:
                    img.paste(emoji_img, (cursor, y), emoji_img)
                    cursor += emoji_size + tracking_px
                else:
                    cursor += emoji_size + tracking_px
            else:
                draw.text((cursor, y), ch, font=font, fill=color)
                char_w = draw.textbbox((0, 0), ch, font=font)[2]
                cursor += char_w + tracking_px

        cursor += draw.textbbox((0, 0), " ", font=font)[2]

    return img


def render_static_image(words, font, tracking_factor, width, height, bg, color):
    classes = ["A"] * len(words)
    return render_text(words, classes, {"A"}, font, tracking_factor, width, height, bg, color)

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

full_text = st.text_input(
    "Texto",
    "MARCELO WILL RETURN IN AVENGERS: DOOMSDAY"
)

font_name = st.selectbox(
    "Fonte",
    list(FONT_OPTIONS.keys()),
    index=0
)

font_config = FONT_OPTIONS[font_name]
font_path = font_config["path"]
tracking_factor = font_config["tracking"]

format_out = st.selectbox(
    "Formato de saída",
    ["GIF", "WebP", "PNG", "JPG"]
)

with st.expander("⚙️ Opções Avançadas", expanded=False):
    fps = st.slider("FPS", 6, 15, 10)
    delay_ms = st.slider("Delay entre blocos (ms)", 100, 1000, 1000)
    resolution = st.selectbox("Resolução", ["640x360", "1280x720"])

    col_a, col_b = st.columns(2)
    with col_a:
        bg_hex = st.color_picker("Cor de fundo", "#000000")
    with col_b:
        text_hex = st.color_picker("Cor do texto", "#FFFFFF")

gerar = st.button("🎞️ Gerar", use_container_width=True)

preview_slot = st.empty()
download_slot = st.empty()

st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.9em;margin-top:2rem'>"
    "Desenvolvido por Marcelo Diniz"
    "</div>",
    unsafe_allow_html=True
)

# =====================================================
# Geração
# =====================================================

if gerar:
    if "WILL RETURN IN" not in full_text:
        st.error("O texto deve conter exatamente 'WILL RETURN IN'")
        st.stop()

    words = full_text.split()
    classes = classify_words(words)

    width, height = map(int, resolution.split("x"))
    bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    dummy = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(dummy)

    font = fit_font_single_line(
    draw,
    full_text,
    font_path,
    int(width * 0.9),
    tracking_factor
)
    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{format_out.lower()}"
    )

    if format_out in ["PNG", "JPG"]:
        img = render_static_image(
            words, font, tracking_factor, width, height, bg, color
        )
        img.save(tmp.name, format="JPEG" if format_out == "JPG" else format_out)
    else:
        hold = max(1, int((delay_ms / 1000) * fps))
        frames = []

        frames += [
            render_text(words, classes, {"A"}, font, tracking_factor, width, height, bg, color)
        ] * hold

        frames += [
            render_text(words, classes, {"A", "B"}, font, tracking_factor, width, height, bg, color)
        ] * hold

        frames += [
            render_text(words, classes, {"A", "B", "C"}, font, tracking_factor, width, height, bg, color)
        ] * (hold * 2)

        frames[0].save(
            tmp.name,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
            format="WEBP" if format_out == "WebP" else "GIF"
        )

    preview_slot.image(
        tmp.name,
        caption="Preview",
        use_container_width=True
    )

    with open(tmp.name, "rb") as f:
        download_slot.download_button(
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
