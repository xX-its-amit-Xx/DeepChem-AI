"""AI PR guard for the DeepChem-AI fork.

Reads a pull request as DATA (file list, patches and description from the
GitHub API) and reports anything that must not be merged without the fork
owner's explicit sign-off. It never checks out, imports or runs code from the
pull request, so a malicious PR cannot execute anything through this script.

Standard library only. Exit code 0: no findings. Exit code 1: findings.
Usage: python ai_pr_guard.py <files.json> <pr.json>
  files.json: output of GET /repos/{repo}/pulls/{n}/files (all pages, one list)
  pr.json:    output of GET /repos/{repo}/pulls/{n}
"""
import json
import re
import sys
import unicodedata

BLOCK = 'BLOCK'  # never merge as is
OWNER = 'OWNER'  # only the owner may approve; never auto-merge

PROTECTED_PREFIXES = ('.github/', 'requirements/', 'docker/', 'scripts/',
                      '.cursor/', '.claude/', '.devcontainer/')
PROTECTED_FILES = {
    'setup.py', 'setup.cfg', 'pyproject.toml', 'manifest.in', 'conftest.py',
    'ai_contributing.md', 'claude.md', 'agents.md', 'gemini.md', '.cursorrules',
    '.gitattributes', '.gitmodules', 'codeowners', 'security.md',
    '.pre-commit-config.yaml', 'tox.ini', 'pytest.ini', 'makefile'
}
DEPENDENCY_HINTS = ('requirements', 'environment', 'env_', 'pipfile',
                    'poetry.lock', 'uv.lock', 'conda')
# Formats that can run code when loaded, or that a reviewer cannot read.
UNSAFE_DATA_EXT = ('.pkl', '.pickle', '.joblib', '.pt', '.pth', '.ckpt',
                   '.bin', '.npy', '.npz', '.h5', '.hdf5', '.pb', '.onnx',
                   '.dill', '.sav', '.model', '.safetensors', '.so', '.dll',
                   '.dylib', '.exe', '.pyc', '.pyd', '.whl', '.egg', '.zip',
                   '.tar', '.gz', '.tgz', '.bz2', '.xz', '.7z', '.jar')
DOC_EXT = ('.md', '.rst', '.txt')
DOC_CHECKS = ('new external URL', 'installs or downloads software')
MAX_FILES = 40
MAX_ADDED_LINES = 1500

# Patterns in ADDED lines of code. (regex, level, message)
CODE_PATTERNS = [
    (r'\bpickle\.loads?\(|\bcPickle\b|\bdill\.loads?\(|\bjoblib\.load\(',
     OWNER, 'loads pickled data (can run code on load)'),
    (r'torch\.load\((?![^)]*weights_only\s*=\s*True)', OWNER,
     'torch.load without weights_only=True'),
    (r'weights_only\s*=\s*False', BLOCK, 'turns off safe weight loading'),
    (r'allow_pickle\s*=\s*True', OWNER, 'numpy load with allow_pickle=True'),
    (r'(?<![\w.])(eval|exec|compile|__import__)\s*\(', OWNER,
     'dynamic code execution'),
    (r'\bos\.(system|popen|exec[lv]p?e?|spawn\w*)\s*\(|\bsubprocess\.|\bpty\.',
     OWNER, 'runs an operating-system command'),
    (r'shell\s*=\s*True', OWNER, 'shell=True'),
    (r'\b(base64\.b(64|32|16|85)decode|codecs\.decode|bytes\.fromhex|'
     r'marshal\.loads|zlib\.decompress)\s*\(', OWNER,
     'decodes hidden content (possible obfuscation)'),
    (r'\b(socket\.|urllib\.request|urlopen\(|requests\.(get|post|put)\(|'
     r'httpx\.|aiohttp\.|ftplib\.|paramiko\.|smtplib\.)', OWNER,
     'network access'),
    (r'https?://(?!github\.com/deepchem/|deepchem\.io|deepchemdata\.s3)',
     OWNER, 'new external URL'),
    (r'os\.environ|getenv\(|\.ssh\b|\.aws\b|\.netrc|id_rsa|\.git-credentials'
     r'|GITHUB_TOKEN|secrets\.', OWNER,
     'reads environment, credentials or secrets'),
    (r'yaml\.load\((?![^)]*Safe)|yaml\.unsafe_load', OWNER,
     'unsafe YAML load'),
    (r'\b(ctypes|cffi)\b|\bimportlib\.import_module\(', OWNER,
     'native or dynamic import'),
    (r'pull_request_target|workflow_run|self-hosted', BLOCK,
     'privileged CI trigger or runner'),
    (r'(pip|conda|mamba|npm|uv)\s+install|curl\s[^|]*\|\s*(ba)?sh|wget\s',
     OWNER, 'installs or downloads software'),
    (r'[A-Za-z0-9+/=]{200,}', OWNER, 'long encoded blob'),
]
# Test weakening, checked in added lines of test files.
TEST_WEAKENING = [
    (r'pytest\.mark\.(skip|xfail)|unittest\.skip|pytest\.skip\(|'
     r'pytest\.importorskip', 'skips or expects failure of a test'),
    (r'^\s*assert\s+True\s*(#.*)?$|^\s*pass\s*#', 'empty assertion'),
]
# Text aimed at an AI reviewer (prompt injection), checked in all added text
# and in the PR title and description.
INJECTION = re.compile(
    r'ignore (all |any )?(previous|prior|above|earlier) (instructions|rules)'
    r'|disregard (the |all )?(previous|above|system)'
    r'|you are (now )?(an?|the) (ai|assistant|reviewer|agent)'
    r'|(as an? )?(ai|llm|language model|assistant|reviewer|agent)s?[,:]? '
    r'(must|should|please|you must|need to)'
    r'|system prompt|approve this (pr|pull request|change)'
    r'|auto-?merge|do not (flag|report|mention)|mark (this )?as safe'
    r'|<\s*(system|instructions?|important)\s*>', re.I)
DISCLOSURE = re.compile(
    r'(written|generated|authored|produced)\s+(by|with)\s+(an?\s+)?'
    r'(ai|llm|claude|gpt|gemini|copilot|codex|agent|human)', re.I)


def hidden_chars(text):
    """Return names of invisible or direction-changing characters in text."""
    found = set()
    for ch in text:
        cp = ord(ch)
        if ch in '\n\r\t':
            continue
        cat = unicodedata.category(ch)
        if (cat in ('Cf', 'Co', 'Cn', 'Cc') or 0xE0000 <= cp <= 0xE007F or
                0xFE00 <= cp <= 0xFE0F):
            found.add('U+%04X' % cp)
    return sorted(found)


def mixed_script(name):
    """True if a file name mixes Latin letters with look-alike scripts."""
    scripts = set()
    for ch in name:
        if ch.isalpha():
            n = unicodedata.name(ch, '')
            scripts.add(n.split(' ')[0])
    return len(scripts) > 1 or any(ord(c) > 127 for c in name)


def safe(text, limit=120):
    """Make untrusted text safe to print in a Markdown summary."""
    text = ''.join(c if 32 <= ord(c) < 127 else '?' for c in str(text))
    return re.sub(r'[`|<>\[\]()!*#@]', '?', text)[:limit]


def added_lines(patch):
    return [
        ln[1:] for ln in (patch or '').split('\n')
        if ln.startswith('+') and not ln.startswith('+++')
    ]


def is_test(path):
    base = path.rsplit('/', 1)[-1]
    return '/tests/' in path or '/test/' in path or base.startswith('test_')


def review(files, pr):
    """Return a list of (level, path, message) findings."""
    out = []

    def add(level, path, msg):
        item = (level, safe(path), msg)
        if item not in out:
            out.append(item)

    title = pr.get('title') or ''
    body = pr.get('body') or ''
    if not DISCLOSURE.search(body):
        add(BLOCK, 'description',
            'no authorship line ("Written by an AI agent ..." or by a human)')
    for label, text in (('title', title), ('description', body)):
        if INJECTION.search(text):
            add(BLOCK, label, 'text addressed to an AI reviewer')
        if hidden_chars(text):
            add(BLOCK, label,
                'hidden characters ' + ','.join(hidden_chars(text)[:5]))
    if '<!--' in body:
        add(OWNER, 'description', 'hidden HTML comment in description')

    if len(files) > MAX_FILES:
        add(OWNER, 'size', 'touches %d files (limit %d): split it' %
            (len(files), MAX_FILES))
    total_added = 0
    code_changed = tests_changed = False
    for f in files:
        path = f.get('filename') or ''
        low = path.lower()
        base = low.rsplit('/', 1)[-1]
        status = f.get('status')
        patch = f.get('patch')
        lines = added_lines(patch)
        total_added += f.get('additions') or 0

        if hidden_chars(path) or mixed_script(path) or '..' in path:
            add(BLOCK, path, 'suspicious file name')
        if low.startswith(PROTECTED_PREFIXES) or base in PROTECTED_FILES:
            add(OWNER, path, 'protected path (CI, build, packaging or '
                'agent configuration)')
        if any(h in base for h in DEPENDENCY_HINTS):
            add(OWNER, path, 'dependency file: confirm every new package '
                'exists, is the intended one and is pinned')
        if low.endswith(UNSAFE_DATA_EXT):
            add(BLOCK, path, 'binary, archive, weights or pickled file')
        elif status != 'removed' and patch is None and (
                f.get('additions') or f.get('changes') or
                status in ('added', 'modified', 'changed')):
            add(BLOCK, path, 'no readable diff (binary or too large to '
                'inspect)')
        if status == 'renamed' and f.get('previous_filename'):
            prev = f['previous_filename'].lower()
            if prev.startswith(PROTECTED_PREFIXES):
                add(OWNER, path, 'moved out of a protected path')
        if low.endswith('.ipynb'):
            add(OWNER, path, 'notebook: outputs can hide content')
        if status == 'removed' and is_test(low):
            add(BLOCK, path, 'deletes a test file')

        text = '\n'.join(lines)
        if hidden_chars(text):
            add(BLOCK, path,
                'hidden characters ' + ','.join(hidden_chars(text)[:5]))
        if INJECTION.search(text):
            add(BLOCK, path, 'text addressed to an AI reviewer')
        if any(len(ln) > 1000 for ln in lines):
            add(OWNER, path, 'very long line (possible hidden payload)')
        is_doc = low.endswith(DOC_EXT)
        for rx, level, msg in CODE_PATTERNS:
            # Prose that describes an attack is not the attack: in documents
            # only links and install commands are checked (plus the hidden
            # character and reviewer-directed text checks above).
            if is_doc and msg not in DOC_CHECKS:
                continue
            if re.search(rx, text):
                add(level, path, msg)
        if is_test(low):
            if status != 'removed':
                tests_changed = True
            for rx, msg in TEST_WEAKENING:
                if re.search(rx, text, re.M):
                    add(OWNER, path, msg)
            removed = [
                ln for ln in (patch or '').split('\n')
                if ln.startswith('-') and not ln.startswith('---')
            ]
            lost = sum('assert' in ln for ln in removed)
            gained = sum('assert' in ln for ln in lines)
            if lost > gained:
                add(OWNER, path, 'removes more assertions (%d) than it adds '
                    '(%d)' % (lost, gained))
        elif low.endswith('.py') and low.startswith('deepchem/'):
            code_changed = True

    if total_added > MAX_ADDED_LINES:
        add(OWNER, 'size', 'adds %d lines (limit %d): split it' %
            (total_added, MAX_ADDED_LINES))
    if code_changed and not tests_changed:
        add(BLOCK, 'tests', 'changes library code but adds or changes no '
            'test')
    return out


def render(findings):
    if not findings:
        return ('## AI PR guard: no findings\n\nThis is a screen, not a '
                'review. The owner still reads the change before merging.\n')
    rows = ['## AI PR guard: %d finding(s)' % len(findings), '',
            'BLOCK = must be fixed. OWNER = only the fork owner may approve. '
            'A red result means this change is never merged automatically.',
            '', '| Level | Where | Why |', '|---|---|---|']
    for level, path, msg in sorted(findings):
        rows.append('| %s | `%s` | %s |' % (level, path, msg))
    return '\n'.join(rows) + '\n'


def main(argv):
    with open(argv[1], encoding='utf-8') as fh:
        files = json.load(fh)
    with open(argv[2], encoding='utf-8') as fh:
        pr = json.load(fh)
    # `gh api --paginate --slurp` gives a list of pages.
    if files and isinstance(files[0], list):
        files = [f for page in files for f in page]
    findings = review(files, pr)
    print(render(findings))
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
