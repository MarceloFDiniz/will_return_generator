import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import requests
from io import BytesIO
import emoji

# =====================================================
# Configuração da página
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
# Fontes disponíveis
# =====================================================

FONT_OPTIONS = {
    "Oswald Regular 400 (default)": {"path": "fonts/Oswald-Regular.ttf", "tracking": 0.15},
    "Roboto Condensed Thin 100": {"path": "fonts/RobotoCondensed-Thin.ttf", "tracking": 0.10},
    "Roboto Condensed Light 300": {"path": "fonts/RobotoCondensed-Light.ttf", "tracking": 0.12},
    "Roboto Condensed Regular Italic 400": {"path": "fonts/RobotoCondensed-Italic.ttf", "tracking": 0.12},
    "Roboto Condensed Black 900": {"path": "fonts/RobotoCondensed-Black.ttf", "tracking": 0.08},
    "Inter Tight Regular 400": {"path": "fonts/InterTight-Regular.ttf", "tracking": 0.05},
    "Inter Tight Medium 500": {"path": "fonts/InterTight-Medium.ttf", "tracking": 0.05},
    "Inter Tight Bold 700": {"path": "fonts/InterTight-Bold.ttf", "tracking": 0.04},
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

    r = requests.get(url, timeout=5)
    if r.status_code != 200:
        return None

    img = Image.open(BytesIO(r.content)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    EMOJI_CACHE[key] = img
    return img

# =====================================================
# Medição de texto
# =====================================================

def measure_text_width(draw, text, font, tracking):
    w = 0
    tpx = int(font.size * tracking)
    for ch in text:
        if ch == " ":
            w += draw.textbbox((0, 0), " ", font=font)[2]
        else:
            cw = draw.textbbox((0, 0), ch, font=font)[2]
            w += cw + tpx
    return w


def fit_font(draw, text, font_path, max_width, tracking):
    size = 96
    while size >= 18:
        font = ImageFont.truetype(font_path, size)
        if measure_text_width(draw, text, font, tracking) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 18)

# =====================================================
# Renderização com FADE
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

    text_height = draw.textbbox((0, 0), "X", font=font)[3]
    x = (width - final_width) // 2
    y = (height - text_height) // 2

    cursor = x
    tpx = int(font.size * tracking)
    emoji_size = font.size

    for i in range(visible_blocks):
        if i > 0:
            cursor += draw.textbbox((0, 0), " ", font=font)[2]

        fading = (i == visible_blocks - 1 and fade_alpha < 1.0)

        for word in blocks_words[i]:
            for ch in word:
                alpha = int(255 * fade_alpha) if fading else 255

                if is_emoji(ch):
                    emoji_img = load_emoji_image(ch, emoji_size)
                    if emoji_img:
                        e = emoji_img.copy()
                        e.putalpha(alpha)
                        img.paste(e, (cursor, y), e)
                        cursor += emoji_size + tpx
                else:
                    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                    od = ImageDraw.Draw(overlay)
                    od.text((cursor, y), ch, font=font, fill=color + (alpha,))
                    img = Image.alpha_composite(img, overlay)
                    cw = draw.textbbox((0, 0), ch, font=font)[2]
                    cursor += cw + tpx

            cursor += draw.textbbox((0, 0), " ", font=font)[2]

    return img

# =====================================================
# UI
# =====================================================

st.title("🎬 Will Return Generator")

st.markdown(
    "Gere animações no estilo **Marvel – Will Return**, com revelação progressiva e fade cinematográfico."
)

text_a = st.text_input("Bloco 1", "Steve Rogers")
text_b = st.text_input("Bloco 2", "Will Return")
text_c = st.text_input("Bloco 3", "In Avengers: Doomsday")

font_name = st.selectbox("Fonte", list(FONT_OPTIONS.keys()), index=0)
font_cfg = FONT_OPTIONS[font_name]

format_out = st.selectbox("Formato", ["GIF", "WebP", "PNG", "JPG"])

with st.expander("⚙️ Opções Avançadas"):
    fps = st.slider("FPS", 6, 15, 10)
    delay_ms = st.slider("Delay (ms)", 200, 1200, 800)
    resolution = st.selectbox("Resolução", ["640x360", "1280x720"])
    bg_hex = st.color_picker("Fundo", "#000000")
    text_hex = st.color_picker("Texto", "#FFFFFF")

gerar = st.button("🎞️ Gerar", use_container_width=True)
preview = st.empty()
download = st.empty()

# =====================================================
# Geração
# =====================================================

if gerar:
    blocks = [b.strip() for b in [text_a, text_b, text_c] if b.strip()]
    blocks_words = [b.split() for b in blocks]

    w, h = map(int, resolution.split("x"))
    bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    dummy = Image.new("RGB", (w, h))
    ddraw = ImageDraw.Draw(dummy)

    final_text = " ".join(blocks)
    font = fit_font(ddraw, final_text, font_cfg["path"], int(w * 0.9), font_cfg["tracking"])
    final_width = measure_text_width(ddraw, final_text, font, font_cfg["tracking"])

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format_out.lower()}")

    if format_out in ["PNG", "JPG"]:
        img = render_blocks(blocks_words, len(blocks_words), font,
                            font_cfg["tracking"], w, h, bg, color, final_width)
        img.convert("RGB").save(tmp.name, format="JPEG" if format_out == "JPG" else format_out)
    else:
        frames = []
        fade_frames = max(4, int(0.25 * fps))
        hold = max(1, int((delay_ms / 1000) * fps))

        for i in range(1, len(blocks_words) + 1):
            for f in range(fade_frames):
                alpha = (f + 1) / fade_frames
                frames.append(
                    render_blocks(blocks_words, i, font,
                                  font_cfg["tracking"], w, h,
                                  bg, color, final_width, alpha)
                )
            frames += [
                render_blocks(blocks_words, i, font,
                              font_cfg["tracking"], w, h,
                              bg, color, final_width, 1.0)
            ] * max(1, hold - fade_frames)

        frames[0].save(
            tmp.name,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
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
