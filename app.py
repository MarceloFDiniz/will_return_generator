import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import requests
from io import BytesIO
import emoji

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

# =========================
# Texto principal
# =========================

full_text = st.text_input(
    "Texto",
    "MARCELO WILL RETURN IN AVENGERS: DOOMSDAY"
)

format_out = st.selectbox(
    "Formato de saída",
    ["GIF", "WebP", "PNG", "JPG"]
)

# =========================
# Opções avançadas
# =========================

with st.expander("⚙️ Opções Avançadas", expanded=False):
    fps = st.slider("FPS", 6, 15, 10)
    delay_ms = st.slider("Delay entre blocos (ms)", 100, 1000, 1000)
    resolution = st.selectbox("Resolução", ["640x360", "1280x720"])

    col_a, col_b = st.columns(2)
    with col_a:
        bg_hex = st.color_picker("Cor de fundo", "#000000")
    with col_b:
        text_hex = st.color_picker("Cor do texto", "#FFFFFF")

# =========================
# Ação principal
# =========================

gerar = st.button("🎞️ Gerar", use_container_width=True)

preview_slot = st.empty()
download_slot = st.empty()

st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.9em;margin-top:2rem'>"
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

    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f".{format_out.lower()}"
    )

    # ---------- Estático ----------
    if format_out in ["PNG", "JPG"]:
        img = render_static_image(words, font, width, height, bg, color)
        img.save(tmp.name, format="JPEG" if format_out == "JPG" else format_out)

    # ---------- Animado ----------
    else:
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

        frames[0].save(
            tmp.name,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / fps),
            loop=0,
            format="WEBP" if format_out == "WebP" else "GIF"
        )

    # =========================
    # Preview (entre Gerar e Download)
    # =========================

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
