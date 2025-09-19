import streamlit as st
import google.generativeai as genai
import os
import re

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
def split_text_into_chunks(text, chunk_size=4000):
    """
    Split text into chunks of approximately chunk_size words.
    Tries to break at sentence boundaries when possible.
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunk_text = ' '.join(chunk_words)
        
        # Try to break at sentence boundary if not the last chunk
        if i + chunk_size < len(words):
            # Look for sentence endings in the last 200 words of the chunk
            last_sentences = chunk_text[-500:].rsplit('.', 1)
            if len(last_sentences) > 1 and len(last_sentences[0]) > chunk_size * 0.7:
                chunk_text = last_sentences[0] + '.'
                # Adjust the index to account for the shorter chunk
                words = text.split()
                actual_words = chunk_text.split()
                i = len(actual_words) - 1
        
        chunks.append(chunk_text)
    
    return chunks


def process_single_chunk(chunk_text, chunk_number, total_chunks):
    """
    Process a single chunk of text with Gemini API.
    """
    full_prompt = f"""
CRITICAL INSTRUCTION: You must preserve EVERY SINGLE WORD from the input text. Do not skip, delete, or modify any content.

Convert the following text into valid HTML following these rules:

1. PRESERVE ALL TEXT: Every single word, character, and line from the input must appear in the output.
2. For headings: Use <h2>, <h3>, or <h4> tags
3. For paragraphs: Use <p> tags
4. For lists: Use <ul>/<ol> with <li> tags for items starting with -, *, or numbers
5. For unclear lines: Use <p> tags (better to be safe)
6. NO ADDITIONS: Do not add any extra text, comments, or explanations
7. NO DELETIONS: Do not remove, skip, or summarize any content
8. OUTPUT FORMAT: Only HTML content (no <html>, <head>, or <body> tags)

IMPORTANT: This is chunk {chunk_number} of {total_chunks}. The input contains {len(chunk_text.split())} words. Your output must contain approximately the same number of words.

Text to convert:

{chunk_text}
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(full_prompt)

        cleaned_text = response.text.strip()

        # Remove markdown fences and any explanatory text
        if cleaned_text.startswith("```html"):
            cleaned_text = cleaned_text[len("```html"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3].strip()
        
        # Remove any introductory text that might be added by the model
        lines = cleaned_text.split('\n')
        html_start = 0
        for i, line in enumerate(lines):
            if line.strip().startswith(('<h', '<p', '<ul', '<ol', '<li', '<div')):
                html_start = i
                break
        
        if html_start > 0:
            cleaned_text = '\n'.join(lines[html_start:]).strip()

        return cleaned_text

    except Exception as e:
        st.error(f"Error processing chunk {chunk_number}: {e}")
        return None


def get_gemini_response(text_to_format):
    """
    Processes text in chunks to handle large documents and ensure no content loss.
    """
    total_words = len(text_to_format.split())
    
    # If text is small enough, process normally
    if total_words <= 4000:
        return process_single_chunk(text_to_format, 1, 1)
    
    # Split into chunks
    chunks = split_text_into_chunks(text_to_format, 4000)
    st.info(f"📄 Processing {len(chunks)} chunks ({total_words:,} total words)")
    
    processed_chunks = []
    progress_bar = st.progress(0)
    
    for i, chunk in enumerate(chunks):
        st.write(f"Processing chunk {i+1}/{len(chunks)}...")
        processed_chunk = process_single_chunk(chunk, i+1, len(chunks))
        
        if processed_chunk is None:
            st.error(f"Failed to process chunk {i+1}")
            return None
        
        processed_chunks.append(processed_chunk)
        progress_bar.progress((i + 1) / len(chunks))
    
    # Combine all chunks
    combined_html = '\n\n'.join(processed_chunks)
    
    # Final safety check
    input_words = len(text_to_format.split())
    output_words = len(combined_html.split())
    word_loss_percentage = ((input_words - output_words) / input_words) * 100
    
    if output_words < input_words * 0.98:  # Stricter threshold - only allow 2% loss
        st.error(f"🚨 CRITICAL: Severe text loss detected!")
        st.error(f"**Input words:** {input_words:,} | **Output words:** {output_words:,}")
        st.error(f"**Words lost:** {input_words - output_words:,} ({word_loss_percentage:.1f}%)")
        st.error("The conversion is missing significant content. Please try again or check the prompt.")
    elif output_words < input_words * 0.99:  # Minor loss warning
        st.warning(f"⚠️ Minor text loss detected: {word_loss_percentage:.1f}% of words missing")
        st.warning(f"**Input:** {input_words:,} words | **Output:** {output_words:,} words")
    else:
        st.success(f"✅ Text processing completed! Preserved {output_words:,} out of {input_words:,} words ({100-word_loss_percentage:.1f}% retention)")

    return combined_html


def extract_text_from_html(html_content):
    """
    Extract plain text from HTML content by removing all HTML tags.
    """
    # Remove HTML tags using regex
    text = re.sub(r'<[^>]+>', '', html_content)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def analyze_missing_words(original_text, extracted_text):
    """
    Detailed analysis of missing words with context and patterns.
    """
    original_words = original_text.split()
    extracted_words = extracted_text.split()
    
    # Create word frequency maps
    original_freq = {}
    extracted_freq = {}
    
    for word in original_words:
        word_lower = word.lower()
        original_freq[word_lower] = original_freq.get(word_lower, 0) + 1
    
    for word in extracted_words:
        word_lower = word.lower()
        extracted_freq[word_lower] = extracted_freq.get(word_lower, 0) + 1
    
    # Find missing words with their original case and frequency
    missing_details = []
    for word in original_words:
        word_lower = word.lower()
        if word_lower not in extracted_freq:
            missing_details.append({
                'word': word,
                'word_lower': word_lower,
                'frequency': original_freq[word_lower]
            })
        elif original_freq[word_lower] > extracted_freq[word_lower]:
            missing_count = original_freq[word_lower] - extracted_freq[word_lower]
            missing_details.append({
                'word': word,
                'word_lower': word_lower,
                'frequency': missing_count,
                'partial': True
            })
    
    # Find extra words
    extra_details = []
    for word in extracted_words:
        word_lower = word.lower()
        if word_lower not in original_freq:
            extra_details.append({
                'word': word,
                'word_lower': word_lower,
                'frequency': extracted_freq[word_lower]
            })
        elif extracted_freq[word_lower] > original_freq[word_lower]:
            extra_count = extracted_freq[word_lower] - original_freq[word_lower]
            extra_details.append({
                'word': word,
                'word_lower': word_lower,
                'frequency': extra_count,
                'partial': True
            })
    
    return {
        'original_count': len(original_words),
        'extracted_count': len(extracted_words),
        'missing_details': missing_details,
        'extra_details': extra_details,
        'match_percentage': (len(set(word.lower() for word in original_words) & set(word.lower() for word in extracted_words)) / len(set(word.lower() for word in original_words))) * 100 if original_words else 0
    }


def find_word_context(original_text, missing_word, context_size=50):
    """
    Find the context around a missing word to help identify why it might be missing.
    """
    words = original_text.split()
    contexts = []
    
    for i, word in enumerate(words):
        if word.lower() == missing_word.lower():
            start = max(0, i - context_size)
            end = min(len(words), i + context_size + 1)
            context = ' '.join(words[start:end])
            contexts.append({
                'position': i,
                'context': context,
                'word_position': i - start
            })
    
    return contexts


def analyze_missing_patterns(missing_details, original_text):
    """
    Analyze patterns in missing words to identify common causes.
    """
    patterns = {
        'special_chars': [],
        'numbers': [],
        'short_words': [],
        'repeated_words': [],
        'punctuation_heavy': [],
        'other': []
    }
    
    for word_info in missing_details:
        word = word_info['word']
        
        if any(char in word for char in '!@#$%^&*()_+-=[]{}|;:,.<>?/~`'):
            patterns['special_chars'].append(word_info)
        elif word.isdigit() or any(char.isdigit() for char in word):
            patterns['numbers'].append(word_info)
        elif len(word) <= 2:
            patterns['short_words'].append(word_info)
        elif word_info['frequency'] > 1:
            patterns['repeated_words'].append(word_info)
        elif sum(1 for c in word if c in '.,!?;:') > len(word) * 0.3:
            patterns['punctuation_heavy'].append(word_info)
        else:
            patterns['other'].append(word_info)
    
    return patterns


def compare_texts(original_text, extracted_text):
    """
    Compare original text with extracted text and return comparison results.
    """
    # Use the detailed analysis function
    analysis = analyze_missing_words(original_text, extracted_text)
    
    return {
        'original_count': analysis['original_count'],
        'extracted_count': analysis['extracted_count'],
        'missing_words': [item['word_lower'] for item in analysis['missing_details']],
        'extra_words': [item['word_lower'] for item in analysis['extra_details']],
        'match_percentage': analysis['match_percentage'],
        'missing_details': analysis['missing_details'],
        'extra_details': analysis['extra_details']
    }


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
        # Show processing info for large texts
        word_count = len(text_input.split())
        if word_count > 4000:
            st.info(f"📊 Large text detected: {word_count:,} words. Will be processed in chunks for better accuracy.")
        
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

                # 🔍 Text Comparison Section
                st.subheader("📊 Text Comparison Analysis")
                
                # Extract text from HTML for comparison
                extracted_text = extract_text_from_html(html_output)
                comparison = compare_texts(text_input, extracted_text)
                
                # Display comparison results
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Original Words", comparison['original_count'])
                
                with col2:
                    st.metric("Extracted Words", comparison['extracted_count'])
                
                with col3:
                    st.metric("Match Percentage", f"{comparison['match_percentage']:.1f}%")
                
                # Show detailed comparison
                if comparison['missing_words'] or comparison['extra_words']:
                    if comparison['match_percentage'] < 50:
                        st.error("🚨 CRITICAL: Major text loss detected!")
                    elif comparison['match_percentage'] < 90:
                        st.warning("⚠️ Significant text differences detected!")
                    else:
                        st.warning("⚠️ Minor text differences detected!")
                    
                    # Analyze missing word patterns
                    missing_details = comparison.get('missing_details', [])
                    if missing_details:
                        patterns = analyze_missing_patterns(missing_details, text_input)
                        
                        st.subheader("🔍 Missing Words Analysis")
                        
                        # Show pattern-based analysis
                        for pattern_name, words in patterns.items():
                            if words:
                                pattern_labels = {
                                    'special_chars': '🔤 Special Characters',
                                    'numbers': '🔢 Numbers',
                                    'short_words': '📏 Short Words (≤2 chars)',
                                    'repeated_words': '🔄 Repeated Words',
                                    'punctuation_heavy': '❗ Punctuation Heavy',
                                    'other': '❓ Other Words'
                                }
                                
                                with st.expander(f"{pattern_labels[pattern_name]} ({len(words)} words)"):
                                    for word_info in words[:20]:  # Show first 20
                                        freq_text = f" (appears {word_info['frequency']} times)" if word_info['frequency'] > 1 else ""
                                        partial_text = " (partially missing)" if word_info.get('partial') else ""
                                        st.write(f"• **{word_info['word']}**{freq_text}{partial_text}")
                                        
                                        # Show context for this word
                                        contexts = find_word_context(text_input, word_info['word'])
                                        if contexts:
                                            st.caption(f"Context: ...{contexts[0]['context'][:100]}...")
                                    
                                    if len(words) > 20:
                                        st.caption(f"... and {len(words) - 20} more words in this category")
                        
                        # Show top missing words by frequency
                        if missing_details:
                            st.subheader("📊 Most Frequently Missing Words")
                            sorted_missing = sorted(missing_details, key=lambda x: x['frequency'], reverse=True)
                            
                            col1, col2, col3 = st.columns(3)
                            for i, word_info in enumerate(sorted_missing[:15]):
                                col = [col1, col2, col3][i % 3]
                                with col:
                                    st.write(f"**{word_info['word']}** ({word_info['frequency']}x)")
                    
                    # Show extra words
                    extra_details = comparison.get('extra_details', [])
                    if extra_details:
                        st.subheader("➕ Extra Words Found")
                        with st.expander(f"Extra words ({len(extra_details)} words)"):
                            for word_info in extra_details[:20]:
                                freq_text = f" (appears {word_info['frequency']} times)" if word_info['frequency'] > 1 else ""
                                st.write(f"• **{word_info['word']}**{freq_text}")
                            
                            if len(extra_details) > 20:
                                st.caption(f"... and {len(extra_details) - 20} more extra words")
                else:
                    st.success("✅ Perfect match! All text has been preserved.")
                
                # Show side-by-side comparison
                with st.expander("🔍 Detailed Text Comparison"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Original Text")
                        st.text_area("", value=text_input, height=200, disabled=True, key="original_text")
                    
                    with col2:
                        st.subheader("Extracted Text (from HTML)")
                        st.text_area("", value=extracted_text, height=200, disabled=True, key="extracted_text")

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
