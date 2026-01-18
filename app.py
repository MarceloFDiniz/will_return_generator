import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile

# =========================
# Layout global (frase inteira)
# =========================

def fit_font_and_wrap_global(draw, words, font_path, max_width):
    size = 96
    phrase = " ".join(words)

    idx_will = words.index("WILL")
    idx_in = words.index("IN")

    while size >= 24:
        font = ImageFont.truetype(font_path, size)

        # 1 linha
        if draw.textbbox((0, 0), phrase, font=font)[2] <= max_width:
            return font, [words]

        # 2 linhas — quebra global, mas nunca dentro de WILL RETURN IN
        for i in range(1, len(words)):
            if idx_will <= i <= idx_in:
                continue  # proibido quebrar aqui

            l1 = " ".join(words[:i])
            l2 = " ".join(words[i:])

            if (
                draw.textbbox((0, 0), l1, font=font)[2] <= max_width
                and draw.textbbox((0, 0), l2, font=font)[2] <= max_width
            ):
                return font, [words[:i], words[i:]]

        size -= 2

    font = ImageFont.truetype(font_path, 24)
    return font, [words]


# =========================
# Classificação por bloco
# =========================

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


# =========================
# Render frame
# =========================

def render_frame(lines, classes, visible, font, width, height, bg, color):
    img = Image.new("RGB", (width, height), bg)
    draw = ImageDraw.Draw(img)

    line_heights = [
        draw.textbbox((0, 0), " ".join(l), font=font)[3]
        for l in lines
    ]
    total_h = sum(line_heights)
    y = (height - total_h) // 2

    idx = 0
    for line, lh in zip(lines, line_heights):
        line_text = " ".join(line)
        lw = draw.textbbox((0, 0), line_text, font=font)[2]
        x = (width - lw) // 2

        for w in line:
            if classes[idx] in visible:
                draw.text((x, y), w + " ", font=font, fill=color)
            w_width = draw.textbbox((0, 0), w + " ", font=font)[2]
            x += w_width
            idx += 1

        y += lh

    return img


# =========================
# UI
# =========================

st.title("Will Return Generator")

full_text = st.text_input(
    "Texto completo:",
    "MARCELO WILL RETURN IN AVENGERS: DOOMSDAY"
)

fps = st.slider("FPS", 6, 15, 10)
delay_ms = st.slider("Delay entre blocos (ms)", 100, 600, 250)
resolution = st.selectbox("Resolução", ["640x360", "1280x720"])
format_out = st.selectbox("Formato", ["GIF", "WebP"])

bg_hex = st.color_picker("Cor de fundo", "#000000")
text_hex = st.color_picker("Cor do texto", "#FFFFFF")

st.markdown(
    "<div style='text-align:center;opacity:0.6;font-size:0.9em'>"
    "Desenvolvido por Marcelo Diniz"
    "</div>",
    unsafe_allow_html=True
)

if st.button("Gerar"):
    if "WILL RETURN IN" not in full_text:
        st.error("O texto deve conter exatamente 'WILL RETURN IN'")
        st.stop()

    words = full_text.split()

    width, height = map(int, resolution.split("x"))
    bg = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    dummy = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(dummy)

    font, lines = fit_font_and_wrap_global(
        draw, words, font_path, int(width * 0.9)
    )

    classes = classify_words(words)

    hold = max(1, int((delay_ms / 1000) * fps))
    frames = []

    frames += [
        render_frame(lines, classes, {"A"}, font, width, height, bg, color)
    ] * hold

    frames += [
        render_frame(lines, classes, {"A", "B"}, font, width, height, bg, color)
    ] * hold

    frames += [
        render_frame(lines, classes, {"A", "B", "C"}, font, width, height, bg, color)
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
        st.download_button(
            "Download",
            f,
            file_name=f"will_return.{format_out.lower()}",
            mime="image/gif" if format_out == "GIF" else "image/webp"
        )
