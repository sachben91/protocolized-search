/**
 * Protocolized Story Search
 * Client-side search using FlexSearch
 */

// Global state
let searchIndex = null;
let documentsData = [];
let metadataMap = {};
let isReady = false;

// DOM elements
const loadingDiv = document.getElementById('loading');
const searchInterface = document.getElementById('search-interface');
const errorDiv = document.getElementById('error');
const searchInput = document.getElementById('search-input');
const resultsCount = document.getElementById('results-count');
const resultsContainer = document.getElementById('results');
const noResultsDiv = document.getElementById('no-results');

// Debounce timer
let searchTimeout = null;

/**
 * Initialize search on page load
 */
async function initSearch() {
    try {
        console.log('Loading search index...');

        // Load both JSON files in parallel
        const [indexData, metaData] = await Promise.all([
            fetch('search-index.json').then(r => {
                if (!r.ok) throw new Error(`Failed to load search index: ${r.status}`);
                return r.json();
            }),
            fetch('stories-metadata.json').then(r => {
                if (!r.ok) throw new Error(`Failed to load metadata: ${r.status}`);
                return r.json();
            })
        ]);

        console.log(`Loaded ${indexData.length} stories`);

        // Store data
        documentsData = indexData;

        // Create metadata map for quick lookup
        metaData.forEach(item => {
            metadataMap[item.id] = item;
        });

        // Initialize FlexSearch
        searchIndex = new FlexSearch.Document({
            document: {
                id: 'id',
                index: ['title', 'subtitle', 'author', 'content'],
                store: ['id', 'title', 'author']
            },
            tokenize: 'forward',
            context: {
                resolution: 9,
                depth: 3,
                bidirectional: true
            },
            cache: true
        });

        // Add all documents to index
        documentsData.forEach(doc => {
            // Flatten content array for indexing
            const docForIndex = {
                ...doc,
                content: doc.content.join(' ')  // FlexSearch needs string, not array
            };
            searchIndex.add(docForIndex);
        });

        console.log('Search index ready');

        // Show search interface
        loadingDiv.classList.add('hidden');
        searchInterface.classList.remove('hidden');
        isReady = true;

        // Focus search input
        searchInput.focus();

        // Setup event listeners
        searchInput.addEventListener('input', handleSearchInput);
        searchInput.addEventListener('keydown', handleKeyboard);

    } catch (error) {
        console.error('Failed to initialize search:', error);
        loadingDiv.classList.add('hidden');
        errorDiv.classList.remove('hidden');
    }
}

/**
 * Handle search input with debouncing
 */
function handleSearchInput(event) {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(() => {
        const query = event.target.value.trim();
        performSearch(query);
    }, 300); // 300ms debounce
}

/**
 * Handle keyboard shortcuts
 */
function handleKeyboard(event) {
    // Escape key clears search
    if (event.key === 'Escape') {
        searchInput.value = '';
        performSearch('');
    }
}

/**
 * Perform search and display results
 */
function performSearch(query) {
    if (!isReady) return;

    // Clear previous results
    resultsContainer.innerHTML = '';
    noResultsDiv.classList.add('hidden');

    // Empty query - show nothing
    if (!query) {
        resultsCount.textContent = '';
        return;
    }

    try {
        // Search using FlexSearch
        const searchResults = searchIndex.search(query, {
            limit: 100,
            enrich: true
        });

        console.log('Search results:', searchResults);

        // Extract and process matches
        const matches = extractMatches(searchResults, query);

        // Display results
        displayResults(matches, query);

    } catch (error) {
        console.error('Search error:', error);
        resultsCount.textContent = 'Search error occurred';
    }
}

/**
 * Extract matching paragraphs from search results
 */
function extractMatches(searchResults, query) {
    const matches = [];
    const queryLower = query.toLowerCase();

    // FlexSearch returns array of field results
    // Each field has array of results with doc and result
    const processedIds = new Set();

    searchResults.forEach(fieldResult => {
        if (!fieldResult.result) return;

        fieldResult.result.forEach(result => {
            const docId = result.id;

            // Skip if already processed this document
            if (processedIds.has(docId)) return;
            processedIds.add(docId);

            const doc = documentsData[docId];
            const meta = metadataMap[docId];

            if (!doc || !meta) return;

            // Find paragraphs containing the query
            const matchingParagraphs = [];

            doc.content.forEach((paragraph, idx) => {
                if (paragraph.toLowerCase().includes(queryLower)) {
                    matchingParagraphs.push({
                        text: paragraph,
                        index: idx
                    });
                }
            });

            // If no exact matches in content, still show the story (matched in title/author)
            if (matchingParagraphs.length === 0) {
                // Use first paragraph as snippet
                if (doc.content.length > 0) {
                    matchingParagraphs.push({
                        text: doc.content[0],
                        index: 0
                    });
                }
            }

            // Add each matching paragraph as a separate result
            matchingParagraphs.slice(0, 3).forEach(para => {  // Max 3 paragraphs per story
                matches.push({
                    id: docId,
                    title: meta.title,
                    subtitle: meta.subtitle,
                    url: meta.url,
                    author: meta.author,
                    date: meta.date,
                    snippet: para.text,
                    paragraphIndex: para.index
                });
            });
        });
    });

    return matches;
}

/**
 * Display search results
 */
function displayResults(matches, query) {
    // Update count
    const uniqueStories = new Set(matches.map(m => m.id)).size;
    const pluralMatches = matches.length === 1 ? 'match' : 'matches';
    const pluralStories = uniqueStories === 1 ? 'story' : 'stories';

    resultsCount.textContent = `${matches.length} ${pluralMatches} in ${uniqueStories} ${pluralStories}`;

    // Show no results message if needed
    if (matches.length === 0) {
        noResultsDiv.classList.remove('hidden');
        return;
    }

    // Render results
    resultsContainer.innerHTML = matches.map(match => {
        const highlightedSnippet = highlightMatch(match.snippet, query);
        const formattedDate = formatDate(match.date);

        return `
            <div class="search-result bg-white p-6 rounded-lg shadow-md border border-gray-200">
                <h3 class="text-xl font-bold mb-2">
                    <a href="${escapeHtml(match.url)}"
                       target="_blank"
                       class="text-blue-600 hover:text-blue-800 hover:underline">
                        ${escapeHtml(match.title)}
                    </a>
                </h3>

                ${match.subtitle ? `
                    <p class="text-sm text-gray-600 italic mb-2">
                        ${escapeHtml(match.subtitle)}
                    </p>
                ` : ''}

                <div class="text-sm text-gray-500 mb-3">
                    <span class="font-medium">${escapeHtml(match.author)}</span>
                    ${formattedDate ? `<span class="mx-2">•</span><span>${formattedDate}</span>` : ''}
                </div>

                <p class="text-gray-800 leading-relaxed mb-3">
                    ${highlightedSnippet}
                </p>

                <a href="${escapeHtml(match.url)}"
                   target="_blank"
                   class="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium">
                    Read full story
                    <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path>
                    </svg>
                </a>
            </div>
        `;
    }).join('');
}

/**
 * Highlight matching text in snippet
 */
function highlightMatch(text, query) {
    if (!query) return escapeHtml(text);

    // Escape special regex characters in query
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

    // Create regex for case-insensitive matching
    const regex = new RegExp(`(${escapedQuery})`, 'gi');

    // First escape HTML, then add highlighting
    const escaped = escapeHtml(text);

    // Replace matches with highlighted version
    const highlighted = escaped.replace(regex, '<mark>$1</mark>');

    // Truncate if too long (keep text around matches)
    return truncateText(highlighted, 400);
}

/**
 * Truncate text if too long
 */
function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;

    // Try to truncate at word boundary
    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');

    if (lastSpace > maxLength * 0.8) {
        return truncated.substring(0, lastSpace) + '...';
    }

    return truncated + '...';
}

/**
 * Format date string
 */
function formatDate(dateString) {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(unsafe) {
    if (!unsafe) return '';

    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSearch);
} else {
    initSearch();
}
