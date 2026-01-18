import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile

# =========================
# Funções utilitárias
# =========================

def fit_font(draw, text, font_path, max_width, start_size=90):
    size = start_size
    while size > 10:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(font_path, 10)

def render_text(text, width, height, bg_color, text_color, font_path):
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    font = fit_font(draw, text, font_path, int(width * 0.9))
    bbox = draw.textbbox((0, 0), text, font=font)

    x = (width - (bbox[2] - bbox[0])) // 2
    y = (height - (bbox[3] - bbox[1])) // 2

    draw.text((x, y), text, fill=text_color, font=font)
    return img

# =========================
# UI
# =========================

st.title("Will Return Generator (Cloud Final)")

full_text = st.text_input(
    "Texto completo:",
    "MARCELO WILL RETURN IN AVENGERS: DOOMSDAY"
)

fps = st.slider("FPS (recomendado: 8–12)", 6, 15, 10)
delay_ms = st.slider("Delay entre frases (ms)", 100, 600, 250)

resolution = st.selectbox("Resolução", ["640x360", "1280x720"])
format_out = st.selectbox("Formato", ["GIF", "WebP"])

bg_hex = st.color_picker("Cor de fundo", "#000000")
text_hex = st.color_picker("Cor do texto", "#FFFFFF")

if st.button("Gerar"):
    if "WILL RETURN IN" not in full_text:
        st.error("O texto deve conter exatamente 'WILL RETURN IN'")
        st.stop()

    before, after = full_text.split("WILL RETURN IN", 1)

    width, height = map(int, resolution.split("x"))
    bg_color = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    text_color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    frames = []
    hold_frames = max(1, int((delay_ms / 1000) * fps))

    # Estado 1
    frames += [render_text(before.strip(), width, height, bg_color, text_color, font_path)] * hold_frames

    # Estado 2
    frames += [render_text((before + " WILL RETURN IN").strip(), width, height, bg_color, text_color, font_path)] * hold_frames

    # Estado 3
    frames += [render_text(full_text.strip(), width, height, bg_color, text_color, font_path)] * (hold_frames * 2)

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
        st.download_button(
            "Download",
            data=f,
            file_name=f"will_return.{format_out.lower()}",
            mime="image/gif" if format_out == "GIF" else "image/webp"
        )
