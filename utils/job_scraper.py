"""Job description scraper utility."""
import requests
from bs4 import BeautifulSoup
from typing import Optional


class JobScraper:
    """Scrapes job descriptions from URLs."""

    @staticmethod
    def fetch_job_description(url: str) -> str:
        """
        Fetch job description from a URL.

        Args:
            url: The job posting URL

        Returns:
            Extracted job description text

        Raises:
            Exception: If fetching or parsing fails
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)

            if not text:
                raise ValueError("No text content found at URL")

            return text

        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing job description: {str(e)}")

    @staticmethod
    def extract_key_sections(job_text: str) -> dict:
        """
        Extract key sections from job description.

        Args:
            job_text: Full job description text

        Returns:
            Dictionary with extracted sections
        """
        # Basic extraction - can be enhanced with NLP
        sections = {
            "full_text": job_text,
            "length": len(job_text)
        }
        return sections
