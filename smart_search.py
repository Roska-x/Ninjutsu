#!/usr/bin/env python3
"""
SmartSearch - simple regex-based search over text files in a directory.

Designed to be used both as a standalone utility and as a library from
the MasterSecurityTool menu to post-process JSON / text results.
"""

from __future__ import annotations

import os
import re
import fnmatch
from dataclasses import dataclass
from typing import Dict, List, Iterable, Optional, Any


@dataclass
class MatchContext:
    file: str
    path: str
    line_number: int
    match_text: str
    context_before: List[str]
    context_line: str
    context_after: List[str]


@dataclass
class FileMatches:
    file: str
    path: str
    match_count: int
    matches: List[MatchContext]


class SmartSearch:
    """
    Simple regex-based search across a directory tree.

    This class is intentionally independent from any input() / print()
    logic so it can be reused from both CLI and interactive menus.
    """

    def __init__(
        self,
        dir_path: str,
        file_patterns: Optional[List[str]] = None,
        recursive: bool = True,
        max_file_size_mb: int = 5,
        ignore_binary: bool = True,
    ) -> None:
        self.dir_path = os.path.abspath(dir_path)
        self.file_patterns = file_patterns or []
        self.recursive = recursive
        self.max_file_size_mb = max_file_size_mb
        self.ignore_binary = ignore_binary

    def _iter_files(self) -> Iterable[str]:
        """
        Yield full paths of files that match the configuration.
        """
        if not os.path.isdir(self.dir_path):
            return

        max_bytes = self.max_file_size_mb * 1024 * 1024 if self.max_file_size_mb > 0 else None

        if self.recursive:
            walker: Iterable[Any] = os.walk(self.dir_path)
            for root, _dirs, files in walker:
                for name in files:
                    full_path = os.path.join(root, name)
                    if not self._matches_patterns(name):
                        continue
                    if max_bytes is not None and not self._within_size_limit(full_path, max_bytes):
                        continue
                    if self.ignore_binary and self._looks_binary(full_path):
                        continue
                    yield full_path
        else:
            try:
                for name in os.listdir(self.dir_path):
                    full_path = os.path.join(self.dir_path, name)
                    if not os.path.isfile(full_path):
                        continue
                    if not self._matches_patterns(name):
                        continue
                    if max_bytes is not None and not self._within_size_limit(full_path, max_bytes):
                        continue
                    if self.ignore_binary and self._looks_binary(full_path):
                        continue
                    yield full_path
            except OSError:
                return

    def _matches_patterns(self, name: str) -> bool:
        """
        Return True if the filename matches configured glob patterns.

        If no patterns are configured, everything is accepted.
        """
        if not self.file_patterns:
            return True
        for pattern in self.file_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    @staticmethod
    def _within_size_limit(path: str, max_bytes: int) -> bool:
        try:
            return os.path.getsize(path) <= max_bytes
        except OSError:
            return False

    @staticmethod
    def _looks_binary(path: str, sample_size: int = 1024) -> bool:
        """
        Heuristic to decide if a file is binary.
        """
        try:
            with open(path, "rb") as f:
                chunk = f.read(sample_size)
        except OSError:
            return True

        if b"\x00" in chunk:
            return True

        # Count non-text bytes
        text_chars = bytes(range(32, 127)) + b"\n\r\t\b"
        nontext = chunk.translate(None, text_chars)
        # If more than 30% of chars are non-text, assume binary
        return len(nontext) > 0 and (len(nontext) / max(len(chunk), 1)) > 0.30

    @staticmethod
    def _read_text_file(path: str) -> Optional[str]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return None

    def regex_search(
        self,
        pattern: str,
        case_sensitive: bool = False,
        multiline: bool = True,
        context_lines: int = 2,
        max_matches_per_file: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Execute a regex search across all selected files.

        Returns a structure:

        {
            "summary": {...},
            "matches": [FileMatches, ...]  # serializable dicts
        }
        """
        if not pattern:
            raise ValueError("Regex pattern must not be empty")

        flags = 0
        if not case_sensitive:
            flags |= re.IGNORECASE
        if multiline:
            flags |= re.MULTILINE

        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regular expression: {e}") from e

        all_file_matches: List[FileMatches] = []
        total_files_scanned = 0
        total_files_with_matches = 0
        total_matches = 0

        for path in self._iter_files():
            total_files_scanned += 1
            text = self._read_text_file(path)
            if text is None:
                continue

            lines = text.splitlines()
            file_matches: List[MatchContext] = []

            for idx, line in enumerate(lines, start=1):
                for m in regex.finditer(line):
                    before_start = max(0, idx - 1 - context_lines)
                    before = lines[before_start : idx - 1]
                    after_end = min(len(lines), idx - 1 + 1 + context_lines)
                    after = lines[idx : after_end]

                    file_matches.append(
                        MatchContext(
                            file=os.path.basename(path),
                            path=path,
                            line_number=idx,
                            match_text=m.group(0),
                            context_before=before,
                            context_line=line,
                            context_after=after,
                        )
                    )

                    if max_matches_per_file is not None and len(file_matches) >= max_matches_per_file:
                        break
                if max_matches_per_file is not None and len(file_matches) >= max_matches_per_file:
                    break

            if file_matches:
                total_files_with_matches += 1
                total_matches += len(file_matches)
                all_file_matches.append(
                    FileMatches(
                        file=os.path.basename(path),
                        path=path,
                        match_count=len(file_matches),
                        matches=file_matches,
                    )
                )

        return {
            "summary": {
                "total_files_scanned": total_files_scanned,
                "total_files_with_matches": total_files_with_matches,
                "total_matches": total_matches,
            },
            "matches": [self._file_matches_to_dict(fm) for fm in all_file_matches],
        }

    @staticmethod
    def _file_matches_to_dict(fm: FileMatches) -> Dict[str, Any]:
        return {
            "file": fm.file,
            "path": fm.path,
            "match_count": fm.match_count,
            "matches": [
                {
                    "file": m.file,
                    "path": m.path,
                    "line_number": m.line_number,
                    "match_text": m.match_text,
                    "context_before": m.context_before,
                    "context_line": m.context_line,
                    "context_after": m.context_after,
                }
                for m in fm.matches
            ],
        }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Regex-based SmartSearch over text files in a directory."
    )
    parser.add_argument("path", help="Base directory for the search.")
    parser.add_argument(
        "-r",
        "--regex",
        required=True,
        help="Regular expression pattern to search for.",
    )
    parser.add_argument(
        "-i",
        "--case-sensitive",
        action="store_true",
        help="Make the search case-sensitive (default is case-insensitive).",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        action="append",
        help="Glob pattern for files to include (can be used multiple times). "
        "If omitted, all files are considered.",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="Do not search subdirectories.",
    )
    parser.add_argument(
        "--max-size-mb",
        type=int,
        default=5,
        help="Maximum file size in MB to scan (default: 5).",
    )
    parser.add_argument(
        "--context-lines",
        type=int,
        default=2,
        help="Number of context lines before/after each match (default: 2).",
    )
    parser.add_argument(
        "--max-matches-per-file",
        type=int,
        default=None,
        help="Maximum matches per file (default: unlimited).",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path to save results as JSON.",
    )

    args = parser.parse_args()

    searcher = SmartSearch(
        dir_path=args.path,
        file_patterns=args.pattern,
        recursive=not args.no_recursive,
        max_file_size_mb=args.max_size_mb,
        ignore_binary=True,
    )

    results = searcher.regex_search(
        pattern=args.regex,
        case_sensitive=args.case_sensitive,
        multiline=True,
        context_lines=args.context_lines,
        max_matches_per_file=args.max_matches_per_file,
    )

    print(
        f"Scanned {results['summary']['total_files_scanned']} files, "
        f"{results['summary']['total_files_with_matches']} with matches, "
        f"{results['summary']['total_matches']} total matches."
    )

    if args.json_output:
        try:
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"Results saved to {args.json_output}")
        except OSError as e:
            print(f"Could not save JSON output: {e}")