import streamlit as st
import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
import re
import textstat
import io
import markdown2
from xhtml2pdf import pisa
from datetime import datetime

# Load environment variables
load_dotenv()

# Set Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ----- BLOG OPTIMIZATION -----
def optimize_existing_blog(current_blog, tone):
    adjusted_tone = {
        "Polished Professional": "an authoritative, brand-aligned professional tone with marketing polish",
        "Conversational Expert": "an engaging, confident expert tone that sounds natural and conversational",
        "Editorial Journalistic": "a branded journalistic tone that subtly highlights clients and brand contributions without sounding like a hard sell"
    }.get(tone, tone.lower())

    prompt = f"""
You are an expert-level SEO strategist, conversion-focused blog editor, and professional content humanizer.

Your task is to fully analyze and optimize the blog content provided below to look 100% human-written, naturally flowing, and deeply engaging — while also being SEO-optimized.

This is a **branded editorial blog**—its goal is to inform and subtly promote the company’s associated clients as leaders within the industry while maintaining a journalistic, story-driven tone.

Make sure to do this — very important:

Keep Flesch reading score between 60–75 (grade 8–10 level)

Write the blog in a **{adjusted_tone}**.

Apply these exact principles:

Make sure to include Intro and conclusion.

1. Identify what the blog is about and who the target audience is.
2. Extract and apply the main keyword and top LSI keywords related to the topic using your understanding of search trends.
3. Use keywords naturally across:
   - Title
   - Headings (use keyword/LSI where appropriate)
   - Intro, body, and conclusion
   - Maintain balanced keyword frequency with good spacing

4. Make the blog feel genuinely human-written:
   - No robotic tone, formulaic phrasing, or obvious AI patterns
   - Avoid lines like "In this blog...", "Let's explore...", or generic intro/openings
   - Add storytelling, expert opinion, and natural transitions

5. Structure the blog with strong formatting and flow:
   - Use H2 for main sections, H3 for subpoints
   - Ensure clear section hierarchy and logical flow
   - Short paragraphs (ideally 2–4 lines)
   - Maintain consistent content length per section

6. Improve or add:
   - A compelling, emotional **Introduction** with a clear hook
   - A thoughtful **Conclusion** that summarizes key insights and includes a CTA
   - Relevant **FAQs** formatted with question + concise answer (if the topic suits it)

7. Ensure excellent readability:
   - Use plain English and simple vocabulary
   - Keep sentence structures clean and transitions smooth
   - Keep Flesch reading score between 60–75 (grade 8–10 level)

8. Use smart visual elements for scannability:
   - Bullet points and numbered lists where helpful
   - Use **bold text** to emphasize important insights or stats
   - Include tables to show comparisons, summaries, or grouped information

9. Link logically and naturally:
   - Internal links to relevant blogs/pages 
   - Outbound links to trusted sources 
   - Use meaningful, descriptive anchor texts

10. Optimize for on-page SEO meta:
   - SEO Meta Title (≤ 60 characters)
   - SEO Meta Description (≤ 155 characters)
   - Meta Keywords (comma-separated)
   - Slug suggestion

Strictly avoid:
- Markdown, asterisks, dashes, or visible formatting characters
- Repetitive filler phrases
- Any line or tone that makes it obvious it was AI-generated

==> Blog to Optimize:
{current_blog}
"""
    model = genai.GenerativeModel("models/gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

# ----- CATEGORY DETECTION -----
def detect_blog_category(blog_text):
    text_lower = blog_text.lower()
    if "step-by-step" in text_lower or "how to" in text_lower or "guide" in text_lower:
        return "How-to Guide"
    elif "our client" in text_lower or "we created" in text_lower or "growify" in text_lower:
        return "Promotional"
    elif "fashion industry" in text_lower or "trend" in text_lower or "revolutionize" in text_lower:
        return "Journalistic"
    elif "benefits of" in text_lower or "reasons why" in text_lower:
        return "Informational"
    else:
        return "Mixed/Unclassified"

# ----- CLEAN + ANALYZE FUNCTIONS -----
def ensure_heading_structure(text):
    text = re.sub(r'(?<!#)\b(FAQs|Conclusion|Introduction|Summary)\b', r'## \1', text)
    text = re.sub(r'(?<!#)\n([A-Z][^\n]{5,100})\n', r'## \1', text)
    return text

def clean_ai_elements(text):
    return re.sub(r'[*_~`<>^=\\-]+', '', text)

def readability_score(text):
    score = textstat.flesch_reading_ease(text)
    grade = textstat.text_standard(text, float_output=False)
    return f"📖 Readability Score: {score:.2f} (Grade Level: {grade})"

def check_links(text):
    outbound = re.findall(r'(https?://[^\s]+)', text)
    internal = re.findall(r'\[[^\]]+\]\([^\)]+\)', text)
    return f"🔗 Outbound Links: {len(outbound)}, Internal Links: {len(internal)}"

def check_intro_conclusion(text):
    intro = "Yes" if "introduction" in text.lower() else "No"
    conclusion = "Yes" if "conclusion" in text.lower() else "No"
    return f"🧩 Intro Present: {intro}, Conclusion Present: {conclusion}"

def extract_meta(text):
    meta_title = re.search(r"SEO Meta Title.*?:\s*(.+)", text)
    meta_description = re.search(r"SEO Meta Description.*?:\s*(.+)", text)
    return (meta_title.group(1).strip() if meta_title else "Untitled Blog",
            meta_description.group(1).strip() if meta_description else "No description found")

# ----- PDF BUILD (NO MANUAL META AT TOP) -----
def build_html_blog_pdf(meta_title: str, meta_description: str, blog_content: str) -> str:
    blog_html = markdown2.markdown(blog_content, extras=["tables", "fenced-code-blocks"])
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 12pt;
                line-height: 1.6;
                color: #222;
            }}
            h1 {{
                font-size: 22pt;
                text-align: center;
                color: #333;
            }}
            h2 {{
                font-size: 16pt;
                color: #444;
                margin-top: 20px;
            }}
            h3 {{
                font-size: 13pt;
                color: #555;
                margin-top: 15px;
            }}
            p, li {{
                font-size: 12pt;
                margin-bottom: 10px;
            }}
        </style>
    </head>
    <body>
        {blog_html}
        <br><br>
        <small>Generated on {date_str}</small>
    </body>
    </html>
    """
    return html

def convert_to_pdf(meta_title, meta_description, blog_content):
    html = build_html_blog_pdf(meta_title, meta_description, blog_content)
    result = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html), dest=result)
    return result.getvalue()

# ----- STREAMLIT APP -----
def main():
    st.title("📈 Optimize Your Existing Blog for SEO")

    tone = st.selectbox("🎙️ Choose Tone Style", ["Polished Professional", "Conversational Expert", "Editorial Journalistic"])
    uploaded_file = st.file_uploader("📂 Upload Blog (.txt or .md)", type=["txt", "md"])

    if "current_blog" not in st.session_state:
        st.session_state["current_blog"] = ""
    if "raw_blog" not in st.session_state:
        st.session_state["raw_blog"] = ""
    if "category" not in st.session_state:
        st.session_state["category"] = ""
    if "last_uploaded_hash" not in st.session_state:
        st.session_state["last_uploaded_hash"] = None

    # Upload & reoptimize if new file
    if uploaded_file:
        blog_content = uploaded_file.read().decode("utf-8")
        blog_content_clean = clean_ai_elements(blog_content)
        new_hash = hash(blog_content_clean)

        if st.session_state["last_uploaded_hash"] != new_hash:
            st.session_state["raw_blog"] = blog_content_clean
            st.session_state["current_blog"] = ""
            st.session_state["category"] = ""
            st.session_state["last_uploaded_hash"] = new_hash

            detected = detect_blog_category(blog_content_clean)
            st.session_state["category"] = detected
            st.success(f"📂 Detected Blog Category: {detected}")

            auto_tone_map = {
                "Promotional": "Polished Professional",
                "Journalistic": "Editorial Journalistic",
                "How-to Guide": "Conversational Expert",
            }
            effective_tone = auto_tone_map.get(detected, tone)

            with st.spinner("Optimizing blog with Gemini..."):
                optimized = optimize_existing_blog(blog_content_clean, effective_tone)
                optimized = ensure_heading_structure(optimized)
                st.session_state["current_blog"] = optimized

    # Manual re-generation button
    if st.session_state["raw_blog"] and st.session_state["current_blog"]:
        if st.button("♻️ Regenerate Optimized Blog"):
            effective_tone = tone
            with st.spinner("Re-optimizing with Gemini..."):
                optimized = optimize_existing_blog(st.session_state["raw_blog"], effective_tone)
                optimized = ensure_heading_structure(optimized)
                st.session_state["current_blog"] = optimized

    # Show output
    if st.session_state["current_blog"]:
        st.subheader("📄 Optimized Blog")
        st.markdown(st.session_state["current_blog"].replace('\n', '  \n'))

        st.markdown("### 📊 Optimization Report")
        st.text(readability_score(st.session_state["current_blog"]))
        st.text(check_links(st.session_state["current_blog"]))
        st.text(check_intro_conclusion(st.session_state["current_blog"]))

        st.download_button("📥 Download as TXT", st.session_state["current_blog"], "optimized_blog.txt")

        meta_title, meta_desc = extract_meta(st.session_state["current_blog"])
        pdf_bytes = convert_to_pdf(meta_title, meta_desc, st.session_state["current_blog"])
        st.download_button("📄 Download as PDF", pdf_bytes, file_name="optimized_blog.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()
