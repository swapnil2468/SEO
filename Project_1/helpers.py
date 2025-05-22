from typing import List
from urllib.parse import urlparse, urljoin
from SimplerLLM.language.llm import LLM, LLMProvider
from bs4 import BeautifulSoup
import requests
from textwrap import wrap
import json
import streamlit as st
import os
from dotenv import load_dotenv
import re
import time
from playwright.sync_api import sync_playwright
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


load_dotenv()
llm_instance = LLM.create(
    provider=LLMProvider.GEMINI,
    model_name="models/gemini-2.0-flash",  
    api_key=os.getenv("GEMINI_API_KEY")
)

def display_wrapped_json(data, width=80):
    def wrap_str(s):
        return '\n'.join(wrap(s, width=width))
    def process_item(item):
        if isinstance(item, dict):
            return {k: process_item(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [process_item(i) for i in item]
        elif isinstance(item, str):
            return wrap_str(item)
        else:
            return item
    wrapped_data = process_item(data)
    st.code(json.dumps(wrapped_data, indent=2), language='json')

def get_rendered_html(url):
    try:
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = uc.Chrome(options=options)

        print(f"🔍 Opening: {url}")
        driver.get(url)
        driver.implicitly_wait(8)  # wait for JS to render
        html = driver.page_source
        driver.quit()
        return html
    except Exception as e:
        print(f"❌ UC Error fetching {url}: {e}")
        return None


def extract_internal_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    internal_links = set()
    domain = urlparse(base_url).netloc
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("/") or domain in href:
            full_url = urljoin(base_url, href)
            internal_links.add(full_url.split("#")[0])
    return list(internal_links)

def full_seo_audit(url):
    result = {}
    visited_urls = set()
    internal_errors = []

    try:
        html = get_rendered_html(url)
        if not html:
            result["error"] = f"Could not render page: {url}"
            return result

        soup = BeautifulSoup(html, "html.parser")
        parsed_url = urlparse(url)

        title_tag = soup.find("title")
        desc_tag = soup.find("meta", {"name": "description"})
        result["title"] = {
            "text": title_tag.text.strip() if title_tag else "Missing",
            "length": len(title_tag.text.strip()) if title_tag else 0,
            "word_count": len(title_tag.text.strip().split()) if title_tag else 0,
        }
        result["description"] = {
            "text": desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else "Missing",
            "length": len(desc_tag["content"].strip()) if desc_tag and desc_tag.get("content") else 0,
            "word_count": len(desc_tag["content"].strip().split()) if desc_tag and desc_tag.get("content") else 0,
        }

        result["headings"] = {f"H{i}": len(soup.find_all(f"h{i}")) for i in range(1, 7)}
        result["H1_content"] = soup.find("h1").text.strip() if soup.find("h1") else ""

        text = " ".join(soup.stripped_strings)
        total_words = len(re.findall(r'\b\w+\b', text))
        anchor_tags = soup.find_all("a", href=True)
        anchor_texts = [a.get_text(strip=True) for a in anchor_tags if a.get_text(strip=True)]
        anchor_words = sum(len(a.split()) for a in anchor_texts)

        result["word_stats"] = {
            "total_words": total_words,
            "anchor_words": anchor_words,
            "anchor_ratio_percent": round((anchor_words / total_words) * 100, 2) if total_words else 0,
            "sample_anchors": anchor_texts[:10]
        }

        result["https_info"] = {
            "using_https": url.startswith("https://"),
            "was_redirected": False  # requests not used here
        }

        html_size = len(html)
        result["text_to_html_ratio_percent"] = round((len(text) / html_size) * 100, 2) if html_size else 0

        result["schema"] = {
            "json_ld_found": bool(soup.find_all("script", {"type": "application/ld+json"})),
            "microdata_found": bool(soup.find_all(attrs={"itemscope": True}))
        }

        images = soup.find_all("img")
        result["images"] = {
            "total_images": len(images),
            "images_without_alt": sum(1 for img in images if not img.get("alt")),
            "sample_images": [{"src": img.get("src"), "alt": img.get("alt")} for img in images[:5]]
        }

        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        try:
            robots_response = requests.get(robots_url, timeout=5)
            disallows = [line.strip() for line in robots_response.text.splitlines() if line.lower().startswith("disallow")]
            result["robots_txt"] = {
                "found": True,
                "disallows": disallows
            }
        except:
            result["robots_txt"] = {
                "found": False,
                "disallows": []
            }

        meta_robots = soup.find("meta", {"name": "robots"})
        result["meta_robots"] = meta_robots["content"] if meta_robots and meta_robots.get("content") else ""

        base_domain = parsed_url.netloc
        for a in anchor_tags:
            href = a["href"]
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == base_domain and full_url not in visited_urls:
                visited_urls.add(full_url)
                try:
                    head_resp = requests.head(full_url, allow_redirects=True, timeout=5)
                    if head_resp.status_code >= 400:
                        internal_errors.append({"url": full_url, "status": head_resp.status_code})
                except Exception as e:
                    internal_errors.append({"url": full_url, "error": str(e)})

        result["internal_link_errors"] = internal_errors

    except Exception as e:
        result["error"] = str(e)

    return result
def ai_analysis(report):
    prompt = f"""You are an advanced SEO and web performance analyst. I am providing a JSON-formatted audit report of a website. This JSON includes data for individual URLs covering:
        •	HTTP/HTTPS status and response codes (including 4xx and 5xx errors)
        •	Page speed and response time
        •	Metadata (title, description, length, duplication)
        •	Content elements (word count, heading structure, text-to-HTML ratio)
        •	Link data (internal/external links, anchor text quality, redirects)
        •	Image data (alt tag presence)
        •	Schema markup presence
        •	Indexing and crawling restrictions (robots.txt, meta robots)

    IMPORTANT  :- DO NOT SKIP ANY DATA FROM THE JSON REPORT PARSE THE FULL REPORT DO NOT LEAVE ANYTHING 
    do not make any table and dont add impact
    Based on this JSON data:
        1. Overall Health Summary
        Provide a concise summary of the site’s overall technical SEO health and performance.
        2. Strengths
        Highlight current SEO and technical strengths (e.g. fast loading pages, clean heading structure, strong HTTPS coverage, good schema usage).
        3. Issues to Fix
        Identify and explain:
            •	Pages with missing or duplicate meta tags
            •	Thin content (low word count)
            •	Improper use of H1/H2 tags
            •	Images missing alt text
            •	Improper anchor text usage
            •	3xx/4xx/5xx pages and their impact
            •	Redirection chains or loops
            •	Pages blocked from crawling or indexing
            •	Poor text-to-HTML ratio
            •	Pages missing schema markup
        4. Critical Page-Level Errors
        List top problematic URLs with specific issues (e.g., 500 errors, duplicate titles, noindex tag, redirect chains).
        5. Actionable Recommendations
        Provide clear, prioritized, and actionable steps to improve:
            •	SEO performance
            •	Technical stability
            •	User experience
            •	Crawlability and indexing
        Format the output in well-structured sections, using bullet points and bold emphasis where helpful.

 Important:
- Do NOT return your output as JSON.
- Do NOT use triple backticks or code blocks.
- DO write clear paragraphs, headings, and bullet points suitable for a presentation or client report.

[SEO_REPORT]: {report}
"""

    api_key = os.getenv("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"❌ Error during Gemini API call: {e}\n\nDetails: {response.text}"
