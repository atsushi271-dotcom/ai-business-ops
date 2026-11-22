#!/usr/bin/env python3
"""週次レビューを生成する。既存の履歴は上書きしない。"""
import argparse
from datetime import date
from pathlib import Path


def create(root: Path, day: date) -> tuple[Path, bool]:
    year, week, _ = day.isocalendar()
    label = f'{year}-W{week:02d}'
    folder = root / 'reviews'
    text = (folder / '_template.md').read_text(encoding='utf-8')
    target = folder / f'{label}.md'
    try:
        with target.open('x', encoding='utf-8') as stream:
            stream.write(text.replace('{{WEEK}}', label).replace('{{DATE}}', day.isoformat()))
    except FileExistsError:
        return target, False
    return target, True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    target, created = create(Path(__file__).resolve().parents[1], args.date)
    print(f'{"created" if created else "exists"}: {target.name}')


if __name__ == '__main__':
    main()
