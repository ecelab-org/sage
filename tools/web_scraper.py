"""
Web scraping tool for the Sage assistant.
Provides functionality to extract content from websites.
"""

import json
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
)

import requests
from bs4 import (
    BeautifulSoup,
    Tag,
)


def scrape_website(input_data: Dict[str, Any]) -> Tuple[str, Optional[Exception]]:
    """
    Scrape content from a website.

    Args:
        input_data: Dictionary containing:
            - url: The URL to scrape
            - params: Optional parameters including:
                - selector: CSS selector to target specific elements
                - extract: What to extract ('text', 'html', 'links', etc.)
                - timeout: Request timeout in seconds

    Returns:
        Tuple of (result_content, exception)
    """
    # ----- Parameter Extraction -----
    # Extract URL from input data with empty string fallback
    url = input_data.get("url", "")
    # Extract optional parameters, defaulting to empty dict if not provided
    params = input_data.get("params", {})

    # ----- Parameter Processing -----
    # CSS selector for targeting specific elements (defaults to body)
    selector = params.get("selector", "body")
    # Type of content to extract (defaults to text)
    extract_type = params.get("extract", "text")
    # Request timeout in seconds (defaults to 10s)
    timeout = params.get("timeout", 10)

    try:
        # ----- Request Preparation -----
        # Add user-agent to avoid being blocked by some websites
        # Many sites block requests without proper user agents
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        # ----- Input Validation -----
        # Ensure URL has proper protocol
        if not url.startswith(("http://", "https://")):
            return "Invalid URL format. URL must start with http:// or https://", None
        # Check if URL was provided
        if not url:
            return "URL is required", None

        # ----- HTTP Request -----
        # Create a session to maintain cookies
        session = requests.Session()
        session.headers.update(headers)
        # Add more browser-like headers
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        # Make GET request with explicit redirect following
        response = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        # Raise exception for HTTP errors (4xx, 5xx)
        response.raise_for_status()

        # ----- Content Type Validation -----
        # Ensure we're dealing with HTML content
        if "text/html" not in response.headers.get("Content-Type", ""):
            return "The URL does not return HTML content", None

        # Parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # ----- Element Selection Logic -----
        # Handle the case where the selector is not found
        if selector != "body":
            # Use CSS selector to find matching elements
            elements = list(soup.select(selector))
            if not elements:
                # Return error if no elements match the provided selector
                return f"No elements found matching selector: {selector}", None
        else:
            # Default: use body element or entire document if body doesn't exist
            elements = [soup.body] if soup.body else [soup]

        # ----- Content Extraction Logic -----
        if extract_type == "text":
            # Extract plain text from elements, joining with double newlines
            # The separator=" " ensures spaces between inline elements
            result = "\n\n".join([el.get_text(separator=" ", strip=True) for el in elements])
        elif extract_type == "html":
            # Extract raw HTML markup for each element
            result = "\n\n".join([str(el) for el in elements])
        elif extract_type == "links":
            # Extract all hyperlinks from the selected elements
            links = []
            for el in elements:
                # Find all anchor tags with href attributes
                for link in el.find_all("a", href=True):
                    if isinstance(link, Tag):
                        links.append(
                            {
                                "text": link.get_text(strip=True),  # Link text
                                "href": link.get("href", ""),  # Link URL
                            }
                        )
            # Convert links to JSON format
            result = json.dumps(links, indent=2)
        else:
            # Handle unsupported extraction types
            return f"Unsupported extraction type: {extract_type}", None

        # ----- Result Size Management -----
        # Truncate result if it's too large to prevent memory issues
        # and ensure reasonable response sizes
        if len(result) > 20000:
            result = result[:20000] + "... [content truncated due to size]"

        return result, None

    except requests.exceptions.RequestException as e:
        return "", Exception(f"Request failed: {str(e)}")
    except Exception as e:  # pylint: disable=broad-except
        return "", Exception(f"Error scraping website: {str(e)}")
