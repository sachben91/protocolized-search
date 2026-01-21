#!/usr/bin/env python3
"""
Generate word cloud data from story content
"""

import json
import re
from collections import Counter
from typing import List, Dict

# Common stop words to exclude
STOP_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their',
    'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go',
    'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know',
    'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
    'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over',
    'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first',
    'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day',
    'most', 'us', 'is', 'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did',
    'having', 'may', 'should', 'am', 'being', 'does', 'did', 'done', 'having',
    'more', 'very', 'much', 'such', 'too', 'own', 'same', 'here', 'where', 'why',
    'how', 'each', 'every', 'both', 'few', 'many', 'through', 'during', 'before',
    'above', 'between', 'under', 'again', 'further', 'once', 'here', 'there',
    'while', 'those', 'ever', 'never', 'always', 'often', 'sometimes', 'still',
    'yet', 'already', 'since', 'until', 'however', 'although', 'though', 'unless',
    'whether', 'while', 'upon', 'might', 'must', 'shall', 'ought', 'used', 'made',
    'quite', 'rather', 'really', 'actually', 'perhaps', 'maybe', 'probably',
    'going', 'got', 'getting', 'goes', 'went', 'gone', 'let', 'thing', 'things'
}


def analyze_word_frequency(stories: List[Dict]) -> List[Dict]:
    """Analyze word frequency across all stories"""

    word_counts = Counter()

    for story in stories:
        # Combine all content
        text = ' '.join(story['content'])

        # Also include title (weighted more heavily)
        title_text = story['title'] + ' ' + story['title']  # Count twice
        text = title_text + ' ' + text

        # Tokenize: split by word boundaries, lowercase
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filter out stop words
        filtered_words = [w for w in words if w not in STOP_WORDS]

        # Count
        word_counts.update(filtered_words)

    # Get top words
    top_words = word_counts.most_common(50)

    # Calculate relative sizes (1-5 scale)
    max_count = top_words[0][1] if top_words else 1
    min_count = top_words[-1][1] if len(top_words) > 1 else 1

    word_cloud_data = []
    for word, count in top_words:
        # Scale size from 1 to 5
        if max_count == min_count:
            size = 3
        else:
            size = 1 + 4 * (count - min_count) / (max_count - min_count)

        word_cloud_data.append({
            'word': word,
            'count': count,
            'size': round(size, 1)
        })

    return word_cloud_data


def main():
    """Generate word cloud data"""

    print("📊 Generating word cloud data...")

    # Load search index
    with open('../docs/search-index.json', 'r', encoding='utf-8') as f:
        stories = json.load(f)

    print(f"   Analyzing {len(stories)} stories...")

    # Analyze word frequency
    word_cloud_data = analyze_word_frequency(stories)

    # Save to file
    output_path = '../docs/wordcloud-data.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(word_cloud_data, f, indent=2)

    print(f"✅ Created {output_path}")
    print(f"\n📋 Top 20 words:")
    for item in word_cloud_data[:20]:
        print(f"   {item['word']:20} - {item['count']:4} occurrences (size: {item['size']})")

    print(f"\n💡 Total unique words: {len(word_cloud_data)}")


if __name__ == '__main__':
    main()
