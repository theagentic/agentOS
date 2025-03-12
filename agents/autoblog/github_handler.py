import os
import base64
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class GitHubHandler:
    def __init__(self, token: str, username: str):
        self.token = token
        self.username = username
        self.headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        self.base_url = 'https://api.github.com'
        self._processed_repos_file = 'processed_repos.json'
        self._processed_repos, self._latest_processed_date, self._reference_date = self._load_processed_repos()
        
    def _load_processed_repos(self) -> Tuple[Dict[str, str], str, str]:
        """
        Load the list of already processed repositories and their publish dates.
        Returns a tuple of (processed_repos_dict, latest_processed_date, reference_date)
        """
        processed_repos = {}
        latest_date = "1970-01-01T00:00:00Z"  # Default to epoch start
        reference_date = "2025-02-07T00:00:00Z"  # Default cutoff date
        
        if os.path.exists(self._processed_repos_file):
            try:
                with open(self._processed_repos_file, 'r') as f:
                    data = json.load(f)
                    
                    # Check if the data is the new format with metadata
                    if isinstance(data, dict) and "_metadata" in data:
                        # Extract metadata
                        metadata = data.pop("_metadata", {})
                        reference_date = metadata.get("reference_date", reference_date)
                        processed_repos = data
                    # Handle both old format (list of strings) and intermediate format (dict with dates)
                    elif isinstance(data, list):
                        # Convert old format to new format
                        processed_repos = {repo: "1970-01-01T00:00:00Z" for repo in data}
                    else:
                        processed_repos = data
                        
                    # Find the latest processed date
                    for date in processed_repos.values():
                        if date > latest_date:
                            latest_date = date
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self._processed_repos_file}. Starting with empty history.")
                
        return processed_repos, latest_date, reference_date
    
    def _save_processed_repos(self):
        """Save the list of processed repositories with their dates and metadata"""
        # Create data structure with metadata
        data = {
            "_metadata": {
                "reference_date": self._reference_date,
                "last_updated": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        }
        
        # Add the repositories
        for repo_name, repo_date in self._processed_repos.items():
            data[repo_name] = repo_date
            
        with open(self._processed_repos_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def set_reference_date(self, date_str: str):
        """Set the reference date - repositories created before this date will be ignored"""
        try:
            # Validate the date format
            datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            self._reference_date = date_str
            self._save_processed_repos()
            return True
        except ValueError:
            print(f"Error: Date '{date_str}' is not in the format 'YYYY-MM-DDTHH:MM:SSZ'")
            return False
    
    def get_user_repos(self) -> List[Dict]:
        """Get all repositories for the user"""
        url = f"{self.base_url}/users/{self.username}/repos"
        repos = []
        page = 1
        
        while True:
            response = requests.get(f"{url}?page={page}&per_page=100&sort=created&direction=desc", headers=self.headers)
            response.raise_for_status()
            page_repos = response.json()
            if not page_repos:
                break
            repos.extend(page_repos)
            page += 1
        
        return repos
    
    def check_readme_exists(self, repo_name: str) -> bool:
        """Check if a README.md file exists in the repository"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/contents/README.md"
        response = requests.get(url, headers=self.headers)
        return response.status_code == 200
    
    def get_repo_content(self, repo_name: str, path: str = '') -> List[Dict]:
        """Get the content of a repository directory"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, repo_name: str, file_path: str) -> str:
        """Get the content of a specific file in the repository"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/contents/{file_path}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        content = response.json()
        if content.get('encoding') == 'base64':
            return base64.b64decode(content['content']).decode('utf-8')
        return ''
    
    def get_repo_languages(self, repo_name: str) -> Dict[str, int]:
        """Get the languages used in a repository"""
        url = f"{self.base_url}/repos/{self.username}/{repo_name}/languages"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def find_new_repos(self) -> List[Dict]:
        """
        Find repositories that:
        1. Are newer than the reference date
        2. Either haven't been processed OR have been updated since last processed
        3. Have a README.md file
        """
        repos = self.get_user_repos()
        new_repos = []
        
        for repo in repos:
            repo_name = repo['name']
            created_date = repo['created_at']
            
            # Skip repos created before the reference date
            if created_date < self._reference_date:
                continue
                
            # Check if repo is new or newer than our last processed version
            is_new = (repo_name not in self._processed_repos) or (created_date > self._processed_repos.get(repo_name, "1970-01-01T00:00:00Z"))
            
            if is_new and self.check_readme_exists(repo_name):
                print(f"Found new/updated repo: {repo_name} (created: {created_date})")
                new_repos.append(repo)
        
        # Sort by creation date (newest first)
        new_repos.sort(key=lambda x: x['created_at'], reverse=True)
        return new_repos
    
    def mark_repo_as_processed(self, repo_name: str, created_date: str = None):
        """
        Mark a repository as processed with its creation date.
        If no date is provided, current date is used.
        """
        if not created_date:
            created_date = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            
        self._processed_repos[repo_name] = created_date
        
        # Update latest processed date if this is newer
        if created_date > self._latest_processed_date:
            self._latest_processed_date = created_date
            
        self._save_processed_repos()
    
    def gather_repo_data(self, repo: Dict) -> Dict:
        """Gather all relevant data from a repository for blog post generation"""
        repo_name = repo['name']
        repo_data = {
            'name': repo_name,
            'url': repo['html_url'],
            'description': repo['description'] or '',
            'created_at': repo['created_at'],
            'updated_at': repo['updated_at'],
            'language': repo['language'],
            'readme': self.get_file_content(repo_name, 'README.md'),
            'languages': self.get_repo_languages(repo_name),
            'code_samples': {}
        }
        
        # Get some code samples (limit to a few key files)
        try:
            contents = self.get_repo_content(repo_name)
            for item in contents:
                if item['type'] == 'file' and item['name'].endswith(('.py', '.js', '.ts', '.html', '.css', '.java', '.cpp')):
                    file_content = self.get_file_content(repo_name, item['path'])
                    repo_data['code_samples'][item['name']] = file_content
                    # Limit to 5 code samples to avoid too much content
                    if len(repo_data['code_samples']) >= 5:
                        break
        except Exception as e:
            print(f"Error getting code samples: {e}")
            
        return repo_data
    
    def get_repository_by_name(self, repo_name: str) -> Optional[Dict]:
        """
        Get a specific repository by name, regardless of whether it's been processed.
        
        Args:
            repo_name: Name of the repository to fetch
            
        Returns:
            Repository data dictionary or None if not found
        """
        # First check if it's a user repository
        url = f"{self.base_url}/repos/{self.username}/{repo_name}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            repo_data = response.json()
            # Check if the repository has a README
            has_readme = self.check_readme_exists(repo_name)
            if has_readme:
                return repo_data
            else:
                print(f"Repository {repo_name} does not have a README.md file.")
                return None
        else:
            # Try searching for the repository
            search_url = f"{self.base_url}/search/repositories?q={repo_name}+user:{self.username}"
            search_response = requests.get(search_url, headers=self.headers)
            
            if search_response.status_code == 200:
                search_results = search_response.json()
                if search_results.get('total_count', 0) > 0:
                    # Get the first matching repository
                    for repo in search_results.get('items', []):
                        if repo['name'].lower() == repo_name.lower():
                            # Check if the repository has a README
                            has_readme = self.check_readme_exists(repo['name'])
                            if has_readme:
                                return repo
                            else:
                                print(f"Repository {repo['name']} does not have a README.md file.")
                                return None
                    
                    # If we get here, none of the repositories matched exactly
                    return None
                else:
                    return None
            else:
                return None
                
    def get_processed_repos(self) -> Dict[str, str]:
        """
        Get the dictionary of processed repositories.
        
        Returns:
            Dictionary of processed repositories with dates
        """
        return self._processed_repos
