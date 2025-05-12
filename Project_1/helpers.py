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
    prompt = f"""You are an expert in technical and content-based SEO with deep knowledge of search 
    engine algorithms, ranking factors, and web performance metrics. I will provide you with a 
    [SEO_REPORT], and your task is to analyze it thoroughly and return a comprehensive evaluation. 
    Your response should include detailed insights across all aspects of SEO including on-page 
    elements like title tags, meta  descriptions, headings, keyword usage, and content relevance; 
    technical factors such as site speed, mobile-friendliness, crawlability, indexing status, and 
    Core Web Vitals; off-page signals like backlink quality and domain authority; as well as content 
    structure, topical depth, freshness, and user engagement metrics such as bounce rate and dwell time,
    if available. For each observation, provide an in-depth explanation of what is working well and why,
    what is underperforming or incorrect, and offer clear reasoning on how these issues may be affecting 
    the site's SEO performance or visibility. Every problem identified should be accompanied by a precise 
    recommendation on how to fix or improve it, along with the underlying SEO rationale. At the end of 
    your analysis, summarize all the recommended optimizations in a prioritized list, categorizing them 
    into high, medium, or low impact based on their potential effect on rankings. Additionally, offer any 
    missed opportunities the report may have overlooked, such as untapped content areas, structured data 
    implementation, or relevant tools that could assist in resolving issues or enhancing monitoring. 
    Present your response in well-structured, readable markdown paragraphs suitable for implementation 
    or reporting.

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
