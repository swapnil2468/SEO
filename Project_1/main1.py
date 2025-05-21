import streamlit as st
from helpers import ai_analysis, display_wrapped_json, full_seo_audit
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests
import time
import re
import pdfkit
from datetime import datetime

# --- PDF HTML Builder ---
def build_html_summary(summary_text: str, site_url: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 12pt; line-height: 1.6; }}
            h1 {{ font-size: 20pt; text-align: center; }}
            h2 {{ font-size: 16pt; margin-top: 20px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <h1>AI SEO Summary Report</h1>
        <p><strong>Website:</strong> {site_url}</p>
        <p><strong>Date:</strong> {date_str}</p>
    """

    lines = summary_text.splitlines()
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html += "</ul>"
                in_list = False
            continue

        if line.startswith("## "):
            if in_list:
                html += "</ul>"
                in_list = False
            html += f"<h2>{line[3:].strip()}</h2>"

        elif line.startswith("* ") or line.startswith("- ") or line.startswith("• "):
            if not in_list:
                html += "<ul>"
                in_list = True
            match = re.match(r"\<b\>(.+?)\</b\>:(.*)", line[2:].strip())  # already converted bold
            if match:
                title = match.group(1).strip()
                rest = match.group(2).strip()
                html += f"<li><b>{title}:</b> {rest}</li>"
            else:
                html += f"<li>{line[2:].strip()}</li>"

        else:
            html += f"<p>{line}</p>"

    if in_list:
        html += "</ul>"

    html += "</body></html>"
    return html

# --- Markdown to HTML Converter ---
def markdown_to_html(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

# --- Convert HTML to PDF using pdfkit ---
def convert_to_pdf(html: str) -> bytes:
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")  # adjust if needed
    return pdfkit.from_string(html, False, configuration=config)

# --- Crawler Logic ---
def crawl_entire_site(start_url):
    visited = set()
    queue = [start_url]
    all_reports = []

    total_to_crawl = 1  # Starts with homepage
    progress_bar = st.progress(0)
    status_text = st.empty()

    while queue:
        current_index = total_to_crawl - len(queue)
        current_url = queue.pop(0)

        if current_url in visited:
            continue

        status_text.text(f"🔍 Auditing {current_url} ({current_index + 1} of {total_to_crawl})")

        try:
            response = requests.get(current_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            visited.add(current_url)

            report = full_seo_audit(current_url)
            all_reports.append({"url": current_url, "report": report})

            base = urlparse(start_url).netloc
            new_links = []

            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(current_url, href)
                if urlparse(full_url).netloc == base and full_url not in visited and full_url not in queue:
                    new_links.append(full_url)

            unique_new_links = [
                    link for link in new_links
                    if link not in visited and link not in queue
                ]

            queue.extend(unique_new_links)
            total_to_crawl += len(unique_new_links)


            progress_bar.progress((current_index + 1) / total_to_crawl)

            time.sleep(0.5)

        except Exception as e:
            all_reports.append({"url": current_url, "error": str(e)})

    status_text.text("✅ Crawl completed!")
    progress_bar.progress(1.0)
    return all_reports
# --- Streamlit UI ---
def main():
    st.title("🕷️ Full-Site AI SEO Auditor")

    start_url = st.text_input("Enter the homepage URL (e.g., https://example.com)")
    st.caption("This will crawl all internal pages and analyze them.")

    if st.button("Start Full Site Audit"):
        if not start_url:
            st.warning("Please enter a valid URL.")
            return  

        if not start_url.startswith("http://") and not start_url.startswith("https://"):
            start_url = "https://" + start_url.strip()

        with st.spinner("Crawling and analyzing site..."):
            full_report = crawl_entire_site(start_url)
            st.session_state["seo_data"] = full_report

        st.success("✅ Crawl complete!")

    if "seo_data" in st.session_state:
        view = st.radio("Choose report view:", ["📊 Raw SEO Report", "🤖 AI SEO Summary"])

        if view == "📊 Raw SEO Report":
            display_wrapped_json(st.session_state["seo_data"])

        elif view == "🤖 AI SEO Summary":
            if "ai_summary" not in st.session_state:
                with st.spinner("Generating summary..."):
                    st.session_state["ai_summary"] = ai_analysis(st.session_state["seo_data"])

            raw_summary = st.session_state["ai_summary"]
            html_friendly = markdown_to_html(raw_summary)
            html = build_html_summary(html_friendly, start_url)

            st.markdown("### 🧠 AI SEO Summary Preview")
            st.markdown(raw_summary)

            pdf_bytes = convert_to_pdf(html)

            st.download_button(
                label="📥 Download SEO Summary as PDF",
                data=pdf_bytes,
                file_name="seo_summary.pdf",
                mime="application/pdf"
            )


if __name__ == "__main__":
    main()
