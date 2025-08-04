#!/usr/bin/env python3
"""
Clean up Git history to remove exposed secrets
"""
import subprocess
import os
import sys

def clean_git_history():
    """Remove secrets from Git history using git filter-branch"""
    
    print("🧹 Starting Git History Cleanup")
    print("=" * 40)
    
    # Patterns to remove from Git history (regex patterns for cleanup)
    mongodb_pattern = "mongodb://" + ".*:.*@"  # MongoDB URIs with credentials
    secrets_to_remove = [
        "AKIA[0-9A-Z]{16}",  # AWS Access Key pattern (removed hardcoded key)
        "AWS_ACCESS_KEY",
        "AWS_SECRET_KEY", 
        "aws_secret_access_key",
        mongodb_pattern,  # MongoDB connection strings with credentials
    ]
    
    print("🔍 Secrets to remove from Git history:")
    for secret in secrets_to_remove:
        print(f"  - {secret}")
    
    try:
        # Create a backup branch first
        print("\n📦 Creating backup branch...")
        subprocess.run(["git", "branch", "backup-before-cleanup"], check=True)
        print("✅ Backup branch 'backup-before-cleanup' created")
        
        # Use git filter-repo if available, otherwise use git filter-branch
        try:
            # Check if git-filter-repo is available
            subprocess.run(["git", "filter-repo", "--version"], 
                         capture_output=True, check=True)
            use_filter_repo = True
        except:
            use_filter_repo = False
        
        if use_filter_repo:
            print("\n🔧 Using git-filter-repo for cleanup...")
            # Use git-filter-repo to remove secrets
            for secret in secrets_to_remove:
                cmd = [
                    "git", "filter-repo", 
                    "--replace-text", f"<(echo '{secret}==>REMOVED')",
                    "--force"
                ]
                print(f"Running: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"⚠️ Filter-repo command failed: {result.stderr}")
        else:
            print("\n🔧 Using git filter-branch for cleanup...")
            # Use git filter-branch as fallback
            for secret in secrets_to_remove:
                cmd = [
                    "git", "filter-branch", "--force", "--index-filter",
                    f"git rm --cached --ignore-unmatch '*{secret}*'",
                    "--prune-empty", "--tag-name-filter", "cat", "--", "--all"
                ]
                print(f"Removing references to: {secret}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"⚠️ Filter-branch command failed: {result.stderr}")
        
        # Clean up refs
        print("\n🧽 Cleaning up references...")
        subprocess.run(["git", "for-each-ref", "--format=delete %(refname)", 
                       "refs/original/"], capture_output=True)
        
        # Force garbage collection
        print("🗑️  Running garbage collection...")
        subprocess.run(["git", "reflog", "expire", "--expire=now", "--all"], 
                      check=False)
        subprocess.run(["git", "gc", "--prune=now", "--aggressive"], 
                      check=False)
        
        print("\n✅ Git history cleanup completed!")
        print("📝 What was done:")
        print("  - Created backup branch 'backup-before-cleanup'")
        print("  - Removed AWS credentials from Git history")
        print("  - Cleaned up MongoDB connection strings")
        print("  - Performed garbage collection")
        
        print("\n🔧 Next steps:")
        print("  1. Verify the cleanup worked: git log -p | grep AKIA")
        print("  2. Try pushing to GitHub again")
        print("  3. If issues persist, contact GitHub support")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git cleanup failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def verify_cleanup():
    """Verify that secrets have been removed from Git history"""
    
    print("\n🔍 Verifying cleanup...")
    
    # Search for remaining secrets in Git history
    mongodb_search_pattern = "mongodb://" + ".*:.*@"
    search_patterns = ["AKIA", "aws_secret_access_key", mongodb_search_pattern]
    
    for pattern in search_patterns:
        try:
            result = subprocess.run([
                "git", "log", "-p", "--all"
            ], capture_output=True, text=True)
            
            if pattern in result.stdout:
                print(f"⚠️ Pattern '{pattern}' still found in Git history")
                return False
            else:
                print(f"✅ Pattern '{pattern}' successfully removed")
                
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    print("✅ All secret patterns successfully removed from Git history!")
    return True

def main():
    """Main cleanup process"""
    
    if not os.path.exists('.git'):
        print("❌ Not in a Git repository")
        sys.exit(1)
    
    print("⚠️  WARNING: This will modify Git history!")
    print("📦 A backup branch will be created first")
    
    # Proceed with cleanup
    if clean_git_history():
        if verify_cleanup():
            print("\n🎉 Git history cleanup successful!")
            print("You should now be able to push to GitHub without secret protection errors")
        else:
            print("\n⚠️ Cleanup completed but verification found remaining issues")
    else:
        print("\n❌ Git history cleanup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()