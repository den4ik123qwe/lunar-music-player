import requests

def search_tracks(query, limit=20):
    params = {'q': query, 'limit': limit}
    try:
        response = requests.get("https://api.deezer.com/search", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        tracks = []
        for track in data.get('data', []):
            track_info = {
                'title': track.get('title', 'Unknown'),
                'artist': track.get('artist', {}).get('name', 'Unknown'),
                'preview': track.get('preview', ''),
                'duration': track.get('duration', 0),
                'album': track.get('album', {}).get('title', ''),
                'cover_medium': track.get('album', {}).get('cover_medium', ''),
                'track_id': track.get('id')
            }
            tracks.append(track_info)
        return tracks if tracks else get_demo_tracks(query, limit)
    except Exception as e:
        print(f"Ошибка Deezer API: {e}")
        return get_demo_tracks(query, limit)

def get_demo_tracks(query, limit=10):
    demo_tracks = [
        {'title': 'Midnight Dreams', 'artist': 'Luna Echo', 'preview': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3', 'duration': 240, 'cover_medium': ''},
        {'title': 'Ocean Waves', 'artist': 'Coastal Breeze', 'preview': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3', 'duration': 210, 'cover_medium': ''},
        {'title': 'Mountain High', 'artist': 'Alpine Project', 'preview': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3', 'duration': 195, 'cover_medium': ''},
        {'title': 'Urban Lights', 'artist': 'City Pulse', 'preview': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3', 'duration': 225, 'cover_medium': ''},
        {'title': 'Desert Wind', 'artist': 'Sahara Sound', 'preview': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3', 'duration': 230, 'cover_medium': ''},
    ]
    result = []
    query_lower = query.lower()
    for track in demo_tracks:
        if query_lower in track['title'].lower() or query_lower in track['artist'].lower():
            result.append(track)
        if len(result) >= limit:
            break
    if not result:
        result = demo_tracks[:limit]
    return result

def get_tracks_with_full_audio(query, limit=20):
    return search_tracks(query, limit)

def test_api_connection():
    try:
        response = requests.get("https://api.deezer.com/search?q=test&limit=1", timeout=10)
        if response.status_code == 200:
            return True, "API работает (30-секундные превью Deezer)"
        else:
            return False, "Используются демо-треки"
    except Exception as e:
        return False, f"Используются демо-треки: {e}"