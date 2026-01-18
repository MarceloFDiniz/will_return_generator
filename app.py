import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import tempfile
import textwrap

# =========================
# Layout helpers
# =========================

def split_two_lines(draw, font, text, max_width):
    words = text.split()
    best = None

    for i in range(1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:])
        w1 = draw.textbbox((0, 0), l1, font=font)[2]
        w2 = draw.textbbox((0, 0), l2, font=font)[2]
        if w1 <= max_width and w2 <= max_width:
            best = (l1, l2)
            break

    return best


def fit_font_and_layout(draw, text, font_path, max_width):
    size = 96
    while size >= 24:
        font = ImageFont.truetype(font_path, size)
        bbox = draw.textbbox((0, 0), text, font=font)
        if bbox[2] <= max_width:
            return font, [text]

        split = split_two_lines(draw, font, text, max_width)
        if split:
            return font, list(split)

        size -= 2

    font = ImageFont.truetype(font_path, 24)
    return font, textwrap.wrap(text, width=20)


def measure_lines(draw, font, lines):
    widths = []
    heights = []
    for l in lines:
        bbox = draw.textbbox((0, 0), l, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    return widths, heights


# =========================
# Render
# =========================

def render_frame(
    show_a,
    show_b,
    show_c,
    blocks,
    layout,
    font,
    width,
    height,
    bg_color,
    text_color,
    footer_font
):
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    for idx, visible in enumerate([show_a, show_b, show_c]):
        if not visible:
            continue

        lines = blocks[idx]
        xs, ys = layout[idx]

        for line, x, y in zip(lines, xs, ys):
            draw.text((x, y), line, font=font, fill=text_color)

    # Footer
    footer_text = "Desenvolvido por Marcelo Diniz"
    fb = draw.textbbox((0, 0), footer_text, font=footer_font)
    fx = (width - (fb[2] - fb[0])) // 2
    fy = height - (fb[3] - fb[1]) - 12

    draw.text((fx, fy), footer_text, font=footer_font, fill=text_color)

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

if st.button("Gerar"):
    if "WILL RETURN IN" not in full_text:
        st.error("O texto deve conter exatamente 'WILL RETURN IN'")
        st.stop()

    before, after = full_text.split("WILL RETURN IN", 1)
    block_a = before.strip()
    block_b = "WILL RETURN IN"
    block_c = after.strip()

    width, height = map(int, resolution.split("x"))
    bg_color = tuple(int(bg_hex[i:i+2], 16) for i in (1, 3, 5))
    text_color = tuple(int(text_hex[i:i+2], 16) for i in (1, 3, 5))

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    footer_font = ImageFont.truetype(font_path, 18)

    dummy = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(dummy)

    # Ajuste global com layout final completo
    full_concat = f"{block_a} {block_b} {block_c}".strip()
    font, _ = fit_font_and_layout(draw, full_concat, font_path, int(width * 0.9))

    blocks = []
    layouts = []

    cursor_x = None
    center_y = height // 2

    # Pre-cálculo de blocos
    for text in [block_a, block_b, block_c]:
        lines = split_two_lines(draw, font, text, int(width * 0.9))
        if lines:
            lines = list(lines)
        else:
            lines = [text]

        blocks.append(lines)

    # Medição total
    total_width = 0
    block_metrics = []

    for lines in blocks:
        w, h = measure_lines(draw, font, lines)
        block_width = max(w)
        block_height = sum(h)
        block_metrics.append((w, h, block_width, block_height))
        total_width += block_width

    start_x = (width - total_width) // 2
    current_x = start_x

    for (lines, (ws, hs, bw, bh)) in zip(blocks, block_metrics):
        xs = []
        ys = []

        y_start = center_y - (bh // 2)
        cy = y_start

        for w, h, line in zip(ws, hs, lines):
            xs.append(current_x + (bw - w) // 2)
            ys.append(cy)
            cy += h

        layouts.append((xs, ys))
        current_x += bw

    hold_frames = max(1, int((delay_ms / 1000) * fps))
    frames = []

    frames += [
        render_frame(True, False, False, blocks, layouts, font, width, height, bg_color, text_color, footer_font)
    ] * hold_frames

    frames += [
        render_frame(True, True, False, blocks, layouts, font, width, height, bg_color, text_color, footer_font)
    ] * hold_frames

    frames += [
        render_frame(True, True, True, blocks, layouts, font, width, height, bg_color, text_color, footer_font)
    ] * (hold_frames * 2)

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
