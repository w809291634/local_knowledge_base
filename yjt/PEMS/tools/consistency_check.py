# -*- coding: utf-8 -*-
"""Scope-aware, failure-producing consistency checker for PEMS deliverables."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx_ops import convert_doc_to_docx
from release_ops import load_structured, package_text


def fail(errors, message):
    errors.append(message)


def normalize_documents(cfg, base: Path, directory: str | None):
    check = cfg.get("check", {})
    docs = check.get("documents")
    if docs:
        result = []
        for item in docs:
            if isinstance(item, str):
                raw_path = Path(item)
                result.append({"path": str((base / raw_path).resolve()) if not raw_path.is_absolute() else str(raw_path), "scope": "default"})
            else:
                raw_path = Path(item["path"])
                result.append({
                    "path": str((base / raw_path).resolve()) if not raw_path.is_absolute() else str(raw_path),
                    "scope": item.get("scope", "default"),
                    "id": item.get("id"),
                })
        return result
    result = []
    root = Path(directory).resolve() if directory else None
    if root:
        for path in sorted(root.iterdir()):
            if path.suffix.lower() in {".doc", ".docx"}:
                result.append({"path": str(path), "scope": "default"})
    for path in check.get("docs", []):
        result.append({"path": str((base / path).resolve()) if not Path(path).is_absolute() else path, "scope": "default"})
    return result


def text_of(path: Path, temp: Path) -> str:
    if path.suffix.lower() == ".docx":
        return package_text(path)[0]
    converted = temp / (path.stem + ".docx")
    convert_doc_to_docx(str(path), str(converted))
    return package_text(converted)[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--dir", default=None)
    parser.add_argument("--report", default=None)
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    cfg = load_structured(config_path)
    check = cfg.get("check", {})
    docs = normalize_documents(cfg, config_path.parent, args.dir)
    if not docs:
        raise RuntimeError("No documents selected")
    records, errors = [], []
    with tempfile.TemporaryDirectory(prefix="pems_consistency_") as temp_name:
        temp = Path(temp_name)
        for index, item in enumerate(docs):
            path = Path(item["path"])
            if not path.exists():
                fail(errors, f"Document not found: {path}")
                continue
            text = text_of(path, temp / str(index))
            records.append({"id": item.get("id", str(path)), "path": str(path), "scope": item.get("scope", "default"), "text": text})
    pattern = re.compile(check.get("key_pattern", r"[A-Z]{2,3}-\d{5}"))
    for record in records:
        record["keys"] = sorted(set(pattern.findall(record["text"])))
    groups = check.get("scope_groups", [])
    if not groups:
        groups = [{"scope": scope, "mode": "equal"} for scope in sorted({record["scope"] for record in records})]
    for group in groups:
        scope = group["scope"]
        members = [record for record in records if record["scope"] == scope]
        if len(members) < 2:
            continue
        if group.get("mode", "equal") == "equal":
            baseline = set(members[0]["keys"])
            for member in members[1:]:
                current = set(member["keys"])
                if current != baseline:
                    fail(errors, f"Scope {scope}: key set mismatch {members[0]['id']} vs {member['id']}")
        elif group.get("mode") == "subset":
            allowed = set(group.get("expected_keys", []))
            for member in members:
                unexpected = set(member["keys"]) - allowed
                if unexpected:
                    fail(errors, f"Scope {scope}: unexpected key(s) in {member['id']}: {sorted(unexpected)}")
    for rule in check.get("required_text", []):
        target = rule.get("document")
        phrase = rule["text"]
        for record in records:
            if target in (None, "*", record["id"], Path(record["path"]).name) and phrase not in record["text"]:
                fail(errors, f"Required text missing in {record['id']}: {phrase}")
    for rule in check.get("forbidden_text", []):
        target = rule.get("document")
        phrase = rule["text"]
        for record in records:
            if target in (None, "*", record["id"], Path(record["path"]).name) and phrase in record["text"]:
                fail(errors, f"Forbidden text found in {record['id']}: {phrase}")
    for label, terms in check.get("keywords", {}).items():
        for record in records:
            if not any(term in record["text"] for term in terms):
                fail(errors, f"Keyword group {label} missing in {record['id']}")
    report = {"status": "failed" if errors else "ok", "documents": [{k: v for k, v in record.items() if k != "text"} for record in records], "errors": errors}
    if args.report:
        Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
