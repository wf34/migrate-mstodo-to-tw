#!/usr/bin/env python3
"""Export Microsoft TODO tasks (pffexport output) into human-readable JSON.

For now this is a skeleton: it walks the input directory, finds every task,
and prints the task names. It writes nothing yet.
"""

import re
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterator, List, Optional

from tap import Tap

SUBTASK_MARKER = 'IOpenTypedFacet.Com_Microsoft_Todo_Subtask'


class Args(Tap):
    input_dir: Path   # pffexport output directory to read tasks from
    output_dir: Path  # destination directory for per-task JSON files (must not exist)
    subdir: List[str] = []  # which immediate subdirs of <input_dir>/Tasks to process; empty = all

    def configure(self) -> None:
        self.add_argument('input_dir')
        self.add_argument('output_dir')


@dataclass
class Task:
    title: Optional[str]
    creation_date: Optional[str]
    starred: bool
    is_complete: bool
    completion_date: Optional[str]
    subfolder: Optional[str]
    subtasks: Optional[List[str]]
    comment: Optional[str]


def task_roots(tasks_dir: Path, subdirs: List[str]) -> List[Path]:
    if not subdirs:
        return [tasks_dir]
    roots = []
    for name in subdirs:
        root = tasks_dir / name
        if not root.is_dir():
            sys.exit(f'error: subdir does not exist under {tasks_dir}: {name}')
        roots.append(root)
    return roots


def iter_task_dirs(root: Path) -> Iterator[Path]:
    """Yield every task directory under root (a dir containing a Task.txt)."""
    for task_file in sorted(root.rglob('Task.txt')):
        yield task_file.parent


def field(lines: List[str], key: str) -> Optional[str]:
    prefix = key + ':'
    for line in lines:
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def parse_date(value: Optional[str]) -> Optional[str]:
    # value looks like "Mar 07, 2020 16:46:36.048241600 UTC"; keep the date only.
    if not value:
        return None
    head = ' '.join(value.split()[:3])
    return datetime.strptime(head, '%b %d, %Y').date().isoformat()


def format_subtask(subtask: dict) -> str:
    mark = '✓' if subtask.get('IsCompleted') else '○'
    return f'{mark} {subtask.get("Subject")}'


def extract_subtasks(task_dir: Path) -> Optional[List[str]]:
    # Subtasks live as a UTF-16LE hex dump in ItemValues.txt after SUBTASK_MARKER.
    item_values = task_dir / 'ItemValues.txt'
    if not item_values.is_file():
        return None
    lines = item_values.read_text(encoding='utf-8', errors='replace').splitlines()
    i = 0
    while i < len(lines) and SUBTASK_MARKER not in lines[i]:
        i += 1
    if i >= len(lines):
        return None
    i += 1
    if i < len(lines) and lines[i].startswith('Value:'):
        i += 1
    hex_chars = []
    while i < len(lines) and lines[i].startswith('0x'):
        after = lines[i].split(':', 1)[1]
        hex_chars.append(re.split(r' {3,}', after, maxsplit=1)[0].replace(' ', ''))
        i += 1
    subtasks_str = bytes.fromhex(''.join(hex_chars)).decode('utf-16-le')
    values = json.loads(subtasks_str)['Values']
    if not values:
        return None
    values.sort(key=lambda s: s.get('CreatedDateTime') or '')
    return [format_subtask(s) for s in values]


class _HtmlText(HTMLParser):
    _BLOCKS = {'p', 'div', 'br', 'li', 'tr', 'h1', 'h2', 'h3'}

    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(re.sub(r'\s+', ' ', data))

    def handle_starttag(self, tag, attrs) -> None:
        if tag in self._BLOCKS:
            self.parts.append('\n')

    def handle_endtag(self, tag) -> None:
        if tag in self._BLOCKS:
            self.parts.append('\n')


def html_to_text(html: str) -> str:
    parser = _HtmlText()
    parser.feed(html)
    lines = [re.sub(r' +', ' ', ln).strip() for ln in ''.join(parser.parts).split('\n')]
    out: List[str] = []
    for ln in lines:
        if ln or (out and out[-1]):
            out.append(ln)
    return '\n'.join(out).strip()


def extract_comment(task_dir: Path) -> Optional[str]:
    # Task comments are stored as HTML in Message.html; keep the visible text only.
    message = task_dir / 'Message.html'
    if not message.is_file():
        return None
    return html_to_text(message.read_text(encoding='utf-8', errors='replace')) or None


def parse_task(task_dir: Path, tasks_dir: Path) -> Task:
    lines = (task_dir / 'Task.txt').read_text(encoding='utf-8', errors='replace').splitlines()
    is_complete = field(lines, 'Is complete') == 'yes'
    rel = task_dir.parent.relative_to(tasks_dir)
    return Task(
        title=field(lines, 'Subject'),
        creation_date=parse_date(field(lines, 'Creation time')),
        starred=field(lines, 'Importance') == 'High',
        is_complete=is_complete,
        completion_date=parse_date(field(lines, 'Modification time')) if is_complete else None,
        subfolder=None if rel == Path('.') else str(rel),
        subtasks=extract_subtasks(task_dir),
        comment=extract_comment(task_dir),
    )


def main() -> None:
    args = Args().parse_args()

    if not args.input_dir.is_dir():
        sys.exit(f'error: input dir does not exist or is not a directory: {args.input_dir}')

    if args.output_dir.exists():
        sys.exit(f'error: output dir already exists, refusing to overwrite: {args.output_dir}')

    tasks_dir = args.input_dir / 'Tasks'
    if not tasks_dir.is_dir():
        sys.exit(f'error: no Tasks dir under input dir: {tasks_dir}')

    for root in task_roots(tasks_dir, args.subdir):
        for task_dir in iter_task_dirs(root):
            task = parse_task(task_dir, tasks_dir)
            mark_ = '✓' if task.is_complete else '○'
            print(mark_ + ' ' + task.title if task.title is not None else f'<no subject> ({task_dir})')
            print(str(task.subtasks) + '\n' if task.subtasks is not None else f'<no subtask>\n')
            if task.comment is not None:
                print('comment: ' + task.comment + '\n')


if __name__ == '__main__':
    main()
