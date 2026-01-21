#!/usr/bin/env python3
"""
Generate word cloud data from story content
"""

import json
import re
from collections import Counter
from typing import List, Dict

# Comprehensive stop words to exclude - focus on keeping nouns and meaningful content words
STOP_WORDS = {
    # Articles, conjunctions, prepositions
    'the', 'a', 'an', 'and', 'or', 'but', 'if', 'as', 'at', 'by', 'for', 'from',
    'in', 'into', 'of', 'on', 'onto', 'to', 'with', 'about', 'above', 'across',
    'after', 'against', 'along', 'among', 'around', 'before', 'behind', 'below',
    'beneath', 'beside', 'between', 'beyond', 'during', 'except', 'inside', 'near',
    'off', 'outside', 'over', 'through', 'throughout', 'under', 'until', 'up', 'upon',
    'within', 'without', 'toward', 'towards',

    # Pronouns
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
    'my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours',
    'theirs', 'myself', 'yourself', 'himself', 'herself', 'itself', 'ourselves',
    'themselves', 'this', 'that', 'these', 'those', 'who', 'whom', 'whose', 'which',
    'what', 'whatever', 'whoever', 'whomever',

    # Common verbs (to focus on nouns)
    'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'having', 'do', 'does', 'did', 'doing', 'done', 'will', 'would', 'shall', 'should',
    'may', 'might', 'must', 'can', 'could', 'ought', 'need', 'dare',
    'go', 'goes', 'going', 'went', 'gone', 'get', 'gets', 'getting', 'got', 'gotten',
    'make', 'makes', 'making', 'made', 'take', 'takes', 'taking', 'took', 'taken',
    'come', 'comes', 'coming', 'came', 'see', 'sees', 'seeing', 'saw', 'seen',
    'know', 'knows', 'knowing', 'knew', 'known', 'think', 'thinks', 'thinking', 'thought',
    'look', 'looks', 'looking', 'looked', 'give', 'gives', 'giving', 'gave', 'given',
    'use', 'uses', 'using', 'used', 'find', 'finds', 'finding', 'found',
    'tell', 'tells', 'telling', 'told', 'ask', 'asks', 'asking', 'asked',
    'work', 'works', 'working', 'worked', 'seem', 'seems', 'seeming', 'seemed',
    'feel', 'feels', 'feeling', 'felt', 'try', 'tries', 'trying', 'tried',
    'leave', 'leaves', 'leaving', 'left', 'call', 'calls', 'calling', 'called',
    'keep', 'keeps', 'keeping', 'kept', 'let', 'lets', 'letting',
    'begin', 'begins', 'beginning', 'began', 'begun', 'help', 'helps', 'helping', 'helped',
    'show', 'shows', 'showing', 'showed', 'shown', 'hear', 'hears', 'hearing', 'heard',
    'play', 'plays', 'playing', 'played', 'run', 'runs', 'running', 'ran',
    'move', 'moves', 'moving', 'moved', 'live', 'lives', 'living', 'lived',
    'believe', 'believes', 'believing', 'believed', 'bring', 'brings', 'bringing', 'brought',
    'happen', 'happens', 'happening', 'happened', 'write', 'writes', 'writing', 'wrote', 'written',
    'sit', 'sits', 'sitting', 'sat', 'stand', 'stands', 'standing', 'stood',
    'lose', 'loses', 'losing', 'lost', 'pay', 'pays', 'paying', 'paid',
    'meet', 'meets', 'meeting', 'met', 'include', 'includes', 'including', 'included',
    'continue', 'continues', 'continuing', 'continued', 'set', 'sets', 'setting',
    'learn', 'learns', 'learning', 'learned', 'change', 'changes', 'changing', 'changed',
    'lead', 'leads', 'leading', 'led', 'understand', 'understands', 'understanding', 'understood',
    'watch', 'watches', 'watching', 'watched', 'follow', 'follows', 'following', 'followed',
    'stop', 'stops', 'stopping', 'stopped', 'create', 'creates', 'creating', 'created',
    'speak', 'speaks', 'speaking', 'spoke', 'spoken', 'read', 'reads', 'reading',
    'spend', 'spends', 'spending', 'spent', 'grow', 'grows', 'growing', 'grew', 'grown',
    'open', 'opens', 'opening', 'opened', 'walk', 'walks', 'walking', 'walked',
    'win', 'wins', 'winning', 'won', 'offer', 'offers', 'offering', 'offered',
    'remember', 'remembers', 'remembering', 'remembered', 'consider', 'considers', 'considering', 'considered',
    'appear', 'appears', 'appearing', 'appeared', 'buy', 'buys', 'buying', 'bought',
    'serve', 'serves', 'serving', 'served', 'die', 'dies', 'dying', 'died',
    'send', 'sends', 'sending', 'sent', 'expect', 'expects', 'expecting', 'expected',
    'build', 'builds', 'building', 'built', 'stay', 'stays', 'staying', 'stayed',
    'fall', 'falls', 'falling', 'fell', 'fallen', 'cut', 'cuts', 'cutting',
    'reach', 'reaches', 'reaching', 'reached', 'kill', 'kills', 'killing', 'killed',
    'remain', 'remains', 'remaining', 'remained', 'suggest', 'suggests', 'suggesting', 'suggested',
    'raise', 'raises', 'raising', 'raised', 'pass', 'passes', 'passing', 'passed',

    # Adverbs and qualifiers
    'not', 'no', 'yes', 'just', 'only', 'also', 'very', 'too', 'so', 'much', 'many',
    'more', 'most', 'less', 'least', 'few', 'some', 'any', 'all', 'both', 'each',
    'every', 'either', 'neither', 'such', 'own', 'same', 'other', 'another',
    'well', 'even', 'still', 'yet', 'however', 'though', 'although', 'never', 'always',
    'often', 'sometimes', 'usually', 'already', 'quite', 'rather', 'really', 'actually',
    'perhaps', 'maybe', 'probably', 'possibly', 'certainly', 'surely',
    'like', 'how', 'why', 'than', 'while', 'because', 'since', 'unless', 'whether',

    # Common time/place words
    'now', 'then', 'when', 'where', 'here', 'there', 'today', 'tomorrow', 'yesterday',
    'once', 'again', 'back', 'away', 'out', 'down', 'next', 'last', 'first', 'second',
    'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',

    # Contractions and informal
    'don', 'doesn', 'didn', 'wasn', 'weren', 'haven', 'hasn', 'hadn', 'won', 'wouldn',
    'can', 'couldn', 'shouldn', 'isn', 'aren', 'ain', 've', 'll', 're',

    # Generic words
    'something', 'anything', 'nothing', 'everything', 'someone', 'anyone', 'everyone',
    'somewhere', 'anywhere', 'everywhere', 'thing', 'things', 'way', 'ways',
    'time', 'times', 'day', 'days', 'year', 'years', 'part', 'parts',
    'place', 'places', 'case', 'cases', 'point', 'points', 'fact', 'facts',
    'lot', 'lots', 'bit', 'bits', 'kind', 'kinds', 'sort', 'sorts', 'type', 'types',

    # Misc common words
    'good', 'bad', 'new', 'old', 'great', 'big', 'small', 'little', 'long', 'short',
    'high', 'low', 'right', 'left', 'sure', 'okay', 'fine', 'nice', 'pretty',
    'people', 'person', 'man', 'woman', 'child', 'number', 'way', 'end', 'side',
    'want', 'wants', 'wanted', 'wanting', 'need', 'needs', 'needed', 'needing',
    'say', 'says', 'saying', 'said', 'mean', 'means', 'meaning', 'meant',
    'become', 'becomes', 'becoming', 'became', 'add', 'adds', 'adding', 'added'
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
