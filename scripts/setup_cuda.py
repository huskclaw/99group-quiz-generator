"""Install a pinned official llama.cpp CUDA runtime locally; never change model/driver/PATH."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / '.tools/downloads'
DESTINATION = ROOT / '.tools/llama-cuda'
RELEASE = 'b12182'
ASSETS = {
    'llama-b12182-bin-win-cuda-12.4-x64.zip': 'c4b42361400222d3b49a2bcdcd44bebcc0f0a98ccc38e17ee4928ba93c7b2650',
    'cudart-llama-bin-win-cuda-12.4-x64.zip': '8c79a9b226de4b3cacfd1f83d24f962d0773be79f1e7b75c6af4ded7e32ae1d6',
}


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(8 * 1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def obtain(item):
    name, expected = item
    path = DOWNLOADS / name
    if not path.exists() or digest(path) != expected:
        print('Downloading official asset:', name, flush=True)
        url = f'https://github.com/ggml-org/llama.cpp/releases/download/{RELEASE}/{name}'
        with urlopen(url, timeout=60) as response, path.open('wb') as target:
            for block in iter(lambda: response.read(1024 * 1024), b''):
                target.write(block)
    if digest(path) != expected:
        raise RuntimeError('Checksum mismatch: ' + name)
    print('SHA256 verified:', name, flush=True)
    return path


def main():
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    DESTINATION.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        archives = list(pool.map(obtain, ASSETS.items()))
    for path in archives:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                resolved = (DESTINATION / member.filename).resolve()
                if not resolved.is_relative_to(DESTINATION.resolve()):
                    raise RuntimeError('Archive entry leaves the intended runtime directory.')
            archive.extractall(DESTINATION)
    if not (DESTINATION / 'llama-server.exe').is_file():
        raise RuntimeError('Official archive layout changed; expected llama-server.exe at runtime root.')
    (DESTINATION / 'runtime.json').write_text(json.dumps({
        'source': 'https://github.com/ggml-org/llama.cpp/releases/tag/' + RELEASE,
        'release': RELEASE, 'backend': 'CUDA 12.4', 'sha256': ASSETS,
    }, indent=2) + '\n', encoding='utf-8')
    print('Ready. start-llama.ps1 will prefer this isolated CUDA runtime. No model or driver was installed.')


if __name__ == '__main__':
    main()
