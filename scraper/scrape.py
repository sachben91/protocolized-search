#!/usr/bin/env python3
"""
Protocolized Story Scraper
Fetches stories from https://protocolized.summerofprotocols.com/t/stories
and builds a searchable JSON index.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Optional
import sys


class ProtocolizedScraper:
    """Scraper for Protocolized Substack stories"""

    def __init__(self, limit: Optional[int] = None):
        self.base_url = "https://protocolized.summerofprotocols.com"
        self.stories_tag_url = f"{self.base_url}/t/stories"
        self.limit = limit  # For testing, limit number of stories

        # Setup session with headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Protocolized-Search-Bot/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def scrape_all(self) -> List[Dict]:
        """Main entry point: scrape all stories and build index"""
        print(f"🔍 Fetching story list from {self.stories_tag_url}...")

        # Get list of story URLs
        story_urls = self.get_story_urls()

        if not story_urls:
            print("❌ No stories found!")
            return []

        print(f"✅ Found {len(story_urls)} stories")

        if self.limit:
            story_urls = story_urls[:self.limit]
            print(f"⚠️  Limiting to {self.limit} stories for testing")

        # Scrape each story
        stories = []
        for i, url in enumerate(story_urls, 1):
            print(f"📖 Scraping {i}/{len(story_urls)}: {url}")

            story_data = self.scrape_story(url)
            if story_data:
                stories.append(story_data)
                print(f"   ✓ Successfully scraped: {story_data['title']}")
            else:
                print(f"   ✗ Failed to scrape")

            # Rate limiting - be respectful
            if i < len(story_urls):
                time.sleep(1)

        print(f"\n✅ Successfully scraped {len(stories)} stories")

        # Build index files
        self.build_index(stories)

        return stories

    def get_story_urls(self) -> List[str]:
        """Fetch all story URLs from the stories tag page"""
        try:
            response = self.session.get(self.stories_tag_url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Approach 1: Try to extract from preloaded JSON in script tags
            # Substack often includes data in window._preloads
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string and '_preloads' in script.string:
                    # Try to extract JSON (simplified approach)
                    # In practice, this would need more robust parsing
                    pass

            # Approach 2: Parse HTML links (more reliable)
            story_urls = []

            # Find all post preview links
            # Substack uses various classes, try multiple selectors
            selectors = [
                'a.post-preview-title',
                'a[href*="/p/"]',
                'h3.post-preview-title a',
                '.post-preview a[href*="/p/"]'
            ]

            links_found = set()
            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if '/p/' in href:
                        # Make absolute URL
                        if href.startswith('http'):
                            full_url = href
                        else:
                            full_url = self.base_url + href

                        # Remove query parameters and fragments
                        full_url = full_url.split('?')[0].split('#')[0]
                        links_found.add(full_url)

            story_urls = sorted(list(links_found))

            return story_urls

        except Exception as e:
            print(f"❌ Error fetching story URLs: {e}")
            return []

    def scrape_story(self, url: str, retries: int = 3) -> Optional[Dict]:
        """Scrape individual story content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract metadata
                title = self._extract_title(soup)
                subtitle = self._extract_subtitle(soup)
                author = self._extract_author(soup)
                date = self._extract_date(soup)
                tags = self._extract_tags(soup)

                # Extract content paragraphs
                content = self._extract_content(soup)

                if not title or not content:
                    print(f"   ⚠️  Missing title or content")
                    return None

                return {
                    'title': title,
                    'subtitle': subtitle,
                    'author': author,
                    'url': url,
                    'date': date,
                    'tags': tags,
                    'content': content
                }

            except Exception as e:
                print(f"   ⚠️  Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(2)  # Wait before retry
                else:
                    print(f"   ❌ Failed after {retries} attempts")
                    return None

        return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract story title"""
        # Try multiple selectors
        selectors = [
            'h1.post-title',
            'h1[class*="post-title"]',
            'h1.headline',
            'article h1'
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        return ""

    def _extract_subtitle(self, soup: BeautifulSoup) -> str:
        """Extract story subtitle"""
        selectors = [
            'h3.subtitle',
            '.subtitle',
            'h2.subtitle'
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author name(s)"""
        # Try multiple selectors
        author_elems = soup.select('.author-name, .pencraft-author-name, [class*="author"]')

        authors = []
        for elem in author_elems:
            text = elem.get_text(strip=True)
            if text and text not in authors and len(text) < 100:
                authors.append(text)

        if authors:
            return ", ".join(authors[:3])  # Max 3 authors

        return "Unknown"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date"""
        # Try <time> tag with datetime attribute
        time_elem = soup.find('time')
        if time_elem and time_elem.get('datetime'):
            date_str = time_elem['datetime']
            # Extract just the date part (YYYY-MM-DD)
            return date_str[:10] if len(date_str) >= 10 else date_str

        return ""

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract story tags"""
        tag_elems = soup.select('.post-tag, [class*="tag"]')

        tags = []
        for elem in tag_elems:
            text = elem.get_text(strip=True)
            if text and text not in tags and len(text) < 50:
                tags.append(text)

        return tags[:5]  # Max 5 tags

    def _extract_content(self, soup: BeautifulSoup) -> List[str]:
        """Extract all content paragraphs"""
        # Find the main article content
        article = soup.find('article') or soup.find('div', class_='body') or soup.find('div', class_='post-content')

        if not article:
            # Fallback: try to find content div
            article = soup.find('div', class_=re.compile(r'content|body|post', re.I))

        if not article:
            return []

        # Extract all paragraphs
        paragraphs = article.find_all('p')

        content = []
        for p in paragraphs:
            # Get text, preserving some structure
            text = p.get_text(separator=' ', strip=True)

            # Filter out non-content paragraphs
            if self._is_valid_paragraph(text):
                content.append(text)

        return content

    def _is_valid_paragraph(self, text: str) -> bool:
        """Check if paragraph is valid content (not boilerplate)"""
        # Must be substantial
        if len(text) < 20:
            return False

        # Filter out common boilerplate
        boilerplate_phrases = [
            'subscribe now',
            'share this post',
            'leave a comment',
            'get 20% off',
            'upgrade to paid',
            'become a subscriber',
            'already a subscriber',
            'sign in',
            'this post is for',
            'give a gift subscription'
        ]

        text_lower = text.lower()
        for phrase in boilerplate_phrases:
            if phrase in text_lower:
                return False

        # Filter out very short "paragraphs"
        word_count = len(text.split())
        if word_count < 5:
            return False

        return True

    def build_index(self, stories: List[Dict]) -> None:
        """Build search index and metadata JSON files"""
        print("\n📝 Building index files...")

        search_index = []
        metadata = []

        for i, story in enumerate(stories):
            # Search index entry (full content for searching)
            search_index.append({
                'id': i,
                'title': story['title'],
                'subtitle': story['subtitle'],
                'author': story['author'],
                'content': story['content'],
                'tags': story['tags']
            })

            # Metadata entry (for display)
            word_count = sum(len(p.split()) for p in story['content'])
            metadata.append({
                'id': i,
                'title': story['title'],
                'subtitle': story['subtitle'],
                'url': story['url'],
                'author': story['author'],
                'date': story['date'],
                'wordCount': word_count,
                'tags': story['tags']
            })

        # Write search index (minified for size)
        index_path = '../docs/search-index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, separators=(',', ':'), ensure_ascii=False)

        # Write metadata (pretty for debugging)
        metadata_path = '../docs/stories-metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Calculate sizes
        import os
        index_size = os.path.getsize(index_path) / 1024  # KB
        meta_size = os.path.getsize(metadata_path) / 1024  # KB

        print(f"✅ Created {index_path} ({index_size:.1f} KB)")
        print(f"✅ Created {metadata_path} ({meta_size:.1f} KB)")

        # Print summary
        total_words = sum(m['wordCount'] for m in metadata)
        total_paragraphs = sum(len(s['content']) for s in stories)

        print(f"\n📊 Index Statistics:")
        print(f"   Stories: {len(stories)}")
        print(f"   Total words: {total_words:,}")
        print(f"   Total paragraphs: {total_paragraphs}")
        print(f"   Avg words per story: {total_words // len(stories):,}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape Protocolized stories')
    parser.add_argument('--limit', type=int, help='Limit number of stories (for testing)')
    parser.add_argument('--dry-run', action='store_true', help='Test without writing files')

    args = parser.parse_args()

    print("🚀 Protocolized Story Scraper")
    print("=" * 50)

    scraper = ProtocolizedScraper(limit=args.limit)

    try:
        stories = scraper.scrape_all()

        if stories:
            print(f"\n✅ Success! Scraped {len(stories)} stories")
            print(f"📁 Index files created in ../docs/")
        else:
            print("\n❌ No stories were scraped")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
