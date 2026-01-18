import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import imageio
import numpy as np
import tempfile
import math

# =========================
# Funções de animação
# =========================

def ease_in_out(t):
    """Easing suave (0..1)"""
    return 0.5 * (1 - math.cos(math.pi * t))

def render_frame(
    text,
    width,
    height,
    font,
    scale,
    opacity,
    bg_color,
    text_color
):
    img = Image.new("RGBA", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Texto
    text_bbox = draw.textbbox((0, 0), text, font=font)
    tw = text_bbox[2] - text_bbox[0]
    th = text_bbox[3] - text_bbox[1]

    # Escala
    scaled_font_size = int(font.size * scale)
    scaled_font = ImageFont.truetype(font.path, scaled_font_size)

    text_bbox = draw.textbbox((0, 0), text, font=scaled_font)
    tw = text_bbox[2] - text_bbox[0]
    th = text_bbox[3] - text_bbox[1]

    x = (width - tw) // 2
    y = (height - th) // 2

    # Texto em camada separada para opacidade
    text_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    r, g, b = text_color
    text_draw.text(
        (x, y),
        text,
        font=scaled_font,
        fill=(r, g, b, int(255 * opacity))
    )

    img = Image.alpha_composite(img, text_layer)
    return img.convert("RGB")

# =========================
# UI Streamlit
# =========================

st.title("Will Return Generator (GIF / WebP)")

text = st.text_input("Texto base:", "WILL RETURN IN")
duration = st.slider("Duração total (segundos)", 3, 15, 6)
fps = st.slider("FPS", 6, 15, 10)

resolution = st.selectbox("Resolução", ["640x360", "1280x720"])
format_out = st.selectbox("Formato", ["GIF", "WebP"])

bg_hex = st.color_picker("Cor de fundo", "#000000")
text_hex = st.color_picker("Cor do texto", "#FFFFFF")

if st.button("Gerar animação"):
    st.info("Renderizando frames...")

    width, height = map(int, resolution.split("x"))
    total_frames = duration * fps

    bg_color = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5)) + (255,)
    text_color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    # Fonte padrão (compatível com Cloud)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    base_font = ImageFont.truetype(font_path, 80)
    base_font.path = font_path  # hack para reutilizar

    frames = []

    for frame in range(total_frames):
        t = frame / total_frames
        e = ease_in_out(t)

        # Fade + zoom
        opacity = min(1.0, max(0.0, e * 1.2))
        scale = 0.8 + 0.4 * e

        seconds_left = max(1, duration - frame // fps)
        full_text = f"{text} {seconds_left}"

        img = render_frame(
            full_text,
            width,
            height,
            base_font,
            scale,
            opacity,
            bg_color,
            text_color
        )

        frames.append(np.array(img))

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".gif" if format_out == "GIF" else ".webp"
    )

    if format_out == "GIF":
        imageio.mimsave(tmp.name, frames, fps=fps)
        mime = "image/gif"
        fname = "will_return.gif"
    else:
        imageio.mimsave(tmp.name, frames, format="WEBP", fps=fps)
        mime = "image/webp"
        fname = "will_return.webp"

    st.success("Concluído")

    with open(tmp.name, "rb") as f:
        st.download_button(
            "Download",
            data=f,
            file_name=fname,
            mime=mime
        )
