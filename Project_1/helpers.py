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
    prompt = f"""You are an enterprise-level SEO strategist with deep expertise in technical and content SEO, search engine algorithms, site structure, crawl/index behavior, and web performance optimization.
You will be given a multi-page SEO audit report in structured JSON format, covering multiple URLs from the same domain. Each page includes metadata such as title tags, headings, word count, schema presence, HTTP status codes, anchor text info, redirection, and crawl signals like robots.txt and meta robots.

Your task is to:
🔍 Perform a Holistic Site-Wide SEO Analysis
        Do not analyze each page individually. Instead:
            •	Aggregate findings across all URLs
            •	Identify patterns, common errors, and strategic gaps
            •	Highlight specific technical SEO flaws, content weaknesses, and architecture limitations
            •	Prioritize fixes and improvements by their impact on crawlability, indexation, user experience, and ranking potential
    Focus Areas:
        1. On-Page SEO Trends (across all pages)
            •	Are title tags optimized, unique, and keyword-rich?
            •	Are H1 tags repeated, missing, or generic across pages?
            •	Is there evidence of thin content (low word count, low text-to-HTML ratio)?
            •	Are anchor texts varied, descriptive, or overused in headers/navs?
        2. Technical SEO
            •	Any pages returning 4xx or 5xx status codes? What is the impact?
            •	Is HTTPS used consistently?
            •	Are redirects present, excessive, or misconfigured?
            •	Are schema markups present and consistent? Are the right types used (e.g. Article, Service, LocalBusiness)?
            •	Does the robots.txt or meta robots block important content?
            •	Is there excessive anchor text clutter from navigation, footers, or poor internal linking?
        3. Site-Wide SEO Observations
            •	Duplicate H1s or titles across different pages
            •	Pages with very low content depth or HTML bloat
            •	Inconsistent use of schema markup
            •	Errors like /account pages showing 406 or 404
            •	High anchor text ratios on key pages like case studies or careers
            •	Missing meta descriptions (if detectable)
            •	Repeated redirection behavior across multiple URLs
            •	Pages with text-to-HTML ratios that suggest performance problems

Output Format You Must Return

        1. Overall SEO Health Summary
            • Provide a brief, high-level overview of the website's SEO status.
            • Mention what's generally working well (e.g., HTTPS usage, schema presence, strong title tags).
            • Note any recurring issues or systemic weaknesses across multiple pages.
            • This should be readable for non-technical stakeholders.

        2. Detailed SEO Issues (Grouped by Area)
            • Group the findings by SEO category:
                - Technical SEO (errors, redirects, HTTPS, crawl/index flags)
                - Content SEO (word count, missing H1, duplicate titles)
                - Internal Linking & Anchor Usage
                - Structured Data
            • Under each group, list specific issues and clearly mention the affected URLs.
            • For each issue:
                - Describe what the problem is
                - Mention the affected page(s)
                - Explain why this matters for SEO
                - Provide clear context (e.g., “On the /about page, the H1 tag is missing”)

        3. Recommended Fixes
            • For every issue described above, give a recommended fix.
            • Tag each one with: **High**, **Medium**, or **Low** impact.
            • Keep fixes clear and short, but explain the SEO rationale.

        4. Missed Opportunities
            • Suggest improvements across the site like:
                - Thin content pages that could rank if expanded
                - Pages missing meta tags or structured headings
                - Pages without internal links pointing to them
                - Pages lacking or misusing structured data types (e.g., Product, Article, LocalBusiness)
            • Mention affected pages wherever possible.
            • Add any high-level observations like:
                - Orphaned pages
                - Redundant redirects
                - Overuse of footer links
                - Unused canonical tags



Use clear, concise, and professional audit language. Write for a stakeholder or SEO lead who will delegate fixes across dev/content/marketing teams. Focus on insights, clarity, and actionability — not technical jargon.
At the end of your analysis, summarize your findings as a human-readable SEO audit summary.

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
