import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def generate_keywords(seed_keyword):
    """
    Generate keywords using Google Gemini API based on the seed keyword.
    """
    if not GEMINI_API_KEY:
        st.error("⚠️ Gemini API key not found. Please add `GEMINI_API_KEY=your_key` in a .env file.")
        return None

    prompt = f"""
Please ignore all previous instructions. You are a proficient SEO and keyword research expert.
Generate a markdown table of 100 keywords based on the seed keyword "{seed_keyword}".
Include a mix of longtail, LSI, and FAQ keywords.
Columns: Keyword, Search Volume, CPC (USD), Paid Difficulty, SEO Difficulty,Keyword Intent.
Output must be clean and in markdown table format only and also sort the output according to your thinking
that which keyword is the best.
"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Error generating keywords: {str(e)}")
        return None

def parse_response_to_dataframe(response_text):
    try:
        lines = response_text.split('\n')
        table_lines = [line for line in lines if '|' in line and not line.strip().startswith('|---')]
        if not table_lines:
            st.error("❌ Could not find a valid table in the response.")
            return None

        headers = [h.strip() for h in table_lines[0].strip('|').split('|')]
        rows = []
        for line in table_lines[1:]:
            row = [cell.strip() for cell in line.strip('|').split('|')]
            rows.append(row)

        df = pd.DataFrame(rows, columns=headers)
        return df
    except Exception as e:
        st.error(f"Error parsing table: {e}")
        return None

def main():
    st.title("🔎 AI Keyword Explorer (Gemini 2.0 Flash)")
    st.write("Enter a seed keyword below and click 'Generate Keywords' to get SEO-optimized suggestions.")

    seed_keyword = st.text_input("💡 Seed Keyword")

    if st.button("🚀 Generate Keywords") and seed_keyword:
        with st.spinner("Generating keyword suggestions..."):
            response = generate_keywords(seed_keyword)
            if response:
                df = parse_response_to_dataframe(response)
                if df is not None:
                    st.subheader("📊 Keyword Suggestions")
                    st.dataframe(df, use_container_width=True)

                    csv_data = df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"keywords_{seed_keyword.replace(' ', '_')}.csv",
                        mime="text/csv"
                    )

if __name__ == "__main__":
    main()
