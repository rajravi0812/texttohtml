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
# For local use, a .env file is good.
# Example using direct assignment for demonstration, but not recommended for production.
# Replace with your actual key or st.secrets
genai.configure(api_key="AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY") 

# Function to get the Gemini response
def get_gemini_response(prompt, text_to_format):
    """
    Sends the user's text and formatting rules to the Gemini API and returns the response.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    full_prompt = (
        f"{prompt}\n\n"
        f"Text to format:\n{text_to_format}"
    )
    try:
        response = model.generate_content(full_prompt)
        return response.text
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

# Define the rules for the API
rules = """
Convert the following text into a well-structured HTML format with proper spacing and indentation.
Use only <h2>, <h3>, and 4 tags for headings and subheadings.
Use <p> tags for paragraphs.
Use <ul> and <ol> with <li> for lists where necessary.
Do not add or remove any words from the text.
No inline CSS or external styling should be used.
The entire formatted content should appear only inside the <body> tag.
Ensure the output is clean HTML code, not a prose explanation of the code.
"""

# Button to trigger the conversion
if st.button("Convert to HTML", type="primary"):
    if text_input:
        with st.spinner("Converting..."):
            # Get the HTML response from the Gemini API
            html_output = get_gemini_response(rules, text_input)

            if html_output:
                st.subheader("Generated HTML:")
                
                # Use st.code to display the raw HTML code
                st.code(html_output, language='html')
                
                st.subheader("Rendered HTML Preview:")
                
                # Create a simple HTML page to display the output
                # Inject a CSS style to force a light theme for the body.
                html_page = f"""
                <!DOCTYPE html>
                <html>
                <head>
                <title>HTML Preview</title>
                <style>
                    body {{
                        background-color: #f0f2f6; /* A light, soft gray background */
                        color: #31333f; /* A dark text color for readability */
                    }}
                </style>
                </head>
                <body>
                {html_output}
                </body>
                </html>
                """
                
                # Use st.components.v1.html to render the HTML content
                # This ensures the preview is always readable regardless of the Streamlit theme
                st.components.v1.html(html_page, height=500, scrolling=True)
            else:
                st.warning("Could not generate HTML. Please try again.")
    else:
        st.warning("Please enter some text to convert.")

# Optional: Add a section for user to input their own API key
# This is a good practice for public apps.
with st.expander("About the API Key"):
    st.info("The application requires a Gemini API key. For this example, replace 'YOUR_API_KEY' in the code. For production, consider using `st.secrets` for security.")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")

st.markdown("---")
st.markdown("© 2025 AI-Powered Text Converter")