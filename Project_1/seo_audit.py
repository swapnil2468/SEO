from urllib.parse import urlparse
from bs4 import BeautifulSoup
import re
import traceback
import logging

# Set up logging
logger = logging.getLogger(__name__)

def fetch_url_content(url):
    import requests
    return requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

def get_http_info(response):
    return {
        "status": response.status_code,
        "using_https": response.url.startswith("https://"),
        "response_time": f"{response.elapsed.total_seconds():.2f} seconds",
    }

def full_seo_audit(url):
    audit_result = {}

    # Fetch content
    try:
        response = fetch_url_content(url)

        final_url = response.url  # Final URL after all redirects
        using_https = final_url.startswith("https://")

        # Determine input type (Domain or URL with path)
        parsed_url = urlparse(url)
        input_type = "Domain" if parsed_url.path.strip("/") == "" else "URL with path"

        audit_result["Input"] = {
            "URL": url,
            "Input type": input_type,
        }

        # HTTP section
        audit_result["http"] = get_http_info(response)

        soup = BeautifulSoup(response.content, "html.parser")
        title_tag = soup.find("title")
        title_data = title_tag.string if title_tag else ""
        title_length = len(title_data)
        title_tag_number = len(soup.find_all("title"))

        audit_result["title"] = {
            "found": "Found" if title_tag else "Not found",
            "data": title_data,
            "length": title_length,
            "characters": len(title_tag.string) if title_tag else 0,
            "words": len(title_tag.string.split()) if title_tag else 0,
            "charPerWord": round(
                len(title_tag.string) / len(title_tag.string.split()), 2
            ) if title_tag and title_tag.string and len(title_tag.string.split()) > 0 else 0,
            "tag number": title_tag_number,
        }

        description_tag = soup.find("meta", {"name": "description"})
        description_data = description_tag["content"] if description_tag else ""
        description_length = len(description_data)
        meta_description_number = len(soup.find_all("meta", {"name": "description"}))

        audit_result["meta_description"] = {
            "found": "Found" if description_tag else "Not found",
            "data": description_data,
            "length": description_length,
            "characters": len(description_tag["content"]) if description_tag else 0,
            "words": len(description_tag["content"].split()) if description_tag else 0,
            "charPerWord": round(
                len(description_tag["content"])
                / len(description_tag["content"].split()),
                2,
            ) if description_tag and description_tag.get("content") and len(description_tag["content"].split()) > 0 else 0,
            "number": meta_description_number,
        }

        metadata_info = {}
        charset_tag = soup.find("meta", {"charset": True})
        metadata_info["charset"] = charset_tag["charset"] if charset_tag else None

        canonical_tag = soup.find("link", {"rel": "canonical"})
        metadata_info["canonical"] = canonical_tag["href"] if canonical_tag else None

        favicon_tag = soup.find("link", {"rel": "icon"}) or soup.find(
            "link", {"rel": "shortcut icon"}
        )
        metadata_info["favicon"] = favicon_tag["href"] if favicon_tag else None

        viewport_tag = soup.find("meta", {"name": "viewport"})
        metadata_info["viewport"] = viewport_tag["content"] if viewport_tag else None

        keywords_tag = soup.find("meta", {"name": "keywords"})
        metadata_info["keywords"] = keywords_tag["content"] if keywords_tag else None

        locale_tag = soup.find("meta", {"property": "og:locale"})
        metadata_info["locale"] = locale_tag["content"] if locale_tag else None

        content_type_tag = soup.find("meta", {"property": "og:type"})
        metadata_info["contentType"] = (
            content_type_tag["content"] if content_type_tag else None
        )

        site_name_tag = soup.find("meta", {"property": "og:site_name"})
        metadata_info["site_name"] = site_name_tag["content"] if site_name_tag else None

        site_image_tag = soup.find("meta", {"property": "og:image"})
        metadata_info["site_image"] = (
            site_image_tag["content"] if site_image_tag else None
        )

        robots_tag = soup.find("meta", {"name": "robots"})
        metadata_info["robots"] = robots_tag["content"] if robots_tag else None

        hreflangs = []
        hreflang_tags = soup.find_all("link", {"rel": "alternate", "hreflang": True})
        for tag in hreflang_tags:
            hreflangs.append({"language": tag["hreflang"], "url": tag["href"]})

        metadata_info["hreflangs"] = hreflangs

        audit_result["metadata_info"] = metadata_info

        # Calculate headings count
        headings = {"H1": 0, "H2": 0, "H3": 0, "H4": 0, "H5": 0, "H6": 0}
        for key in headings:
            headings[key] = len(soup.find_all(key.lower()))

        h1_content = soup.find("h1").text if soup.find("h1") else ""

        audit_result["Page Headings summary"] = {
            **headings,
            "H1 count": len(soup.find_all("h1")),
            "H1 Content": h1_content,
        }

        # Word count section
        # Extract textual content from the soup object
        text_content = " ".join(list(soup.stripped_strings))

        # Convert the text content to lowercase and then split into words using regex
        words = re.findall(r"\b\w+\b", text_content.lower())

        # Count the total words
        word_count_total = len(words)

        # Calculate anchor_text_words and anchor_percentage
        anchor_elements = soup.find_all("a")
        anchor_text = " ".join(a.text for a in anchor_elements if a.text.strip())
        anchor_text_words = len(anchor_text.split())
        anchor_percentage = round((anchor_text_words / word_count_total) * 100, 2) if word_count_total > 0 else 0

        audit_result["word_count"] = {
            "total": word_count_total,
            "Corrected word count": word_count_total,
            "Anchor text words": anchor_text_words,
            "Anchor Percentage": anchor_percentage,
        }

        # On page links summary
        total_links = len(soup.find_all("a"))
        external_links = sum(
            1 for link in soup.find_all("a") if link.get("href", "").startswith("http")
        )
        internal_links = total_links - external_links
        nofollow_count = sum(
            1 for link in soup.find_all("a") if "nofollow" in link.get("rel", [])
        )

        links = [
            {"href": link["href"], "text": link.text.strip()}
            for link in soup.find_all("a")
            if link.get("href")
        ]

        audit_result["links_summary"] = {
            "Total links": total_links,
            "External links": external_links,
            "Internal": internal_links,
            "Nofollow count": nofollow_count,
            "links": links,
        }

        # Image analysis
        images = soup.find_all("img")

        number_of_images = len(images)

        image_data = [
            {"src": img.get("src", ""), "alt": img.get("alt", "")} for img in images
        ]

        audit_result["images_analysis"] = {
            "summary": {
                "total": number_of_images,
                "No src tag": sum(1 for img in images if not img.get("src")),
                "No alt tag": sum(1 for img in images if not img.get("alt")),
            },
            "data": image_data,
        }
    except Exception as ex:
        logger.error(f"error in basic_seo_audit: {str(ex)}\nStack trace: {traceback.format_exc()}")
        return {"error": str(ex)}

    return audit_result