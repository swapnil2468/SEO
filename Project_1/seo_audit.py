from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests
import re

def free_seo_audit(url):
    result = {}
    visited_urls = set()
    internal_errors = []

    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        parsed_url = urlparse(url)

        # Basic metadata
        title_tag = soup.find("title")
        desc_tag = soup.find("meta", {"name": "description"})
        result["title"] = title_tag.text.strip() if title_tag else "Missing"
        result["description"] = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else "Missing"

        # Headings
        result["headings"] = {f"H{i}": len(soup.find_all(f"h{i}")) for i in range(1, 4)}

        # Word count
        text = " ".join(soup.stripped_strings)
        result["word_count"] = len(re.findall(r'\b\w+\b', text))

        # HTTPS usage
        result["https"] = url.startswith("https://")

        # Redirection check
        result["was_redirected"] = len(response.history) > 0

        # Schema detection
        result["json_ld_found"] = bool(soup.find_all("script", {"type": "application/ld+json"}))
        result["microdata_found"] = bool(soup.find_all(attrs={"itemscope": True}))

        # Anchor text analysis
        anchor_tags = soup.find_all("a", href=True)
        anchor_texts = [a.get_text(strip=True) for a in anchor_tags if a.get_text(strip=True)]
        anchor_words = sum(len(txt.split()) for txt in anchor_texts)
        result["anchor_word_count"] = anchor_words
        result["anchor_count"] = len(anchor_tags)
        result["anchor_text_ratio"] = round(anchor_words / result["word_count"] * 100, 2) if result["word_count"] else 0
        result["sample_anchors"] = anchor_texts[:10]

        # Text-to-HTML ratio
        html_size = len(response.text)
        text_size = len(text)
        result["text_to_html_ratio_percent"] = round((text_size / html_size) * 100, 2) if html_size else 0

        # robots.txt check
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        try:
            robots_response = requests.get(robots_url, timeout=5)
            disallows = [line.strip() for line in robots_response.text.splitlines() if line.lower().startswith("disallow")]
            result["robots_txt_found"] = True
            result["robots_disallows"] = disallows
        except:
            result["robots_txt_found"] = False
            result["robots_disallows"] = []

        # meta robots tag check
        meta_robots = soup.find("meta", {"name": "robots"})
        result["meta_robots"] = meta_robots["content"] if meta_robots and meta_robots.get("content") else ""

        # Internal 4xx/5xx errors
        base_domain = parsed_url.netloc
        internal_links = set()
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

        result["internal_4xx_5xx_errors"] = internal_errors

    except Exception as e:
        result["error"] = str(e)

    return result