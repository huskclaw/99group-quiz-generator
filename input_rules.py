"""Fast input checks before inference; topic scope is a user-overridable heuristic."""
import re

MAX_TOPIC_CHARS = 160
MAX_NOTES_CHARS = 3000
OUTSIDE_TOPIC_WARNING = 'This topic appears outside property, employee or company learning. Try a relevant topic, or just continue anyway.'

WORK_TERMS = {
    'property', 'properties', 'properti', 'real estate', 'realestate', 'agent', 'agen',
    'rumah', 'house', 'housing', 'home', 'apartment', 'apartemen', 'ruko', 'tanah',
    'land', 'building', 'bangunan', 'developer', 'pengembang', 'mortgage', 'kpr',
    'rental', 'rent', 'sewa', 'tenant', 'penyewa', 'listing', 'market', 'pasar',
    'valuation', 'valuasi', 'investment', 'investasi', 'sales', 'penjualan', 'marketing',
    'pemasaran', 'lead', 'leads', 'enquiries', 'crm', 'negotiation', 'negosiasi',
    'employee', 'employees', 'karyawan', 'pegawai', 'staff', 'company', 'perusahaan',
    'workplace', 'work', 'kerja', 'team', 'tim', 'leadership', 'kepemimpinan',
    'communication', 'komunikasi', 'collaboration', 'kolaborasi', 'productivity',
    'produktivitas', 'training', 'pelatihan', 'hr', 'sdm', 'onboarding', '99 group',
    '99group', 'rumah123', '99.co', 'cybersecurity', 'phishing', 'security', 'keamanan',
    'customer', 'pelanggan', 'client', 'klien', 'management', 'manajemen', 'ethics', 'etika',
    'spreadsheet', 'excel', 'data literacy', 'literasi data', 'professional', 'profesional',
    'safety', 'keselamatan', 'compliance', 'kepatuhan', 'cuti', 'benefits', 'gaji',
}

OVERRIDE = re.compile(
    r'\b(?:ignore|forget|disregard)\b.{0,45}\b(?:previous|prior|system|instructions?|rules?)\b'
    r'|\b(?:abaikan|lupakan)\b.{0,45}\b(?:instruksi|perintah|aturan|sebelumnya|sistem)\b'
    r'|\b(?:system prompt|prompt sistem|reveal your instructions|jailbreak)\b', re.I)


def readable_text(text: str, label: str) -> None:
    """Reject obvious repetition/keyboard noise, without sending it to the model."""
    if not text.strip():
        return
    words = re.findall(r'[A-Za-zÀ-ž]+', text)
    if not words:
        raise ValueError(f'{label} must contain readable English or Indonesian text.')
    # Ignore URL/path tokens when detecting unusually long unbroken words.
    prose = re.sub(r'https?://\S+', '', text)
    if re.search(r'[A-Za-z]{40,}', prose) or re.search(r'([A-Za-z]{1,10})\1{5,}', prose, re.I):
        raise ValueError(f'{label} looks like repeated or random characters. Please enter meaningful text.')
    if len(words) >= 16 and len({w.casefold() for w in words}) / len(words) < .12:
        raise ValueError(f'{label} contains excessive repetition.')


def check_topic(topic: str) -> str:
    """Return work or outside; direct instruction overrides and obvious noise are errors."""
    readable_text(topic, 'Topic')
    if OVERRIDE.search(topic):
        raise ValueError('Enter a learning topic, not instructions to override the app.')
    lowered = topic.casefold()
    return 'work' if any(re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', lowered) for term in WORK_TERMS) else 'outside'


def enforce_scope(topic: str, allow_off_topic: bool) -> str:
    scope = check_topic(topic)
    if scope == 'outside' and not allow_off_topic:
        raise ValueError(OUTSIDE_TOPIC_WARNING)
    return 'exploratory' if scope == 'outside' else 'work'
