#!/usr/bin/env python3
"""
Enhanced Protocolized Story Scraper
Fetches ALL stories from archive with pagination support
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from typing import List, Dict, Optional, Set
import sys


class ProtocolizedScraperEnhanced:
    """Enhanced scraper that fetches all stories from archive"""

    def __init__(self, limit: Optional[int] = None):
        self.base_url = "https://protocolized.summerofprotocols.com"
        self.archive_url = f"{self.base_url}/archive"
        self.limit = limit

        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Protocolized-Search-Bot/1.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def scrape_all(self) -> List[Dict]:
        """Main entry point: scrape all stories from archive"""
        print(f"🔍 Fetching stories from archive: {self.archive_url}...")

        # Get all story URLs from archive (with pagination)
        story_urls = self.get_all_story_urls()

        if not story_urls:
            print("❌ No stories found!")
            return []

        print(f"✅ Found {len(story_urls)} unique stories")

        if self.limit:
            story_urls = list(story_urls)[:self.limit]
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

            # Rate limiting
            if i < len(story_urls):
                time.sleep(1)

        print(f"\n✅ Successfully scraped {len(stories)} stories")

        # Build index files
        self.build_index(stories)

        return stories

    def get_all_story_urls(self) -> Set[str]:
        """Get all story URLs from archive with pagination"""
        all_urls = set()

        # Try multiple approaches to get all stories

        # Approach 1: Archive page
        print("   Trying archive page...")
        urls_from_archive = self._get_urls_from_archive()
        all_urls.update(urls_from_archive)
        print(f"   Found {len(urls_from_archive)} from archive")

        # Approach 2: Stories tag page
        print("   Trying /t/stories tag page...")
        urls_from_tag = self._get_urls_from_tag()
        all_urls.update(urls_from_tag)
        print(f"   Found {len(urls_from_tag)} from tag page")

        # Approach 3: Try sitemap
        print("   Trying sitemap...")
        urls_from_sitemap = self._get_urls_from_sitemap()
        all_urls.update(urls_from_sitemap)
        print(f"   Found {len(urls_from_sitemap)} from sitemap")

        return all_urls

    def _get_urls_from_archive(self) -> Set[str]:
        """Get story URLs from archive page"""
        urls = set()

        try:
            response = self.session.get(self.archive_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all post links
            # Substack archive uses various link structures
            selectors = [
                'a[href*="/p/"]',
                '.post-preview-title a',
                'h3 a[href*="/p/"]',
                '.archive-item a'
            ]

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if '/p/' in href and href not in urls:
                        full_url = self._make_absolute_url(href)
                        urls.add(full_url)

        except Exception as e:
            print(f"      ⚠️  Error fetching archive: {e}")

        return urls

    def _get_urls_from_tag(self) -> Set[str]:
        """Get story URLs from /t/stories tag page"""
        urls = set()

        try:
            tag_url = f"{self.base_url}/t/stories"
            response = self.session.get(tag_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all post links
            selectors = [
                'a[href*="/p/"]',
                '.post-preview-title a'
            ]

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    if '/p/' in href:
                        full_url = self._make_absolute_url(href)
                        urls.add(full_url)

        except Exception as e:
            print(f"      ⚠️  Error fetching tag page: {e}")

        return urls

    def _get_urls_from_sitemap(self) -> Set[str]:
        """Try to get URLs from sitemap.xml"""
        urls = set()

        try:
            sitemap_url = f"{self.base_url}/sitemap.xml"
            response = self.session.get(sitemap_url, timeout=15)

            if response.status_code == 200:
                # Parse XML sitemap
                soup = BeautifulSoup(response.content, 'xml')
                loc_tags = soup.find_all('loc')

                for loc in loc_tags:
                    url = loc.text.strip()
                    if '/p/' in url:
                        urls.add(url)

        except Exception as e:
            print(f"      ⚠️  Sitemap not available: {e}")

        return urls

    def _make_absolute_url(self, href: str) -> str:
        """Convert relative URL to absolute"""
        if href.startswith('http'):
            # Remove query params and fragments
            return href.split('?')[0].split('#')[0]
        else:
            # Make absolute
            full_url = self.base_url + href
            return full_url.split('?')[0].split('#')[0]

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
                content = self._extract_content(soup)

                if not title or not content:
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
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    print(f"   ❌ Failed after {retries} attempts: {e}")
                    return None

        return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract story title"""
        selectors = [
            'h1.post-title',
            'h1[class*="post-title"]',
            'h1.headline',
            'article h1',
            'h1[class*="title"]'
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
            'h2.subtitle',
            '[class*="subtitle"]'
        ]

        for selector in selectors:
            elem = soup.select_one(selector)
            if elem:
                return elem.get_text(strip=True)

        return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract author name(s)"""
        author_elems = soup.select('.author-name, .pencraft-author-name, [class*="author"]')

        authors = []
        for elem in author_elems:
            text = elem.get_text(strip=True)
            if text and text not in authors and len(text) < 100 and 'subscribe' not in text.lower():
                authors.append(text)

        return ", ".join(authors[:3]) if authors else "Unknown"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Extract publication date"""
        time_elem = soup.find('time')
        if time_elem and time_elem.get('datetime'):
            date_str = time_elem['datetime']
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

        return tags[:5]

    def _extract_content(self, soup: BeautifulSoup) -> List[str]:
        """Extract all content paragraphs"""
        article = soup.find('article') or soup.find('div', class_='body') or soup.find('div', class_='post-content')

        if not article:
            article = soup.find('div', class_=re.compile(r'content|body|post', re.I))

        if not article:
            return []

        paragraphs = article.find_all('p')
        content = []

        for p in paragraphs:
            text = p.get_text(separator=' ', strip=True)
            if self._is_valid_paragraph(text):
                content.append(text)

        return content

    def _is_valid_paragraph(self, text: str) -> bool:
        """Check if paragraph is valid content"""
        if len(text) < 20:
            return False

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
            search_index.append({
                'id': i,
                'title': story['title'],
                'subtitle': story['subtitle'],
                'author': story['author'],
                'content': story['content'],
                'tags': story['tags']
            })

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

        # Write files
        index_path = '../docs/search-index.json'
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(search_index, f, separators=(',', ':'), ensure_ascii=False)

        metadata_path = '../docs/stories-metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Calculate sizes
        import os
        index_size = os.path.getsize(index_path) / 1024
        meta_size = os.path.getsize(metadata_path) / 1024

        print(f"✅ Created {index_path} ({index_size:.1f} KB)")
        print(f"✅ Created {metadata_path} ({meta_size:.1f} KB)")

        # Summary
        total_words = sum(m['wordCount'] for m in metadata)
        total_paragraphs = sum(len(s['content']) for s in stories)

        print(f"\n📊 Index Statistics:")
        print(f"   Stories: {len(stories)}")
        print(f"   Total words: {total_words:,}")
        print(f"   Total paragraphs: {total_paragraphs}")
        if len(stories) > 0:
            print(f"   Avg words per story: {total_words // len(stories):,}")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape all Protocolized stories')
    parser.add_argument('--limit', type=int, help='Limit number of stories (for testing)')

    args = parser.parse_args()

    print("🚀 Enhanced Protocolized Story Scraper")
    print("=" * 50)

    scraper = ProtocolizedScraperEnhanced(limit=args.limit)

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
