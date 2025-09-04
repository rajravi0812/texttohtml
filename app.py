import streamlit as st
import google.generativeai as genai
import os

# Set the page configuration at the very beginning of the script
st.set_page_config(
    page_title="Text to HTML Converter",
    page_icon="✍️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Set up the Gemini API key from environment variables or direct assignment
# For security, it's best to use st.secrets or environment variables.
genai.configure(api_key="AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY")  # ⚠️ Replace with st.secrets["GEMINI_API_KEY"] in production

# Function to get the Gemini response
def get_gemini_response(text_to_format):
    """
    Sends the user's text and formatting rules to the Gemini API and returns the response.
    Ensures no words are skipped or altered.
    """
    full_prompt = f"""
You are given raw text. Your job is to strictly convert ALL of it into valid HTML, 
following these rules:

1. DO NOT delete, skip, shorten, or change ANY words from the input. Every line must appear in the output.
2. If a line looks like a heading, wrap it in <h2>, <h3>, or <h4>.
3. If a line is normal text, wrap it in <p>.
4. If a line looks like a list item (starts with -, *, or a number), put it inside <ul>/<ol> with <li>.
5. If you are unsure how to classify a line, wrap it in <p>.
6. Do NOT add any extra text, comments, explanations, or code fences.
7. Output ONLY the HTML content (no <html>, <head>, or <body>).

Here is the text to convert:

{text_to_format}
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(full_prompt)

        cleaned_text = response.text.strip()

        # Remove markdown fences only
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text[len("```html"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()

        # Safety check: verify no major text loss
        input_words = len(text_to_format.split())
        output_words = len(cleaned_text.split())
        if output_words < input_words * 0.95:  # Allow small variation
            st.warning("⚠️ Some text might be missing in the conversion. Please verify carefully.")

        return cleaned_text

    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None


# Streamlit App UI
st.title("📄 Text to HTML Converter with Gemini API")

st.markdown("""
This app converts your text into a well-structured HTML format based on a set of rules using the Gemini API.
""")

# Input for the user's text
text_input = st.text_area(
    "Enter your text here:",
    height=250,
    placeholder="Type or paste the text you want to convert to HTML...",
)

# Button to trigger the conversion
if st.button("Convert to HTML", type="primary"):
    if text_input:
        with st.spinner("Converting..."):
            # Get the HTML response from the Gemini API
            html_output = get_gemini_response(text_input)

            if html_output:
                st.subheader("Generated HTML:")

                # Use st.code to display the raw HTML code
                st.code(html_output, language='html')

                st.subheader("Rendered HTML Preview:")

                # Create a simple HTML page to display the output
                html_page = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <title>HTML Preview</title>
                <style>
                    body {{
                        background-color: #f0f2f6;
                        color: #31333f;
                        font-family: Arial, sans-serif;
                    }}
                </style>
                </head>
                <body>
                {html_output}
                </body>
                </html>
                """

                # Use st.components.v1.html to render the HTML content
                st.components.v1.html(html_page, height=500, scrolling=True)

                # ✅ Download button for HTML file
                st.download_button(
                    label="💾 Download HTML File",
                    data=html_output,
                    file_name="converted_text.html",
                    mime="text/html"
                )

            else:
                st.warning("Could not generate HTML. Please try again.")
    else:
        st.warning("Please enter some text to convert.")

# Optional: Add a section for user to input their own API key
with st.expander("About the API Key"):
    st.info("The application requires a Gemini API key. For this example, replace 'YOUR_API_KEY_HERE' in the code. For production, consider using `st.secrets` for security.")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")

st.markdown("---")
st.markdown("© 2025 AI-Powered Text Converter")
