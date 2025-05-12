import streamlit as st
import os
import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Set Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Session state setup
if "current_blog" not in st.session_state:
    st.session_state["current_blog"] = ""
if "keyword_data" not in st.session_state:
    st.session_state["keyword_data"] = ""
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""

def generate_initial_blog(topic_input, keyword_data):
    prompt = f"""
Ignore all previous instructions.

You are an expert-level SEO strategist and conversion-focused blog writer. You write content that consistently ranks #1 on Google and drives high-quality traffic. You use Google's E-E-A-T principles (Experience, Expertise, Authoritativeness, Trustworthiness) and follow all on-page SEO best practices.

Your task is to write a comprehensive, long-form, 100% unique, SEO-optimized blog post on the topic provided by the user. If keyword data is provided, use those keywords naturally and strategically throughout the post.

Write in a friendly, informative tone. Use clear formatting for readability, such as short paragraphs, simple bullet points, and clear sections. Do **not** use any Markdown, HTML, or special formatting like headings, bold, or italics.
Blogs are to be written for brands with ADVANCE & PREMIUM plans. LSI, NLPs, trending & popular phrases etc. are good to be included in the articles. Also relevant & accurate FAQs are important.
Ensure the blog includes:
- A strong title
- SEO Meta Title (≤ 60 characters)
- SEO Meta Description (≤ 155 characters)
- Meta Keywords (comma-separated)
- Introduction with a hook
- Main content broken into sections
- Usage of long-tail and LSI keywords
- Answers to frequently asked questions (if relevant)
- A compelling conclusion with CTA
==> User Input Topic / Notes:
{topic_input}

==> Keywords:
{keyword_data}
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def refine_blog(current_blog, user_instruction):
    prompt = f"""
You previously wrote the following blog content:

---BLOG---
{current_blog}
---END BLOG---

Now revise it based on this instruction:
"{user_instruction}"

Output the full updated blog only.
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text

def main():
    st.title("✍️ AI Blog Writer with Live Edits")
    st.write("Generate a full SEO blog, then iteratively refine it using your feedback!")

    uploaded_file = st.file_uploader("📂 Upload Keyword CSV (optional)", type=["csv"])
    topic_input = st.text_area("💡 Enter Blog Topic or Brief")

    if st.button("🚀 Generate Blog") and topic_input.strip():
        # Parse CSV if available
        keyword_data = ""
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                keyword_data = "\n".join([' | '.join([str(val) for val in row]) for _, row in df.iterrows()])
            except Exception as e:
                st.error(f"Failed to read file: {e}")
                return

        # Save to session
        st.session_state["keyword_data"] = keyword_data
        st.session_state["topic_input"] = topic_input

        with st.spinner("Generating SEO blog..."):
            blog = generate_initial_blog(topic_input, keyword_data)
            st.session_state["current_blog"] = blog

    # Show current blog and editing options only if the blog is generated
    if st.session_state["current_blog"] and st.session_state["current_blog"] != "":
        st.subheader("📄 Current Blog Output")
        
        # Display the original blog output in Markdown format with specific title and subtitle highlighting
        st.markdown(f"### **Blog Title**\n\n{st.session_state['current_blog']}", unsafe_allow_html=True)

        # Download as TXT
        st.download_button("📥 Download Blog as TXT", st.session_state["current_blog"], "seo_blog_post.txt", "text/plain")

        # Download as Markdown
        st.download_button("📥 Download Blog as Markdown", f"# Blog Title\n\n{st.session_state['current_blog']}", "seo_blog_post.md", "text/markdown")

        # Edit input
        refine_input = st.text_area("✏️ Suggest a change (e.g., 'Make it shorter', 'Add FAQs')")
        if st.button("🔁 Apply Edit") and refine_input.strip():
            with st.spinner("Applying changes..."):
                updated_blog = refine_blog(st.session_state["current_blog"], refine_input)
                st.session_state["current_blog"] = updated_blog  # Replace with new version

            # Display the updated blog output in Markdown format with specific title and subtitle highlighting
            st.markdown(f"### **Updated Blog Title**\n\n{st.session_state['current_blog']}", unsafe_allow_html=True)
            st.rerun()  # Refresh to show updated content

if __name__ == "__main__":
    main()
