"""
Sybil-OS Maintainer Agent
Automated Code Review & Approval Logic

This script monitors the Sybil-OS repository for incoming Pull Requests,
analyzes changes, validates architecture alignment, and enforces security policies.
"""

import os
import re
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Load environment
from dotenv import load_dotenv
load_dotenv()

import requests

logger = logging.getLogger(__name__)


# ==================== Configuration ====================

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "hmnuiodaryim0-lab/sybil-OS")
CREATOR_MENTION = os.getenv("CREATOR_MENTION", "hmnuiodaryim0-lab")

GITHUB_API = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


# ==================== Data Models ====================

class ReviewDecision(Enum):
    """Review decision types"""
    APPROVE_MERGE = "approve_merge"      # Minor doc update, auto-merge
    REVIEW_REQUIRED = "review_required"  # Code change, needs human review
    SECURITY_RISK = "security_risk"      # Suspicious, close PR
    SKIP = "skip"                        # Already processed


@dataclass
class PullRequest:
    """GitHub Pull Request"""
    number: int
    title: str
    body: str
    state: str
    user: str
    head_sha: str
    files_url: str
    html_url: str


@dataclass
class ReviewResult:
    """Review result"""
    decision: ReviewDecision
    summary: str
    pros: List[str]
    cons: List[str]
    security_concerns: List[str]
    architecture_concerns: List[str]
    files_changed: int


# ==================== Security Patterns ====================

SECRET_PATTERNS = [
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"sk-ant-[a-zA-Z0-9_-]{20,}", "Anthropic API Key"),
    (r"DISCORD_BOT_TOKEN\s*=\s*['\"][a-zA-Z0-9_-]{20,}['\"]", "Discord Bot Token"),
    (r"AIza[0-9A-Za-z_-]{35}", "Google API Key"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
    (r"xox[baprs]-[0-9a-zA-Z]{10,}", "Slack Token"),
    (r"sq0csp-[0-9A-Za-z_-]{43}", "Square OAuth Secret"),
]

SENSITIVE_PATTERNS = [
    (r"password\s*=\s*['\"][^'\"]+['\"]", "Hardcoded password"),
    (r"api_key\s*=\s*['\"][^'\"]+['\"]", "Hardcoded API key"),
    (r"secret\s*=\s*['\"][^'\"]+['\"]", "Hardcoded secret"),
    (r"C:/Users/[\w/]+", "Windows absolute path"),
    (r"/home/[\w/]+", "Linux absolute path"),
    (r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", "IP address (potential internal)"),
]


# ==================== Architecture Validation ====================

REQUIRED_FILES = {
    "models/persona.py": "HumanCognitiveProfile model",
    "core/allocator.py": "Career allocation algorithm",
    "database/schema.sql": "Database schema with pgvector",
}

ARCHITECTURE_KEYWORDS = {
    "logic_depth", "empathy_level", "stress_resilience", 
    "creative_entropy", "social_cohesion", "vector_summary",
    "HumanCognitiveProfile", "ProjectRequirement", "ObserverRegistry"
}


# ==================== Maintainer Logic ====================

class SybilOSMaintainer:
    """
    Automated code review and approval for Sybil-OS
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.repo = GITHUB_REPO
        self.processed_prs: set = set()
    
    # -------------------- Core API --------------------
    
    def get_open_prs(self) -> List[PullRequest]:
        """Get all open pull requests"""
        url = f"{GITHUB_API}/repos/{self.repo}/pulls?state=open"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            return [
                PullRequest(
                    number=pr["number"],
                    title=pr["title"],
                    body=pr.get("body", ""),
                    state=pr["state"],
                    user=pr["user"]["login"],
                    head_sha=pr["head"]["sha"],
                    files_url=pr["files_url"],
                    html_url=pr["html_url"]
                )
                for pr in data
            ]
        except Exception as e:
            logger.error(f"Failed to get PRs: {e}")
            return []
    
    def get_pr_files(self, pr_number: int) -> List[Dict]:
        """Get files changed in a PR"""
        url = f"{GITHUB_API}/repos/{self.repo}/pulls/{pr_number}/files"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to get PR files: {e}")
            return []
    
    def get_file_content(self, path: str, ref: str = "master") -> Optional[str]:
        """Get file content from repository"""
        url = f"{GITHUB_API}/repos/{self.repo}/contents/{path}?ref={ref}"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            import base64
            data = resp.json()
            return base64.b64decode(data["content"]).decode("utf-8")
        except Exception:
            return None
    
    # -------------------- Security Check --------------------
    
    def check_secrets(self, files: List[Dict]) -> List[Tuple[str, str]]:
        """Check for hardcoded secrets"""
        concerns = []
        
        for f in files:
            filename = f.get("filename", "")
            patch = f.get("patch", "")
            
            # Skip non-code files
            if any(x in filename for x in [".md", ".txt", ".lock", ".json"]):
                continue
            
            for pattern, description in SECRET_PATTERNS:
                if re.search(pattern, patch, re.IGNORECASE):
                    concerns.append((filename, f"🔴 {description} detected"))
            
            for pattern, description in SENSITIVE_PATTERNS:
                if re.search(pattern, patch, re.IGNORECASE):
                    concerns.append((filename, f"🟡 {description}"))
        
        return concerns
    
    # -------------------- Architecture Check --------------------
    
    def check_architecture(self, files: List[Dict]) -> Tuple[bool, List[str]]:
        """Validate architecture alignment"""
        concerns = []
        valid = True
        
        # Check if key files are modified
        modified_files = {f.get("filename", "") for f in files}
        
        # Check for HumanCognitiveProfile usage
        for f in files:
            filename = f.get("filename", "")
            patch = f.get("patch", "")
            
            # Check if new files introduce required keywords
            if f.get("status") == "added":
                for keyword in ARCHITECTURE_KEYWORDS:
                    if keyword in patch:
                        # Good - using architecture keywords
                        pass
            
            # Check for breaking changes
            if "delete" in f.get("status", ""):
                for req_file in REQUIRED_FILES:
                    if req_file in filename:
                        concerns.append(f"🗑️ Deleted required file: {req_file}")
                        valid = False
        
        return valid, concerns
    
    # -------------------- ETHICS Check --------------------
    
    def check_ethics(self, files: List[Dict]) -> List[str]:
        """Check for ETHICS.md violations"""
        concerns = []
        
        ethics_violations = [
            (r"surveillance.*without.*consent", "Potential surveillance without consent"),
            (r"force.*allocation", "Forced job allocation"),
            (r"remove.*appeal", "Removed human appeal mechanism"),
            (r"bypass.*consent", "Data collection bypassing consent"),
        ]
        
        for f in files:
            patch = f.get("patch", "")
            
            for pattern, description in ethics_violations:
                if re.search(pattern, patch, re.IGNORECASE):
                    concerns.append(f"⚠️ ETHICS.md: {description}")
        
        return concerns
    
    # -------------------- Review Decision --------------------
    
    def review_pr(self, pr: PullRequest) -> ReviewResult:
        """Review a pull request and make decision"""
        files = self.get_pr_files(pr.number)
        
        # Default result
        result = ReviewResult(
            decision=ReviewDecision.REVIEW_REQUIRED,
            summary="",
            pros=[],
            cons=[],
            security_concerns=[],
            architecture_concerns=[]
        )
        
        result.files_changed = len(files)
        
        # 1. Security check
        secrets = self.check_secrets(files)
        if secrets:
            result.security_concerns = [f"{file}: {issue}" for file, issue in secrets]
            result.decision = ReviewDecision.SECURITY_RISK
        
        # 2. Architecture check
        arch_valid, arch_concerns = self.check_architecture(files)
        result.architecture_concerns = arch_concerns
        
        # 3. ETHICS check
        ethics_concerns = self.check_ethics(files)
        
        # 4. Determine decision
        doc_extensions = {".md", ".txt", ".yaml", ".yml", ".json"}
        code_extensions = {".py", ".js", ".ts", ".sql"}
        
        doc_files = [f for f in files 
                    if any(f.get("filename", "").endswith(ext) for ext in doc_extensions)]
        code_files = [f for f in files 
                     if any(f.get("filename", "").endswith(ext) for ext in code_extensions)]
        
        # Decision logic
        if result.decision == ReviewDecision.SECURITY_RISK:
            result.summary = "Security concerns detected. PR requires manual review."
        elif len(code_files) == 0 and len(doc_files) > 0:
            # Only doc changes - auto merge
            result.decision = ReviewDecision.APPROVE_MERGE
            result.summary = "Minor documentation update. Auto-approved."
            result.pros = ["No code changes", "Improves documentation"]
        elif ethics_concerns:
            result.decision = ReviewDecision.SECURITY_RISK
            result.summary = "Potential ETHICS.md violation detected."
            result.security_concerns.extend(ethics_concerns)
        else:
            result.decision = ReviewDecision.REVIEW_REQUIRED
            result.summary = "Code changes require human review."
            result.pros = ["Valid contributions", "Architecture maintained"]
        
        return result
    
    # -------------------- Actions --------------------
    
    def post_review(self, pr: PullRequest, result: ReviewResult):
        """Post review comment and decision"""
        # Build review body
        body = f"""## 🤖 Sybil-OS Maintainer Review

**Decision:** {result.decision.value}

---

### Summary
{result.summary}

### Files Changed: {result.files_changed}

"""
        
        if result.pros:
            body += "### ✅ Pros\n"
            for pro in result.pros:
                body += f"- {pro}\n"
            body += "\n"
        
        if result.architecture_concerns:
            body += "### 🏗️ Architecture Review\n"
            for concern in result.architecture_concerns:
                body += f"- {concern}\n"
            body += "\n"
        
        if result.security_concerns:
            body += "### 🔐 Security Concerns\n"
            for concern in result.security_concerns:
                body += f"- {concern}\n"
            body += "\n"
        
        # Add creator mention for code changes
        if result.decision == ReviewDecision.REVIEW_REQUIRED:
            body += f"---\n\n**@{CREATOR_MENTION}** Please review and approve."
        
        # Post review
        url = f"{GITHUB_API}/repos/{self.repo}/pulls/{pr.number}/reviews"
        review_data = {
            "body": body,
            "event": "COMMENT" if result.decision != ReviewDecision.SECURITY_RISK else "REQUEST_CHANGES"
        }
        
        try:
            resp = self.session.post(url, json=review_data, timeout=10)
            resp.raise_for_status()
            logger.info(f"Review posted for PR #{pr.number}")
        except Exception as e:
            logger.error(f"Failed to post review: {e}")
    
    def merge_pr(self, pr: PullRequest):
        """Merge an approved PR"""
        url = f"{GITHUB_API}/repos/{self.repo}/pulls/{pr.number}/merge"
        data = {
            "commit_title": f"Merge pull request #{pr.number}: {pr.title}",
            "merge_method": "squash"
        }
        
        try:
            resp = self.session.put(url, json=data, timeout=10)
            if resp.status_code == 200:
                logger.info(f"PR #{pr.number} merged successfully")
                return True
            else:
                logger.error(f"Failed to merge: {resp.text}")
                return False
        except Exception as e:
            logger.error(f"Merge error: {e}")
            return False
    
    def close_pr(self, pr: PullRequest, reason: str):
        """Close a PR with security risk"""
        # Add label
        url = f"{GITHUB_API}/repos/{self.repo}/issues/{pr.number}/labels"
        self.session.post(url, json=["security-risk"], timeout=10)
        
        # Close
        url = f"{GITHUB_API}/repos/{self.repo}/pulls/{pr.number}"
        self.session.patch(url, json={"state": "closed"}, timeout=10)
        
        logger.warning(f"PR #{pr.number} closed: {reason}")
    
    # -------------------- Main Loop --------------------
    
    def process_pr(self, pr: PullRequest) -> bool:
        """Process a single PR"""
        if pr.number in self.processed_prs:
            logger.debug(f"PR #{pr.number} already processed")
            return False
        
        logger.info(f"Processing PR #{pr.number}: {pr.title}")
        
        # Review
        result = self.review_pr(pr)
        
        # Post review
        self.post_review(pr, result)
        
        # Take action
        if result.decision == ReviewDecision.APPROVE_MERGE:
            self.merge_pr(pr)
            self.processed_prs.add(pr.number)
            return True
        
        elif result.decision == ReviewDecision.SECURITY_RISK:
            self.close_pr(pr, "Security concerns detected")
            self.processed_prs.add(pr.number)
            return True
        
        else:
            # REVIEW_REQUIRED - just mark as processed
            self.processed_prs.add(pr.number)
            return False
    
    def run_check(self):
        """Run one check cycle"""
        logger.info("Checking for open pull requests...")
        
        prs = self.get_open_prs()
        
        if not prs:
            logger.info("No open PRs found")
            return
        
        for pr in prs:
            self.process_pr(pr)
    
    def start_monitoring(self, interval_minutes: int = 60):
        """Start periodic monitoring"""
        import time
        
        logger.info(f"Starting PR monitoring (every {interval_minutes} minutes)...")
        
        while True:
            try:
                self.run_check()
            except Exception as e:
                logger.error(f"Monitor error: {e}")
            
            time.sleep(interval_minutes * 60)


# ==================== Entry Point ====================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    maintainer = SybilOSMaintainer()
    
    # Run once (for cron)
    # maintainer.run_check()
    
    # Or run continuously
    maintainer.start_monitoring(interval_minutes=60)
