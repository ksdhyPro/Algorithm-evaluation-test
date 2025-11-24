import json
import os

from services.contests import contest_paths, resolve_submission_dir
from utils import normalize_rel_path, read_results_file, load_users


def append_submission_record(contest_id, record):
    _, _, _, submissions_json = contest_paths(contest_id)
    data = {'submissions': []}
    if os.path.exists(submissions_json):
        try:
            with open(submissions_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'submissions': []}

    data.setdefault('submissions', []).append(record)
    with open(submissions_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_submission_status(contest_id, submission_id, status_code, status_desc):
    _, _, _, submissions_json = contest_paths(contest_id)
    if not os.path.exists(submissions_json):
        return
    try:
        with open(submissions_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return

    updated = False
    for sub in data.get('submissions', []):
        if sub.get('submission_id') == submission_id:
            sub['status_code'] = status_code
            sub['status_desc'] = status_desc
            updated = True
            break

    if updated:
        with open(submissions_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

