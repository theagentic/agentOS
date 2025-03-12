import subprocess
import os
from typing import Tuple, List

class GitHandler:
    def __init__(self, blog_repo_path: str):
        self.blog_repo_path = blog_repo_path
        self.obsidian_path = os.environ.get("OBSIDIAN_VAULT_PATH", "")
        # Set the Hugo content path directly to match the exact path
        self.hugo_content_path = os.path.join(self.blog_repo_path, "content", "posts")
    
    def execute_powershell_command(self, command: str, cwd: str = None) -> Tuple[bool, str, str]:
        """Execute a PowerShell command and return success status, stdout, and stderr"""
        try:
            process = subprocess.Popen(
                ['powershell', '-Command', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=cwd if cwd else self.blog_repo_path
            )
            stdout, stderr = process.communicate()
            success = process.returncode == 0
            return success, stdout, stderr
        except Exception as e:
            return False, "", str(e)
    
    def sync_obsidian_to_hugo(self, source_path: str = None) -> Tuple[bool, str]:
        """Sync blog files from Obsidian vault to Hugo content directory"""
        if not source_path and not self.obsidian_path:
            return False, "No source path specified and OBSIDIAN_VAULT_PATH not set"
        
        # Use the direct path without appending "Blog"
        source = source_path if source_path else self.obsidian_path
        if not os.path.exists(source):
            return False, f"Source path does not exist: {source}"
        
        # Ensure target directory exists
        os.makedirs(self.hugo_content_path, exist_ok=True)
        
        # Use robocopy to mirror the directories
        command = f'robocopy "{source}" "{self.hugo_content_path}" /mir'
        success, stdout, stderr = self.execute_powershell_command(command)
        
        # Robocopy returns specific exit codes:
        # 0 = No files copied
        # 1 = Files copied successfully
        # 2 = Extra files/dirs detected
        # 4 = Mismatched files/dirs detected
        # Values 0-7 are considered success for robocopy
        # We get the actual return code from the PowerShell execution
        return_code = 0
        
        # Check if we got a return code in stdout (PowerShell outputs $LASTEXITCODE)
        if stdout and "LASTEXITCODE" in stdout:
            try:
                # Extract the return code from stdout
                for line in stdout.splitlines():
                    if line.strip().isdigit():
                        return_code = int(line.strip())
                        break
            except ValueError:
                pass
        
        # If we couldn't get the return code from stdout, use the success flag
        # While success will be False for robocopy even on successful copies with changes,
        # we'll consider it a failure only if stderr contains error messages
        robocopy_success = success or (return_code < 8 and not stderr)
        
        if robocopy_success:
            return True, "Successfully synchronized Obsidian files to Hugo"
        else:
            return False, f"Failed to sync files: {stderr}"
    
    def build_hugo_site(self) -> Tuple[bool, str]:
        """Build the Hugo site"""
        command = "hugo"
        success, stdout, stderr = self.execute_powershell_command(command)
        
        if success:
            return True, "Hugo site built successfully"
        else:
            return False, f"Failed to build Hugo site: {stderr}"
    
    def commit_and_push_blog_post(self, file_name: str = None, commit_message: str = None) -> Tuple[bool, str]:
        """Commit and push changes to the blog repository"""
        # Extract just the filename without path if provided
        message = commit_message
        if file_name and not message:
            base_file_name = os.path.basename(file_name)
            message = f"Add blog post for {base_file_name}"
        elif not message:
            message = "Update blog content"
        
        # Commands to execute
        commands = [
            "git pull origin main",
            "git add .",
            f'git commit -m "{message}"',
            "git push origin main"
        ]
        
        results = []
        for cmd in commands:
            success, stdout, stderr = self.execute_powershell_command(cmd)
            results.append((success, cmd, stdout, stderr))
            
            # Stop if a command fails
            if not success:
                # For commit, it's fine if there's nothing to commit
                if "nothing to commit" in stderr or "nothing to commit" in stdout:
                    return True, "No changes to commit"
                
                error_msg = f"Failed to execute '{cmd}'. Error: {stderr}"
                return False, error_msg
        
        return True, "Successfully committed and pushed blog post changes"
    
    def full_publish_workflow(self, source_path: str = None, commit_message: str = None) -> Tuple[bool, List[str]]:
        """Run the full publishing workflow:
        1. Sync from Obsidian to Hugo
        2. Build Hugo site
        3. Commit and push changes
        """
        results = []
        
        # Step 1: Sync files
        success, message = self.sync_obsidian_to_hugo(source_path)
        results.append(f"Sync: {'✅' if success else '❌'} - {message}")
        if not success:
            return False, results
        
        # Step 2: Build Hugo site
        success, message = self.build_hugo_site()
        results.append(f"Build: {'✅' if success else '❌'} - {message}")
        if not success:
            return False, results
        
        # Step 3: Git operations
        success, message = self.commit_and_push_blog_post(commit_message=commit_message)
        results.append(f"Deploy: {'✅' if success else '❌'} - {message}")
        
        return all(r.startswith("Sync: ✅") or r.startswith("Build: ✅") or r.startswith("Deploy: ✅") for r in results), results
