from datetime import datetime, timedelta
import logging
from typing import List
import yaml
from pathlib import Path
from .spotify_client import SpotifyClient

logger = logging.getLogger(__name__)

class PlaylistAutomation:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.client = SpotifyClient(
            client_id=self.config['spotify']['client_id'],
            client_secret=self.config['spotify']['client_secret'],
            redirect_uri=self.config['spotify']['redirect_uri'],
            scope=self.config['spotify']['scope']
        )
        self.artist_playlists = self.config['artist_playlists']
        self.last_run_file = Path("data/last_run.txt")

    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_last_run_date(self) -> str:
        if self.last_run_file.exists():
            with open(self.last_run_file, 'r') as f:
                return f.read().strip()
        return (datetime.now() - timedelta(days=self.config['lookback_days'])).strftime('%Y-%m-%d')

    def _save_last_run_date(self):
        self.last_run_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.last_run_file, 'w') as f:
            f.write(datetime.now().strftime('%Y-%m-%d'))

    def process_artist(self, artist_name: str, after_date: str):
        logger.info(f"Processing artist: {artist_name}")
        
        try:
            # Find artist
            artist = self.client.search_artist(artist_name)
            if not artist:
                logger.warning(f"Could not find artist: {artist_name}")
                return

            playlist_id = self.artist_playlists[artist_name]
            
            # Get new releases
            releases = self.client.get_artist_releases(artist['id'], after_date)
            if not releases:
                logger.info(f"No new releases found for {artist_name}")
                return

            # Get existing tracks in artist's playlist
            existing_tracks = set(self.client.get_playlist_tracks(playlist_id))

            # Process new tracks
            new_tracks = []
            for release in releases:
                tracks = self.client.get_album_tracks(release['id'])
                for track in tracks:
                    if track['id'] not in existing_tracks:
                        new_tracks.append(track['id'])

            # Add new tracks to artist's playlist with progress logging
            if new_tracks:
                total_tracks = len(new_tracks)
                logger.info(f"Adding {total_tracks} new tracks to {artist_name}'s playlist in batches")
                self.client.add_tracks_to_playlist(playlist_id, new_tracks)
                logger.info(f"Successfully added all {total_tracks} tracks to {artist_name}'s playlist")
        except Exception as e:
            logger.error(f"Error processing artist {artist_name}: {str(e)}", exc_info=True)
            raise

    def run(self):
        logger.info("Starting playlist automation")
        last_run_date = self._get_last_run_date()
        
        for artist in self.artist_playlists.keys():
            try:
                self.process_artist(artist, last_run_date)
            except Exception as e:
                logger.error(f"Error processing artist {artist}: {str(e)}")

        self._save_last_run_date()
        logger.info("Playlist automation completed")
