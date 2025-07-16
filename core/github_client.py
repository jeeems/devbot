import os
from github import Github

# Initialize GitHub client
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN environment variable not set")
    github_client = None
else:
    github_client = Github(GITHUB_TOKEN)

def check_repo_access(repo_path: str, branch: str = "main"):
    """Check if repository is accessible with current GitHub token"""
    if not github_client:
        return None, "GitHub client is not initialized. Check GITHUB_TOKEN."
    try:
        repo = github_client.get_repo(repo_path)
        repo.get_contents("", ref=branch)
        return repo, None
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            return None, "Repository not found or access denied."
        elif "401" in error_msg:
            return None, "Authentication failed. Check your GitHub token."
        else:
            return None, f"Error accessing repository: {error_msg}"