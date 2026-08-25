from __future__ import annotations

import re
from urllib.parse import urlparse

import frappe
import requests
from frappe.utils.password import get_decrypted_password


_GITHUB_REPO_RE = re.compile(
	r"(?:https?://)?(?:www\.)?github\.com/(?P<owner>[^/]+)/(?P<repo>[^/?.#]+)",
	re.IGNORECASE,
)


def get_github_access_token() -> str:
	token = get_decrypted_password(
		"SaaS Settings",
		"SaaS Settings",
		"github_access_token",
		raise_exception=False,
	)
	if not token:
		frappe.throw(
			"GitHub access token is not configured. Add it in SaaS Settings → GitHub Distribution."
		)
	return token


def parse_github_repository(repository_url: str) -> tuple[str, str]:
	match = _GITHUB_REPO_RE.search((repository_url or "").strip())
	if not match:
		frappe.throw("Invalid GitHub repository URL on SaaS Application")
	owner = match.group("owner")
	repo = match.group("repo").removesuffix(".git")
	return owner, repo


def _fetch_archive(owner: str, repo: str, ref: str, token: str) -> requests.Response:
	url = f"https://api.github.com/repos/{owner}/{repo}/tarball/{ref}"
	headers = {
		"Authorization": f"Bearer {token}",
		"Accept": "application/vnd.github+json",
		"X-GitHub-Api-Version": "2022-11-28",
	}
	response = requests.get(url, headers=headers, timeout=180, allow_redirects=True)
	return response


def fetch_application_source_archive(application: str, ref: str | None = None) -> tuple[bytes, str]:
	app = frappe.get_doc("SaaS Application", application)
	if not (app.repository_url or "").strip():
		frappe.throw("This application does not have a private GitHub repository configured")

	owner, repo = parse_github_repository(app.repository_url)
	token = get_github_access_token()
	refs = [ref] if ref else ["main", "master", "develop"]
	last_response = None

	for candidate in refs:
		if not candidate:
			continue
		response = _fetch_archive(owner, repo, candidate, token)
		last_response = response
		if response.status_code == 200:
			filename = f"{app.app_slug or repo}-{candidate}.tar.gz"
			return response.content, filename

	if last_response is not None:
		frappe.throw(
			f"Unable to download source archive from GitHub ({last_response.status_code}). "
			"Verify the access token, organization access, and repository URL."
		)
	frappe.throw("Unable to download source archive from GitHub")


def stream_application_source_archive(application: str) -> None:
	"""Write archive bytes to the current HTTP response. Token never leaves the server."""
	content, filename = fetch_application_source_archive(application)
	frappe.local.response.filename = filename
	frappe.local.response.filecontent = content
	frappe.local.response.type = "download"
	frappe.local.response.display_content_as = "attachment"


def get_secure_download_metadata(application: str) -> dict:
	"""Metadata safe to expose to customers — never includes GitHub token."""
	app = frappe.get_doc("SaaS Application", application)
	owner, repo = parse_github_repository(app.repository_url) if app.repository_url else ("", "")
	return {
		"application": application,
		"app_slug": app.app_slug,
		"repository_provider": app.repository_provider or "GitHub",
		"repository_is_private": int(bool(app.repository_is_private)),
		"repository_owner": owner,
		"repository_name": repo,
		"download_mode": "platform_proxy",
		"instructions": (
			"Use the secure download button in your dashboard. "
			"The platform downloads the private repository using a server-side token."
		),
	}
