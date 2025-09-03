import streamlit as st
from google import genai

# -------------------------
# 🔑 API Key Initialization
# -------------------------
client = genai.Client(api_key="AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY")

# -------------------------
# 🎙️ Streamlit UI
# -------------------------
st.title("🎧 MP3 → Transcript Converter (Gemini API)")

uploaded_file = st.file_uploader("Upload an MP3 file", type=["mp3"])

if uploaded_file is not None:
    st.audio(uploaded_file, format="audio/mp3")

    if st.button("Transcribe Audio"):
        # Save uploaded file locally
        with open("temp.mp3", "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("Transcribing... please wait ⏳"):
            # Upload to Gemini
            myfile = client.files.upload(file="temp.mp3")

            # Ask Gemini to transcribe
            response = client.models.generate_content(
                model="gemini-2.5-flash",  # or "gemini-2.5-pro" for better accuracy
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
