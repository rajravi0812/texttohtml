import streamlit as st
import google.generativeai as genai

# --- Setup ---
st.set_page_config(page_title="Text → HTML Formatter (Gemini)", page_icon="📝", layout="wide")

st.title("📝 Text → HTML Formatter (Gemini API)")
st.write("Paste any text below and it will be reformatted into clean HTML with headings, subheadings, bullets, and numbered points.")

# --- Directly set Gemini API key ---
API_KEY = "AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY"
genai.configure(api_key=API_KEY)

# Input text
raw_text = st.text_area("📌 Paste your text here:", height=300)

if st.button("Format Text"):
    if not raw_text.strip():
        st.error("Please paste some text.")
    else:
        try:
            # Load model
            model = genai.GenerativeModel("gemini-1.5-flash")

            with st.spinner("Formatting your text..."):
                response = model.generate_content(
                    f"""
                    You are a strict text-to-HTML formatter. 
                    Your task is ONLY to wrap the given text in HTML tags for structure. 
                    
                    ❌ Do NOT add, change, or invent any content. 
                    ❌ Do NOT summarize or expand. 
                    
                    ✅ Only organize the provided text with:
                        - <h3> for main headings
                        - <h4> for subheadings
                        - <ol> for numbered lists
                        - <ul> for bullet points
                        - <p> for normal text

                    Return ONLY valid HTML.

                    Text to format:
                    {raw_text}
                    """
                )

            formatted_html = response.text.strip()

            st.success("✅ Formatting complete!")

            st.markdown("### ✨ Formatted Preview")
            st.markdown(formatted_html, unsafe_allow_html=True)

            # Show raw HTML
            st.markdown("### 🧾 HTML Code")
            st.code(formatted_html, language="html")

            # Download option
            st.download_button(
                "⬇ Download HTML File",
                data=formatted_html,
                file_name="formatted_text.html",
                mime="text/html",
            )

        except Exception as e:
            st.error(f"Error: {str(e)}")
