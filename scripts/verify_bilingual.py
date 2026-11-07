"""Real v2 checks with public synthetic inputs; never reads browser session data."""
import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import httpx
from generator import generate_quiz
from quiz import GeneratedQuiz, results_json
from settings import Settings

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--case', choices=['indonesian', 'long-notes', 'english', 'fun'], default='indonesian')
args = parser.parse_args()
notes = (ROOT/'examples/long-training-briefing.txt').read_text(encoding='utf-8') if args.case == 'long-notes' else ''
topic, count = {
    'indonesian': ('Keterampilan agen properti: mencocokkan rumah dengan syarat pembeli dan menghitung rasio 20 kunjungan dari 80 calon pembeli', 2),
    'long-notes': ('Property market updates in Jakarta', 5),
    'english': ('Matching property listings to explicit buyer constraints', 2),
    'fun': ('give me cookie recipe', 1),
}[args.case]
trace = []
def record(response):
    if not response.request.url.path.endswith('/chat/completions'):
        return
    response.read()
    body = response.json()
    entry = {'http_status': response.status_code}
    if body.get('choices'):
        choice = body['choices'][0]
        entry.update(finish_reason=choice.get('finish_reason'), content=choice['message'].get('content'))
    trace.append(entry)
    print('Inference',len(trace),entry['http_status'],entry.get('finish_reason'),flush=True)
    if entry.get('content'):
        obj = json.loads(entry['content'])
        if 'issues' in obj:
            print('Review:', json.dumps(obj,ensure_ascii=False),flush=True)

settings = Settings.from_env()
started = time.monotonic()
try:
    with httpx.Client(timeout=httpx.Timeout(settings.timeout,connect=3),trust_env=False,
                      event_hooks={'response':[record]}) as client:
        session = generate_quiz(topic,count,notes,settings,client=client,
                                allow_off_topic=args.case == 'fun',progress=lambda s:print(s,flush=True))
    payload = json.loads(results_json(session,[q.correct_index for q in session.quiz.questions]))
    candidate_entry = next(e for e in reversed(trace) if 'questions' in json.loads(e.get('content','{}')))
    candidate = GeneratedQuiz.model_validate_json(candidate_entry['content']).to_quiz()
    position = trace.index(candidate_entry)
    reviews = [json.loads(e['content']) for e in trace[position+1:] if e.get('content')]
    assert len(reviews) == (count+1)//2 and all(r['approved'] and not r['issues'] for r in reviews)
    payload['verification'] = {'elapsed_seconds':round(time.monotonic()-started,2),
        'api_completions':len(trace),'notes_characters':len(notes),
        'reviewed_candidate':candidate.model_dump(),'quality_reviews':reviews,
        'audit_option_order':'Each audit uses zero-based question/option indices in its pre-shuffle batch of up to two questions.',
        'answer_selection':'Correct keys selected programmatically; not an employee attempt.'}
    output=ROOT/'examples'/('bilingual-'+args.case+'.json')
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('PASS:',output.name,payload['verification']['elapsed_seconds'],'seconds',flush=True)
finally:
    out=ROOT/'artifacts'/('bilingual-'+args.case+'-trace.json')
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(trace,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
