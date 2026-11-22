#!/usr/bin/env python3
"""公開用に再構成したMarkdown運用検査。業務上の事実を検証するものではない。"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re


def check(root: Path, as_of: date) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    root = root.resolve()
    files = sorted((root / 'knowledge').glob('*.md'))
    if not files:
        return ['knowledge/*.md がありません'], []
    ids: dict[str, str] = {}
    for path in files:
        name = path.relative_to(root).as_posix()
        text = path.read_text(encoding='utf-8')
        match = re.search(r'^\|\s*最終確認\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|', text, re.M)
        if not match:
            errors.append(f'{name}: 最終確認日がありません')
        else:
            try:
                confirmed = date.fromisoformat(match.group(1))
                if confirmed > as_of:
                    errors.append(f'{name}: 最終確認日が検査日より未来です')
                elif (as_of - confirmed).days > 30:
                    warnings.append(f'{name}: 最終確認日から30日を超えています')
            except ValueError:
                errors.append(f'{name}: 最終確認日が不正です')
        columns = None
        for number, line in enumerate(text.splitlines(), 1):
            if line.startswith('|'):
                count = len(re.split(r'(?<!\\)\|', line))
                if columns is not None and count != columns:
                    errors.append(f'{name}:{number}: 表の列数が一致しません')
                columns = count
            else:
                columns = None
            if '~~' in line:
                errors.append(f'{name}:{number}: 現在の情報に取り消し線があります')
            if path.name in ('05_open_issues.md', '08_ledger.md'):
                item = re.match(r'^\|\s*([A-Z]+-\d+)\s*\|', line)
                if item:
                    identifier = item.group(1)
                    if identifier in ids:
                        errors.append(f'{name}:{number}: ID重複 {identifier} ({ids[identifier]})')
                    ids[identifier] = f'{name}:{number}'
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', link) or link.startswith('#'):
                continue
            target = (path.parent / link.split('#', 1)[0]).resolve()
            if not target.is_relative_to(root):
                errors.append(f'{name}: リンクがリポジトリの外を指しています')
            elif not target.exists():
                errors.append(f'{name}: リンク先がありません: {link}')
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--as-of', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    errors, warnings = check(args.root, args.as_of)
    for message in warnings:
        print('WARN', message)
    for message in errors:
        print('ERROR', message)
    print(f'{len(errors)} errors, {len(warnings)} warnings')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
