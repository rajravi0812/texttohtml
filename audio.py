import streamlit as st
import google.genai as genai
import os

# -------------------------
# 🔑 API Key Initialization
# -------------------------
client = genai.Client(api_key="AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY")

# -------------------------
# 🎙️ Streamlit UI
# -------------------------
st.title("🎧 Audio → Transcript Converter (Gemini API)")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "m4a", "wav", "flac"])

if uploaded_file is not None:
    # Preview audio (works for mp3/wav, sometimes not for m4a)
    try:
        st.audio(uploaded_file)
    except Exception:
        st.warning("Preview not available for this format, but transcription will still work ✅")

    if st.button("Transcribe Audio"):
        # Build file path
        file_extension = uploaded_file.name.split(".")[-1]
        file_path = f"temp.{file_extension}"

        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Transcribing... please wait ⏳"):
            # ✅ Upload file path to Gemini
            myfile = client.files.upload(file=file_path)

            # Ask Gemini to transcribe
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # or "gemini-2.5-pro"
                contents=["Please transcribe this audio:", myfile]
            )

        # Get transcript
        transcript = response.text if response and response.text else "No transcript found."

        # Display transcript
        st.subheader("📝 Transcript")
        st.write(transcript)

        # Download option
        st.download_button(
            label="⬇️ Download Transcript",
            data=transcript,
            file_name="transcript.txt",
            mime="text/plain"
        )
