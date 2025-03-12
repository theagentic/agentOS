import time
from typing import Dict, List, Optional
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

class SpotifyRateLimitError(Exception):
    pass

class SpotifyClient:
    BATCH_SIZE = 3  # Number of tracks per request
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, scope: str):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope
        ))

    def _handle_rate_limit(self, e: HTTPError):
        if e.response.status_code == 429:  # Rate limit error
            retry_after = int(e.response.headers.get('Retry-After', 30))
            logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
            time.sleep(retry_after)
            raise SpotifyRateLimitError("Rate limit exceeded")
        raise e

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_artist(self, artist_name: str) -> Optional[Dict]:
        results = self.sp.search(q=artist_name, type='artist', limit=1)
        if results['artists']['items']:
            return results['artists']['items'][0]
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_artist_releases(self, artist_id: str, after_date: str) -> List[Dict]:
        albums = []
        results = self.sp.artist_albums(artist_id, album_type='album,single')
        
        while results:
            for item in results['items']:
                if item['release_date'] >= after_date:
                    albums.append(item)
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
                
        return albums

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_album_tracks(self, album_id: str) -> List[Dict]:
        return self.sp.album_tracks(album_id)['items']

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        tracks = []
        results = self.sp.playlist_tracks(playlist_id)
        
        while results:
            for item in results['items']:
                tracks.append(item['track']['id'])
            if results['next']:
                results = self.sp.next(results)
            else:
                results = None
                
        return tracks

    @retry(retry=retry_if_exception_type(SpotifyRateLimitError),
           stop=stop_after_attempt(3),
           wait=wait_exponential(multiplier=1, min=4, max=10))
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]):
        """Add tracks in batches with pagination"""
        if not track_ids:
            return

        logger.info(f"Adding {len(track_ids)} tracks in batches of {self.BATCH_SIZE}")
        
        # Process tracks in batches
        for i in range(0, len(track_ids), self.BATCH_SIZE):
            batch = track_ids[i:i + self.BATCH_SIZE]
            try:
                self.sp.playlist_add_items(playlist_id, batch)
                logger.debug(f"Added batch of {len(batch)} tracks")
                # Small delay between batches to prevent rate limiting
                time.sleep(1)
            except HTTPError as e:
                self._handle_rate_limit(e)
