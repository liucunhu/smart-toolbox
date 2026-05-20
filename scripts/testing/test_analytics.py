import requests
import json

resp = requests.get('http://localhost:8000/api/v1/analytics/toutiao/articles', params={'account_id': 8})
data = resp.json()
articles = data.get('articles', [])

print(f'Total articles: {len(articles)}')
print('\nFirst 5 articles:')
for i, a in enumerate(articles[:5]):
    print(f'{i+1}. Title: {a.get("title", "N/A")[:50]}')
    print(f'   Reads: {a.get("read_count", 0)}, Likes: {a.get("like_count", 0)}, Comments: {a.get("comment_count", 0)}')
    print()
