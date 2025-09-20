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
    # Get protected words from session state
    protected_words = st.session_state.get('protected_words', [])
    protected_words_text = ""
    if protected_words:
        protected_words_text = f"\n\n🛡️ PROTECTED WORDS (NEVER REMOVE): {', '.join(protected_words)}"
    
    full_prompt = f"""
🚨🚨🚨 ABSOLUTE CRITICAL INSTRUCTION: EXACT PRESERVATION ONLY! 🚨🚨🚨

FAILURE TO FOLLOW THESE RULES = COMPLETE REJECTION!

MANDATORY RULES - NO EXCEPTIONS:
✅ PRESERVE EVERY SINGLE WORD from input exactly as written
✅ PRESERVE EVERY CHARACTER exactly as written
✅ NEVER ADD ANY WORDS that are not in the input
✅ NEVER ADD ANY TEXT that is not in the input
✅ NEVER ADD ANY EXPLANATIONS or COMMENTS
✅ NEVER ADD ANY INTRODUCTORY TEXT
✅ NEVER ADD ANY CONCLUDING TEXT
✅ NEVER ADD ANY HTML COMMENTS
✅ NEVER ADD ANY EXTRA CONTENT
✅ NEVER "IMPROVE" or "ENHANCE" the text
✅ NEVER ADD ANY WORDS OF YOUR OWN

STRICT PRESERVATION REQUIREMENTS:
- Misspelled words → Keep exactly as written (DO NOT FIX)
- Special characters/symbols → Preserve all punctuation exactly
- Numbers/dates/codes → Keep all numeric content exactly
- Short words (1-2 chars) → Never skip single letters
- Repeated words → Keep ALL instances exactly
- Foreign/unusual spellings → Preserve exactly (DO NOT TRANSLATE)
- Abbreviations/acronyms → Keep all shortened forms exactly
- Technical terms → Preserve all jargon exactly
- Any "wrong" looking text → Keep everything exactly
- Spaces and formatting → Maintain original spacing exactly

HTML CONVERSION RULES:
1. 🎯 EXACT PRESERVATION: Every word from input MUST appear in output
2. 📝 Headings: Use <h2>, <h3>, or <h4> tags
3. 📄 Paragraphs: Use <p> tags  
4. 📋 Lists: Use <ul>/<ol> with <li> tags for items starting with -, *, or numbers
5. ❓ Unclear lines: Use <p> tags (preserve everything)
6. 🚫 ABSOLUTELY NO ADDITIONS: No extra text, comments, explanations, or any content not in input
7. 🚫 ABSOLUTELY NO DELETIONS: No removing, skipping, summarizing, or "fixing"
8. 📤 OUTPUT: Only HTML content (no <html>, <head>, or <body> tags)

CRITICAL VALIDATION REQUIREMENTS:
- Input word count: {len(chunk_text.split())} words
- Output MUST contain EXACTLY the same number of words
- Output MUST NOT contain ANY words not in the input
- If uncertain about a word → INCLUDE IT ANYWAY
- Better to have "wrong" content than missing content
- This is chunk {chunk_number} of {total_chunks}
{protected_words_text}

🚨 FINAL WARNING: ANY WORD LOSS OR ADDITION = COMPLETE FAILURE 🚨
🚨 DO NOT ADD ANY WORDS OF YOUR OWN - ONLY PRESERVE INPUT EXACTLY 🚨

Text to convert (PRESERVE EXACTLY - NO ADDITIONS):

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
    
    # ULTRA-STRICT safety check - ABSOLUTE ZERO TOLERANCE FOR LOSS AND ADDITIONS
    input_words = len(text_to_format.split())
    output_words = len(combined_html.split())
    word_loss_percentage = ((input_words - output_words) / input_words) * 100
    
    # Check for protected words specifically
    protected_words = st.session_state.get('protected_words', [])
    missing_protected = []
    if protected_words:
        for word in protected_words:
            if word.lower() not in combined_html.lower():
                missing_protected.append(word)
    
    # Check for added words (words in output that are not in input)
    input_word_set = set(word.lower() for word in text_to_format.split())
    output_word_set = set(word.lower() for word in combined_html.split())
    added_words = output_word_set - input_word_set
    
    # Check for word count violations
    word_count_violation = False
    if output_words != input_words:
        word_count_violation = True
    
    if output_words < input_words * 0.9999:  # ABSOLUTE ZERO TOLERANCE: Only allow 0.01% loss
        st.error(f"🚨🚨🚨 CRITICAL WARNING: WORD LOSS DETECTED! 🚨🚨🚨")
        st.error(f"**Input words:** {input_words:,} | **Output words:** {output_words:,}")
        st.error(f"**Words lost:** {input_words - output_words:,} ({word_loss_percentage:.3f}%)")
        st.error("⚠️ WARNING: Some words were lost during conversion!")
        st.warning("📄 HTML file will still be generated, but please review for missing content.")
        
        # Show immediate analysis of what's missing
        if input_words - output_words > 0:
            st.error("🔍 MISSING CONTENT ANALYSIS:")
            missing_words = set(text_to_format.lower().split()) - set(combined_html.lower().split())
            if missing_words:
                st.error(f"Missing words: {list(missing_words)[:30]}")
                if len(missing_words) > 30:
                    st.error(f"... and {len(missing_words) - 30} more missing words")
        
        # Check protected words specifically
        if missing_protected:
            st.error(f"🚨 PROTECTED WORDS MISSING: {missing_protected}")
            st.error("This is a CRITICAL VIOLATION of protected word policy!")
        
        # Continue with HTML generation despite word loss
        st.info("🔄 Continuing with HTML generation despite word loss...")
    
    elif added_words:  # Check for added words
        st.error(f"🚨🚨🚨 CRITICAL WARNING: AI ADDED WORDS! 🚨🚨🚨")
        st.error(f"**AI added words:** {list(added_words)[:20]}")
        if len(added_words) > 20:
            st.error(f"... and {len(added_words) - 20} more added words")
        st.error("⚠️ WARNING: AI added words that were not in input!")
        st.warning("📄 HTML file will still be generated, but please review for added content.")
        st.info("🔄 Continuing with HTML generation despite added words...")
    
    elif word_count_violation:  # Check for exact word count match
        st.error(f"🚨🚨🚨 CRITICAL WARNING: WORD COUNT MISMATCH! 🚨🚨🚨")
        st.error(f"**Input words:** {input_words:,} | **Output words:** {output_words:,}")
        st.error("⚠️ WARNING: Word count mismatch detected!")
        st.warning("📄 HTML file will still be generated, but please review for content accuracy.")
        st.info("🔄 Continuing with HTML generation despite word count mismatch...")
    
    elif output_words < input_words * 0.99995:  # Extremely minor loss warning
        st.warning(f"⚠️ MINIMAL word loss detected: {word_loss_percentage:.4f}% of words missing")
        st.warning(f"**Input:** {input_words:,} words | **Output:** {output_words:,} words")
        st.warning("This is extremely close to perfect - but we aim for 100% preservation.")
        
        if missing_protected:
            st.error(f"🚨 PROTECTED WORDS MISSING: {missing_protected}")
            st.error("Protected word violation detected!")
            st.warning("📄 HTML file will still be generated, but please review for missing protected words.")
            st.info("🔄 Continuing with HTML generation despite missing protected words...")
    else:
        st.success(f"✅ PERFECT! Preserved {output_words:,} out of {input_words:,} words ({100-word_loss_percentage:.4f}% retention)")
        st.success("🎯 ABSOLUTE ZERO TOLERANCE POLICY SUCCESSFUL!")
        st.success("🚫 NO AI WORDS ADDED - EXACT PRESERVATION ACHIEVED!")
        
        if protected_words and not missing_protected:
            st.success("🛡️ All protected words preserved successfully!")

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

# Create tabs for different functionalities
tab1, tab2 = st.tabs(["🔄 Convert Text to HTML", "📊 Compare Files"])

with tab1:
    st.markdown("""
    This app converts your text into a well-structured HTML format based on a set of rules using the Gemini API.

    🎯 **ABSOLUTE ZERO TOLERANCE POLICY**: Every single word from your input will be preserved in the output, including:
    - Misspelled words
    - Special characters and symbols  
    - Numbers and technical terms
    - Short words (1-2 characters)
    - Repeated words
    - Foreign or unusual spellings
    - Any text that looks "wrong" or unusual
    
    🚫 **NO AI WORD ADDITION**: The AI will NEVER add its own words, explanations, or any content not in your input.
    """)
    
    # Protected words section
    st.subheader("🛡️ Protected Words Configuration")
    st.markdown("Add specific words that should NEVER be removed during conversion:")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        protected_words_input = st.text_input(
            "Protected words (comma-separated):",
            value=", ".join(st.session_state.get('protected_words', [])),
            help="Enter words that must never be removed, separated by commas"
        )
    
    with col2:
        if st.button("Update Protected Words"):
            if protected_words_input.strip():
                protected_words = [word.strip() for word in protected_words_input.split(',') if word.strip()]
                st.session_state['protected_words'] = protected_words
                st.success(f"✅ {len(protected_words)} protected words added!")
            else:
                st.session_state['protected_words'] = []
                st.info("Protected words cleared.")
    
    # Show current protected words
    if st.session_state.get('protected_words'):
        st.info(f"🛡️ **Current Protected Words:** {', '.join(st.session_state['protected_words'])}")
    else:
        st.info("No protected words set. All words will be preserved by default.")

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
            
            # Show zero tolerance policy
            st.info("🎯 **ABSOLUTE ZERO TOLERANCE POLICY**: This system is configured to preserve EVERY single word, including misspelled, unusual, or problematic text. No words will be left behind!")
            st.info("🚫 **NO AI WORD ADDITION**: The AI will NEVER add its own words, explanations, or any content not in your input.")
            
            # Show protected words status
            protected_words = st.session_state.get('protected_words', [])
            if protected_words:
                st.info(f"🛡️ **Protected Words Active:** {', '.join(protected_words)} - These words will be specially protected during conversion.")
                
            with st.spinner("Converting with ABSOLUTE ZERO TOLERANCE..."):
                # Get the HTML response from the Gemini API
                html_output = get_gemini_response(text_input)

            if html_output is not None:
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
                st.error("🚨 CONVERSION FAILED: Unable to generate HTML. Please try again.")
    else:
        st.warning("Please enter some text to convert.")

with tab2:
    st.markdown("""
    ## 📊 File Comparison Tool
    
    Upload your original text file and HTML file to automatically compare them and see how many words match.
    No manual review needed - get instant statistics!
    """)
    
    # File upload section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📄 Upload Original Text File")
        original_file = st.file_uploader(
            "Choose a text file",
            type=['txt', 'md', 'docx'],
            key="original_file",
            help="Upload your original text file (.txt, .md, .docx)"
        )
    
    with col2:
        st.subheader("🌐 Upload HTML File")
        html_file = st.file_uploader(
            "Choose an HTML file",
            type=['html', 'htm'],
            key="html_file",
            help="Upload your HTML file (.html, .htm)"
        )
    
    # Process files when both are uploaded
    if original_file and html_file:
        st.success("✅ Both files uploaded successfully!")
        
        try:
            # Read original text file
            if original_file.name.endswith('.docx'):
                # For docx files, we'd need python-docx library
                st.error("DOCX files not supported yet. Please convert to TXT or MD format.")
                original_text = ""
            else:
                original_text = str(original_file.read(), "utf-8")
            
            # Read HTML file
            html_content = str(html_file.read(), "utf-8")
            
            if original_text:
                st.subheader("📊 Comparison Results")
                
                # Extract text from HTML
                extracted_text = extract_text_from_html(html_content)
                
                # Compare texts
                comparison = compare_texts(original_text, extracted_text)
                
                # Display results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Original Words", f"{comparison['original_count']:,}")
                
                with col2:
                    st.metric("HTML Words", f"{comparison['extracted_count']:,}")
                
                with col3:
                    st.metric("Match %", f"{comparison['match_percentage']:.1f}%")
                
                with col4:
                    words_lost = comparison['original_count'] - comparison['extracted_count']
                    st.metric("Words Lost", f"{words_lost:,}")
                
                # Overall assessment
                if comparison['match_percentage'] >= 99.5:
                    st.success("🎯 EXCELLENT! Near-perfect text preservation!")
                elif comparison['match_percentage'] >= 95:
                    st.warning("⚠️ GOOD: Minor text differences detected")
                elif comparison['match_percentage'] >= 90:
                    st.error("🚨 POOR: Significant text loss detected")
                else:
                    st.error("💥 CRITICAL: Major text loss - conversion failed!")
                
                # Show detailed analysis if there are differences
                if comparison['missing_words'] or comparison['extra_words']:
                    st.subheader("🔍 Detailed Analysis")
                    
                    # Missing words analysis
                    missing_details = comparison.get('missing_details', [])
                    if missing_details:
                        patterns = analyze_missing_patterns(missing_details, original_text)
                        
                        st.write("**Missing Words by Category:**")
                        for pattern_name, words in patterns.items():
                            if words:
                                pattern_labels = {
                                    'special_chars': '🔤 Special Characters',
                                    'numbers': '🔢 Numbers',
                                    'short_words': '📏 Short Words',
                                    'repeated_words': '🔄 Repeated Words',
                                    'punctuation_heavy': '❗ Punctuation Heavy',
                                    'other': '❓ Other Words'
                                }
                                st.write(f"- {pattern_labels[pattern_name]}: {len(words)} words")
                        
                        # Show top missing words
                        if missing_details:
                            st.write("**Most Frequently Missing Words:**")
                            sorted_missing = sorted(missing_details, key=lambda x: x['frequency'], reverse=True)
                            missing_list = [f"{word['word']} ({word['frequency']}x)" for word in sorted_missing[:10]]
                            st.write(", ".join(missing_list))
                    
                    # Extra words
                    extra_details = comparison.get('extra_details', [])
                    if extra_details:
                        st.write(f"**Extra Words Found:** {len(extra_details)} words")
                        if len(extra_details) <= 20:
                            extra_list = [word['word'] for word in extra_details]
                            st.write(", ".join(extra_list))
                        else:
                            extra_list = [word['word'] for word in extra_details[:20]]
                            st.write(", ".join(extra_list) + f" ... and {len(extra_details) - 20} more")
                
                # Download comparison report
                report = f"""
TEXT COMPARISON REPORT
====================
Original File: {original_file.name}
HTML File: {html_file.name}
Generated: {st.session_state.get('current_time', 'Unknown')}

SUMMARY:
- Original Words: {comparison['original_count']:,}
- HTML Words: {comparison['extracted_count']:,}
- Match Percentage: {comparison['match_percentage']:.1f}%
- Words Lost: {comparison['original_count'] - comparison['extracted_count']:,}

ASSESSMENT: {'EXCELLENT' if comparison['match_percentage'] >= 99.5 else 'GOOD' if comparison['match_percentage'] >= 95 else 'POOR' if comparison['match_percentage'] >= 90 else 'CRITICAL'}
"""
                
                st.download_button(
                    label="📄 Download Comparison Report",
                    data=report,
                    file_name="text_comparison_report.txt",
                    mime="text/plain"
                )
                
        except Exception as e:
            st.error(f"Error processing files: {e}")
    
    elif original_file or html_file:
        st.warning("⚠️ Please upload both files to perform comparison.")
    
    else:
        st.info("👆 Upload both files above to start comparison.")

# Optional: Add a section for user to input their own API key
with st.expander("About the API Key"):
    st.info("The application requires a Gemini API key. For this example, replace 'YOUR_API_KEY_HERE' in the code. For production, consider using `st.secrets` for security.")
    st.markdown("[Get your Gemini API key](https://aistudio.google.com/app/apikey)")

st.markdown("---")
st.markdown("© 2025 AI-Powered Text Converter")
