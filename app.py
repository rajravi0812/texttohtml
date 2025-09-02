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
# Replace with your actual key or st.secrets
genai.configure(api_key="AIzaSyC60uyhgxLvsGUZMO3mrAj120oybFF3KnY") 

# Function to get the Gemini response
def get_gemini_response(prompt, text_to_format):
    """
    Sends the user's text and formatting rules to the Gemini API and returns the response.
    It also cleans the output to remove extra text.
    """
    model = genai.Generativeai.GenerativeModel('gemini-1.5-flash')
    
    # Refined and more explicit prompt
    full_prompt = (
        "I need you to convert the following raw text into a well-structured HTML code snippet. "
        "Strictly adhere to these rules:\n\n"
        "1. Convert all text into a well-structured HTML format with proper spacing and indentation.\n"
        "2. Use only <h2>, <h3>, and <h4> tags for headings and subheadings.\n"
        "3. Use <p> tags for paragraphs.\n"
        "4. Use <ul> and <ol> with <li> for lists where necessary.\n"
        "5. DO NOT ADD OR REMOVE ANY WORDS FROM THE ORIGINAL TEXT.\n"
        "6. DO NOT ADD ANY INTRODUCTORY OR EXPLANATORY TEXT. ONLY PROVIDE THE HTML CODE.\n"
        "7. No inline CSS or external styling should be used.\n"
        "8. The entire formatted content should appear only inside the <body> tag. "
        "Do not include <html>, <head>, or <body> tags in your response. "
        "Just provide the content that would go inside the <body> tag.\n\n"
        "Text to format:\n\n"
        f"{text_to_format}"
    )
    
    try:
        response = model.generate_content(full_prompt)
        
        # Post-processing to clean the output
        cleaned_text = response.text.strip()
        
        # Remove markdown code fences and any trailing explanation
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text[len("```html"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")].strip()
            
        # The model might sometimes add a brief introductory sentence. Remove it.
        # This is a bit of a heuristic, but it often works.
        first_line = cleaned_text.split('\n')[0].strip()
        if not first_line.startswith(("<h", "<p", "<ul", "<ol")):
            # If the first line doesn't look like an HTML tag, assume it's intro text and remove it
            cleaned_text = '\n'.join(cleaned_text.split('\n')[1:]).strip()
            
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
            html_output = get_gemini_response("", text_input)

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
            else:
                st.warning("Could not generate HTML. Please try again.")
    else:
        st.warning("Please enter some text to convert.")

# Optional: Add a section for user to input their own API key
with st.expander("About the API Key"):
    st.info("The application requires a Gemini API key. For this example, replace 'YOUR_API_KEY' in the code. For production, consider using `st.secrets` for security.")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")

st.markdown("---")
st.markdown("© 2025 AI-Powered Text Converter")