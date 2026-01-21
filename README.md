# Protocolized Story Search

A fast, client-side search engine for stories from [Protocolized](https://protocolized.summerofprotocols.com), The Magazine of Strange Rules.

**Live Demo:** [View the search interface](http://localhost:8000) (when running locally)

## Features

- **Fast client-side search** - Instant results using FlexSearch
- **Paragraph-level matching** - See exactly where your search terms appear
- **Highlighted results** - Search terms highlighted in yellow
- **Zero cost hosting** - Deploy to GitHub Pages for free
- **Mobile responsive** - Works great on all devices
- **No backend required** - Pure static HTML/CSS/JavaScript

## Quick Start

### View Locally

1. **Start the local server:**
   ```bash
   cd docs
   python3 -m http.server 8000
   ```

2. **Open in your browser:**
   http://localhost:8000

3. **Try searching:**
   - Single words: `protocol`, `rules`, `strange`
   - Phrases: `"strange rules"`, `"summer of protocols"`
   - Any text from the stories

### Update the Search Index

When new stories are published on Protocolized:

1. **Run the scraper:**
   ```bash
   cd scraper
   pip3 install -r requirements.txt  # First time only
   python3 scrape.py
   ```

2. **Review changes:**
   ```bash
   cd ..
   git diff docs/search-index.json
   ```

3. **Commit and push:**
   ```bash
   git add docs/*.json
   git commit -m "Update search index: $(date +%Y-%m-%d)"
   git push
   ```

## Project Structure

```
protocolized-search/
├── scraper/
│   ├── scrape.py              # Python scraper for Substack
│   ├── requirements.txt       # Python dependencies
│   └── README.md             # Scraper documentation
│
├── docs/                      # Static website (GitHub Pages)
│   ├── index.html             # Search interface
│   ├── search-index.json      # Searchable content (236 KB)
│   ├── stories-metadata.json  # Story metadata (4 KB)
│   └── js/
│       └── search.js          # Search logic
│
└── README.md                  # This file
```

## Technology Stack

- **Scraper:** Python 3.9+ with BeautifulSoup4
- **Search:** FlexSearch (7KB, fastest client-side search)
- **Frontend:** Vanilla HTML/CSS/JS with Tailwind CSS
- **Hosting:** GitHub Pages (free)

## Scraper Details

The scraper fetches stories from https://protocolized.summerofprotocols.com/t/stories

**Features:**
- Extracts title, subtitle, author, date, tags
- Parses content into individual paragraphs
- Filters out boilerplate (subscribe CTAs, etc.)
- Rate limited (1 request/second)
- Retry logic for failed requests

**Usage:**
```bash
# Scrape all stories
python3 scrape.py

# Test with 5 stories
python3 scrape.py --limit 5

# Dry run (no file writes)
python3 scrape.py --dry-run
```

**Current Status:**
- ✅ Successfully scraped 15 stories
- ✅ Generated 236 KB search index
- ✅ Generated 4.4 KB metadata file

## Search Features

**Search capabilities:**
- Single word matching
- Multi-word phrase matching
- Case-insensitive search
- Partial word matching (e.g., "prot" matches "protocol")
- Context-aware results

**Performance:**
- Initial load: ~500ms (one-time)
- Search query: 10-20ms (instant)
- Index size: 236 KB (15 stories)

## Deployment to GitHub Pages

### Option 1: Manual Deployment

1. **Create GitHub repository:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Protocolized story search"
   git remote add origin https://github.com/YOUR_USERNAME/protocolized-search.git
   git push -u origin main
   ```

2. **Enable GitHub Pages:**
   - Go to repository Settings → Pages
   - Source: Deploy from branch
   - Branch: `main`
   - Folder: `/docs`
   - Click Save

3. **Wait 1-2 minutes** for deployment

4. **Visit your site:**
   https://YOUR_USERNAME.github.io/protocolized-search/

### Option 2: Automated Updates with GitHub Actions

Create `.github/workflows/update-index.yml`:

```yaml
name: Update Search Index

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:      # Manual trigger

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r scraper/requirements.txt

      - name: Run scraper
        run: |
          cd scraper
          python scrape.py

      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/*.json
          git commit -m "Auto-update search index [skip ci]" || exit 0
          git push
```

## Current Statistics

- **Stories indexed:** 15
- **Total words:** 40,713
- **Total paragraphs:** 917
- **Average words per story:** 2,714
- **Index size:** 236 KB
- **Metadata size:** 4.4 KB

## Known Issues & Notes

1. **Story count:** Currently scraping 15 stories from `/t/stories` tag page. The site may have more stories not tagged as "stories".

2. **Metadata extraction:** Some stories are missing author and date information. This may be due to:
   - Different HTML structure on some pages
   - Missing metadata in original posts
   - Need to update scraper selectors

3. **Future enhancements:**
   - Add filter by author/tags
   - Add sort by date/relevance
   - Add search suggestions
   - Improve metadata extraction
   - Scrape from `/archive` page to get all stories

## Maintenance

**Regular updates:**
- Run scraper when new stories are published
- Update monthly or as needed
- Monitor for changes to Substack HTML structure

**Troubleshooting:**
- If scraper fails: Check Substack page structure, update selectors
- If search is slow: Consider splitting index or reducing content
- If deployment fails: Check GitHub Actions logs

## Cost

**Total: $0/month**

- Hosting: Free (GitHub Pages)
- Domain: Free (.github.io subdomain)
- SSL: Free (automatic)
- Bandwidth: Free (100GB/month)
- All libraries: Free (open source)

## Contributing

To add features or fix issues:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

MIT License - Feel free to use and modify

## Credits

- Stories from [Protocolized](https://protocolized.summerofprotocols.com)
- Part of [Summer of Protocols](https://summerofprotocols.com)
- Search powered by [FlexSearch](https://github.com/nextapps-de/flexsearch)
- Built with ❤️ for finding strange rules

## Support

For issues or questions:
- Check the docs above
- Review the code comments
- Open an issue on GitHub

---

**Happy searching!** 🔍
