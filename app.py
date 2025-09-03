import streamlit as st
import google.genai as genai

# -------------------------
# 🔑 API Key Initialization
# -------------------------
client = genai.Client(api_key="AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY")

# -------------------------
# 🎙️ Streamlit UI
# -------------------------
st.title("🎧 Audio → Transcript Converter (Gemini API)")

uploaded_file = st.file_uploader("Upload an audio file", type=["mp3", "m4a"])

if uploaded_file is not None:
    # Streamlit can preview mp3 but not always m4a, so just try:
    try:
        st.audio(uploaded_file)
    except Exception:
        st.warning("Preview not available for this format, but transcription will still work ✅")

    if st.button("Transcribe Audio"):
        # Save uploaded file locally
        with open("temp." + uploaded_file.type.split("/")[-1], "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Transcribing... please wait ⏳"):
            # Upload to Gemini
            myfile = client.files.upload(file=f.name)

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
