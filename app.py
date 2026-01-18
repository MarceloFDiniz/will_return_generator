import streamlit as st
from moviepy.editor import (
    TextClip,
    concatenate_videoclips,
    AudioFileClip,
    CompositeVideoClip,
)
import tempfile
import os

# --- UI ---
st.title("Countdown Video Generator")

text = st.text_input("Texto da contagem regressiva:", "BACK IN")
duration = st.slider("Duração total (segundos):", 3, 30, 10)
font_size = st.slider("Tamanho da fonte:", 40, 200, 120)
color = st.color_picker("Cor do texto:", "#FFFFFF")
bg_color = st.color_picker("Cor de fundo:", "#000000")
music_file = st.file_uploader("Música de fundo (opcional):", type=["mp3", "wav"])
output_type = st.selectbox("Tipo de saída:", ["MP4", "GIF"])

if st.button("Gerar"):
    st.info("Processando... aguarde.")

    # --- Gerar clipe texto (MoviePy) ---
    clips = []
    for i in range(duration, 0, -1):
        txt = f"{text} {i}"
        clip = (
            TextClip(txt,
                     fontsize=font_size,
                     color=color,
                     size=(1280, 720),
                     bg_color=bg_color)
            .set_duration(1)
        )
        clips.append(clip)

    final_clip = concatenate_videoclips(clips, method="compose")

    # --- Música opcional ---
    if music_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(music_file.getbuffer())
            tmp_path = tmp.name

        audio = AudioFileClip(tmp_path).set_duration(final_clip.duration)
        final_clip = final_clip.set_audio(audio)

    # --- Exportar ---
    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=f".{output_type.lower()}")
    out_path = tmp_out.name
    tmp_out.close()

    if output_type == "MP4":
        final_clip.write_videofile(out_path, fps=24, codec="libx264")
    else:
        final_clip.write_gif(out_path, fps=10)

    st.success("Concluído.")
    with open(out_path, "rb") as f:
        st.download_button(
            label=f"Download {output_type}",
            data=f,
            file_name=f"countdown.{output_type.lower()}",
            mime="video/mp4" if output_type == "MP4" else "image/gif"
        )

    # Cleanup
    final_clip.close()
    if music_file:
        os.unlink(tmp_path)
    os.unlink(out_path)
