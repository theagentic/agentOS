# Spotify Agent for AgentOS

This agent provides Spotify control and automation capabilities for the AgentOS platform, allowing you to control your music through voice or text commands.

## Features

- Control Spotify playback (play, pause, skip, volume)
- Search and play tracks, albums, artists, and playlists
- Get information about currently playing music
- Create and manage playlists
- Automate discovery of new music from favorite artists
- Schedule automatic playlist updates

## Setup

1. Create a Spotify Developer account and register an application at https://developer.spotify.com/dashboard

2. Copy the example environment file:
   ```
   cp .env.example .env
   ```

3. Configure your Spotify credentials in the `.env` file:
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
   ```

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Run the initial setup to authenticate (one-time process):
   ```
   python spotiauto/setup.py
   ```
   This will open a browser for authentication and save your tokens.

## Usage in AgentOS

### Playback Controls

1. **Play music**:
   ```
   spotiauto play
   ```
   Resumes playback of your most recent session.

   ```
   spotiauto play Coldplay Yellow
   ```
   Searches for and plays the specified track.

2. **Pause music**:
   ```
   spotiauto pause
   ```
   Pauses the currently playing music.

3. **Skip track**:
   ```
   spotiauto next
   ```
   Skips to the next track.

   ```
   spotiauto previous
   ```
   Goes back to the previous track.

4. **Volume control**:
   ```
   spotiauto volume 50
   ```
   Sets volume to 50%.

   ```
   spotiauto volume up
   spotiauto volume down
   ```
   Increases or decreases volume.

### Music Search and Discovery

1. **Search for music**:
   ```
   spotiauto search Billie Eilish
   ```
   Searches for an artist, album, or track.

2. **Play a playlist**:
   ```
   spotiauto playlist "Workout Mix"
   ```
   Plays the specified playlist.

3. **Check what's playing**:
   ```
   spotiauto current
   ```
   Shows information about the currently playing track.

### Playlist Management

1. **Create a playlist**:
   ```
   spotiauto create-playlist "My New Playlist"
   ```
   Creates a new playlist.

2. **Add to playlist**:
   ```
   spotiauto add-to-playlist "My Playlist" "Artist - Song"
   ```
   Adds a track to the specified playlist.

3. **New Releases**:
   ```
   spotiauto new-releases
   ```
   Creates or updates playlists with new music from your favorite artists.

## Automation Features

The agent can be configured to automatically update playlists with new releases from your favorite artists. Edit your `.env` file to set:

- `FAVORITE_ARTISTS`: Comma-separated list of artists to track
- `AUTO_UPDATE`: Set to `true` to enable automatic weekly updates
- `UPDATE_DAY`: Day of week for updates (0-6, where 0 is Monday)
- `NEW_MUSIC_LOOKBACK_DAYS`: How far back to look for new releases

## Help and Status

For a full list of commands and their usage:
```
spotiauto help
```

To check the connection status:
```
spotiauto status
```

## Configuration

Edit `config/config.yaml` to:
- Update Spotify API credentials
- Modify artist list
- Adjust logging settings
- Change lookback period for new releases

## Directory Structure

```
spotiauto/
├── config/
│   └── config.yaml
├── spotiauto/
│   ├── __init__.py
│   ├── spotify_client.py
│   └── automation.py
├── data/
│   └── last_run.txt
├── logs/
│   └── spotiauto.log
├── main.py
├── requirements.txt
└── README.md
```
