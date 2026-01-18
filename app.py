import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile

# =========================
# Helpers
# =========================

def fit_font_single_line(draw, text, font_path, max_width):
    size = 96
    while size >= 18:
        font = ImageFont.truetype(font_path, size)
        if draw.textbbox((0, 0), text, font=font)[2] <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 18)


def classify_words(words):
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


def render_frame(words, classes, visible, font, width, height, bg, color):
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    full_text = " ".join(words)
    bbox = draw.textbbox((0, 0), full_text, font=font)
    x = (width - (bbox[2] - bbox[0])) // 2
    y = (height - (bbox[3] - bbox[1])) // 2

    cursor = x
    for w, cls in zip(words, classes):
        word_text = w + " "
        if cls in visible:
            draw.text((cursor, y), word_text, font=font, fill=color)
        cursor += draw.textbbox((0, 0), word_text, font=font)[2]

    return img


# =========================
# UI config
# =========================

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

st.title("🎬 Will Return Generator")

full_text = st.text_input(
    "Texto",
    "MARCELO WILL RETURN IN AVENGERS: DOOMSDAY"
)

fps = st.slider("FPS", 6, 15, 10)
delay_ms = st.slider("Delay entre blocos (ms)", 100, 1000, 1000)
resolution = st.selectbox("Resolução", ["640x360", "1280x720"])
format_out = st.selectbox("Formato", ["GIF", "WebP"])

# --- Linha de controles visuais
col1, col2, col3, col4 = st.columns(4)

with col1:
    bg_hex = st.color_picker("Fundo", "#000000")

with col2:
    text_hex = st.color_picker("Texto", "#FFFFFF")

with col3:
    gerar = st.button("Gerar")

with col4:
    download_placeholder = st.empty()

st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.9em'>"
    "Desenvolvido por Marcelo Diniz"
    "</div>",
    unsafe_allow_html=True
)

# =========================
# Geração
# =========================

if gerar:
    if "WILL RETURN IN" not in full_text:
        st.error("O texto deve conter exatamente 'WILL RETURN IN'")
        st.stop()

    words = full_text.split()
    classes = classify_words(words)

    width, height = map(int, resolution.split("x"))
    bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    dummy = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(dummy)

    font = fit_font_single_line(draw, full_text, font_path, int(width * 0.9))

    hold = max(1, int((delay_ms / 1000) * fps))
    frames = []

    frames += [
        render_frame(words, classes, {"A"}, font, width, height, bg, color)
    ] * hold

    frames += [
        render_frame(words, classes, {"A", "B"}, font, width, height, bg, color)
    ] * hold

    frames += [
        render_frame(words, classes, {"A", "B", "C"}, font, width, height, bg, color)
    ] * (hold * 2)

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".gif" if format_out == "GIF" else ".webp"
    )

    frames[0].save(
        tmp.name,
        save_all=True,
        append_images=frames[1:],
        duration=int(1000 / fps),
        loop=0,
        format="WEBP" if format_out == "WebP" else "GIF"
    )

    with open(tmp.name, "rb") as f:
        download_placeholder.download_button(
            "Download",
            f,
            file_name=f"will_return.{format_out.lower()}",
            mime="image/gif" if format_out == "GIF" else "image/webp"
        )
