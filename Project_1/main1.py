import streamlit as st
from helpers import ai_analysis, display_wrapped_json, free_seo_audit
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests
import time

def crawl_entire_site(start_url):
    visited = set()
    queue = [start_url]
    all_reports = []

    while queue:
        current_url = queue.pop(0)
        if current_url in visited:
            continue

        try:
            response = requests.get(current_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            visited.add(current_url)

            report = free_seo_audit(current_url)
            all_reports.append({"url": current_url, "report": report})

            base = urlparse(start_url).netloc
            for a in soup.find_all("a", href=True):
                href = a["href"]
                full_url = urljoin(current_url, href)
                if urlparse(full_url).netloc == base and full_url not in visited and full_url not in queue:
                    queue.append(full_url)

            time.sleep(0.5)
        except Exception as e:
            all_reports.append({"url": current_url, "error": str(e)})

    return all_reports

def main():
    st.title("🕷️ Full-Site AI SEO Auditor")

    start_url = st.text_input("Enter the homepage URL of the website (e.g., https://example.com)")
    st.caption("🔁 This will crawl all internal pages with no depth or page limit.")

    if st.button("Start Full Site Audit"):
        if not start_url:
            st.warning("Please enter a valid URL.")
            return

        if not start_url.startswith("http://") and not start_url.startswith("https://"):
            start_url = "https://" + start_url.strip()

        st.info("Crawling full site and analyzing SEO. Please wait...")
        with st.spinner("Auditing site..."):
            full_report = crawl_entire_site(start_url)
            st.session_state["seo_data"] = full_report  # 🔐 Store result

        st.success("✅ Audit Complete!")

    if "seo_data" in st.session_state:
        view = st.radio("Choose report view:", ["📊 Raw SEO Report", "🤖 AI SEO Summary"])

        if view == "📊 Raw SEO Report":
            display_wrapped_json(st.session_state["seo_data"])

        elif view == "🤖 AI SEO Summary":
            with st.spinner("Generating AI insights..."):
                ai_result = ai_analysis(st.session_state["seo_data"])
                st.write(ai_result)

if __name__ == "__main__":
    main()
