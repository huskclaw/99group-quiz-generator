"""Optional synthetic long-input probe; does not read employee data or app notes."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from settings import Settings

settings = Settings.from_env()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rounds', type=int, choices=range(1, 7), default=1)
parser.add_argument('--runtime-label', default='Not specified; consult the launcher output')
args = parser.parse_args()
root_url = settings.base_url.removesuffix('/v1')
records = []
with httpx.Client(timeout=httpx.Timeout(45, connect=3), trust_env=False) as client:
    for repetitions in (100, 200, 300) * args.rounds:
        content = ('A hypothetical property report records asking prices and enquiries, not completed sales. ' * repetitions)
        messages = [{'role': 'system', 'content': 'Read the supplied training data. Return only the JSON object {"ok":true}.'},
                    {'role': 'user', 'content': content + '\nConfirm you received this synthetic data using {"ok":true}.'}]
        rendered = client.post(root_url + '/apply-template', json={'messages': messages, 'chat_template_kwargs': {'enable_thinking': False}})
        rendered.raise_for_status()
        tokenized = client.post(root_url + '/tokenize', json={'content': rendered.json()['prompt']})
        tokenized.raise_for_status()
        count = len(tokenized.json()['tokens'])
        print('Probing', count, 'input tokens', flush=True)
        started = time.monotonic()
        response = client.post(settings.base_url + '/chat/completions', json={
            'model': settings.model, 'messages': messages, 'max_tokens': 128,
            'temperature': 0, 'cache_prompt': False, 'chat_template_kwargs': {'enable_thinking': False},
            'response_format': {'type': 'json_schema', 'json_schema': {'name': 'probe', 'strict': True,
                'schema': {'type': 'object', 'properties': {'ok': {'type': 'boolean'}}, 'required': ['ok'], 'additionalProperties': False}}}})
        response.raise_for_status()
        choice = response.json()['choices'][0]
        assert json.loads(choice['message']['content']) == {'ok': True}
        records.append({'input_tokens': count, 'elapsed_seconds': round(time.monotonic()-started, 2), 'finish_reason': choice['finish_reason']})
        print('PASS', records[-1], flush=True)
        (ROOT/'examples/context-probe.json').write_text(json.dumps({'runtime_label': args.runtime_label,
            'configuration': '8192 context, full SWA cache; synthetic inputs only',
            'synthetic_requests': records}, indent=2)+'\n', encoding='utf-8')
