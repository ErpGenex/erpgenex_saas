from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict:
	with path.open(encoding="utf-8") as handle:
		return json.load(handle)


def _collect_records(apps_root: Path, folder: str) -> set[str]:
	records: set[str] = set()
	for path in apps_root.glob(f"*/**/{folder}/*/*.json"):
		try:
			data = _load_json(path)
		except Exception:
			continue
		if not isinstance(data, dict):
			continue
		name = data.get("name")
		if name:
			records.add(name)
	return records


def _workspace_paths(apps_root: Path) -> list[Path]:
	paths = []
	for path in apps_root.glob("*/**/workspace/*/*.json"):
		if "__pycache__" not in path.parts:
			paths.append(path)
	return sorted(paths)


def audit_workspaces(apps_root: str | Path = "apps") -> dict:
	apps_root = Path(apps_root)
	doctypes = _collect_records(apps_root, "doctype")
	reports = _collect_records(apps_root, "report")
	workspaces = []
	totals = {
		"workspaces": 0,
		"links": 0,
		"hidden_workspaces": 0,
		"hidden_links": 0,
		"missing_targets": 0,
		"invalid_json": 0,
	}

	for path in _workspace_paths(apps_root):
		try:
			data = _load_json(path)
		except Exception as exc:
			totals["invalid_json"] += 1
			workspaces.append({"path": str(path), "error": str(exc)})
			continue

		if not isinstance(data, dict):
			totals["invalid_json"] += 1
			workspaces.append({"path": str(path), "error": "JSON root is not an object"})
			continue

		workspace = {
			"path": str(path),
			"name": data.get("name") or data.get("label"),
			"module": data.get("module"),
			"public": int(data.get("public") or 0),
			"is_hidden": int(data.get("is_hidden") or 0),
			"hidden_links": [],
			"missing_targets": [],
			"links": len(data.get("links") or []),
		}
		totals["workspaces"] += 1
		totals["links"] += workspace["links"]
		if workspace["is_hidden"]:
			totals["hidden_workspaces"] += 1

		for link in data.get("links") or []:
			if int(link.get("hidden") or 0):
				totals["hidden_links"] += 1
				workspace["hidden_links"].append(link.get("label") or link.get("link_to"))

			link_to = link.get("link_to")
			link_type = link.get("link_type")
			if not link_to or link.get("type") != "Link":
				continue
			if link_type == "DocType" and link_to not in doctypes:
				totals["missing_targets"] += 1
				workspace["missing_targets"].append({"type": "DocType", "target": link_to})
			elif link_type == "Report" and link_to not in reports:
				totals["missing_targets"] += 1
				workspace["missing_targets"].append({"type": "Report", "target": link_to})

		if workspace["is_hidden"] or workspace["hidden_links"] or workspace["missing_targets"]:
			workspaces.append(workspace)

	return {"totals": totals, "workspaces_with_findings": workspaces}


def main() -> None:
	parser = argparse.ArgumentParser(description="Audit Workspace visibility and link targets.")
	parser.add_argument("--apps-root", default="apps")
	parser.add_argument("--json", action="store_true", help="Print full JSON report.")
	args = parser.parse_args()

	report = audit_workspaces(args.apps_root)
	if args.json:
		print(json.dumps(report, ensure_ascii=False, indent=2))
		return

	totals = report["totals"]
	print(
		"Workspace audit: "
		f"{totals['workspaces']} workspaces, "
		f"{totals['links']} links, "
		f"{totals['hidden_workspaces']} hidden workspaces, "
		f"{totals['hidden_links']} hidden links, "
		f"{totals['missing_targets']} missing targets, "
		f"{totals['invalid_json']} invalid JSON files"
	)
	for workspace in report["workspaces_with_findings"]:
		print(f"- {workspace.get('name') or workspace.get('path')}: {workspace.get('path')}")
		if workspace.get("error"):
			print(f"  invalid_json: {workspace['error']}")
		if workspace.get("is_hidden"):
			print("  hidden workspace")
		for label in workspace.get("hidden_links") or []:
			print(f"  hidden link: {label}")
		for missing in workspace.get("missing_targets") or []:
			print(f"  missing {missing['type']}: {missing['target']}")


if __name__ == "__main__":
	main()
