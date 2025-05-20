from typing import List
from urllib.parse import urlparse
from SimplerLLM.language.llm import LLM, LLMProvider
from bs4 import BeautifulSoup
import requests
from textwrap import wrap
import json
import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
llm_instance = LLM.create(
    provider=LLMProvider.GEMINI,
    model_name="models/gemini-2.0-flash",  # This is the correct model name for Gemini
    api_key=os.getenv("GEMINI_API_KEY")  # This assumes your .env has GEMINI_API_KEY
)

def display_wrapped_json(data, width=80):
    """
    Display JSON data with text wrapping for improved readability.
    """
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

def free_seo_audit(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Basic HTTP info
        audit_result = {
            "http": {
                "status": response.status_code,
                "using_https": url.startswith("https://"),
                "response_time": f"{response.elapsed.total_seconds():.2f} seconds",
            }
        }

        # Metadata
        title_tag = soup.find("title")
        description_tag = soup.find("meta", {"name": "description"})
        audit_result["metadata"] = {
            "title": title_tag.string if title_tag else None,
            "title_length": len(title_tag.string) if title_tag else 0,
            "description": description_tag["content"] if description_tag else None,
            "description_length": len(description_tag["content"]) if description_tag else 0,
        }

        # Basic content analysis
        text_content = " ".join(soup.stripped_strings)
        headings = soup.find_all(["h1", "h2", "h3"])
        audit_result["content"] = {
            "word_count": len(text_content.split()),
            "h1_count": len([h for h in headings if h.name == "h1"]),
            "h2_count": len([h for h in headings if h.name == "h2"]),
            "h3_count": len([h for h in headings if h.name == "h3"]),
        }

        # Basic link analysis
        links = soup.find_all("a")
        internal_links = [link.get("href") for link in links if urlparse(link.get("href", "")).netloc == ""]
        external_links = [link.get("href") for link in links if urlparse(link.get("href", "")).netloc != ""]
        audit_result["links"] = {
            "total_links": len(links),
            "internal_links": len(internal_links),
            "external_links": len(external_links),
        }

        # Basic image analysis
        images = soup.find_all("img")
        audit_result["images"] = {
            "total_images": len(images),
            "images_without_alt": sum(1 for img in images if not img.get("alt")),
        }

        return audit_result
    except Exception as ex:
        return {"error": str(ex)}

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
