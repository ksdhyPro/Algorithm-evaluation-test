import json
import os
import base64
from datetime import datetime

from config import BASE_DIR
from utils import load_users, normalize_rel_path, read_results_file


def contest_paths(contest_id):
    contest_dir = os.path.join(BASE_DIR, contest_id)
    evaluation_dir = os.path.join(contest_dir, 'evaluation')
    submissions_root = os.path.join(evaluation_dir, 'submissions')
    submissions_json = os.path.join(evaluation_dir, 'submissions.json')
    return contest_dir, evaluation_dir, submissions_root, submissions_json


def resolve_submission_dir(contest_id, submission_id=None, participant_id=None, storage_path=None):
    contest_dir, evaluation_dir, submissions_root, _ = contest_paths(contest_id)
    candidates = []

    if storage_path:
        candidates.append(os.path.join(contest_dir, storage_path))
    if submission_id:
        candidates.append(os.path.join(submissions_root, f'submission_{submission_id}'))
    if submission_id and participant_id:
        candidates.append(os.path.join(evaluation_dir, participant_id, f'submission_{submission_id}'))

    for cand in candidates:
        if cand and os.path.exists(cand):
            return cand
    return None


def generate_contest_id():
    prefix = datetime.now().strftime('AE%Y%m%d')
    for seq in range(1000):
        contest_id = f"{prefix}-{seq:03d}"
        contest_dir = os.path.join(BASE_DIR, contest_id)
        if not os.path.exists(contest_dir):
            return contest_id
    raise RuntimeError('无法生成唯一的评测 ID，请稍后再试')


def get_all_contests():
    contests = []
    if not os.path.exists(BASE_DIR):
        return contests

    users = load_users()
    user_map = {u.get('id'): u.get('name', u.get('id')) for u in users}

    for item in os.listdir(BASE_DIR):
        item_path = os.path.join(BASE_DIR, item)
        if not os.path.isdir(item_path):
            continue
        info_dir = os.path.join(item_path, 'info')
        info_file = os.path.join(info_dir, 'info.json')
        if not os.path.exists(info_file):
            continue
        try:
            with open(info_file, 'r', encoding='utf-8') as f:
                info = json.load(f)
                info['id'] = item
                owner_id = info.get('owner_id') or 'system'
                info['owner_id'] = owner_id
                info['owner_name'] = info.get('owner_name') or user_map.get(owner_id, owner_id)

                # 读取封面图并转换为 Base64
                cover_image_path = os.path.join(info_dir, info.get('cover_image', ''))
                if os.path.exists(cover_image_path):
                    with open(cover_image_path, 'rb') as img_file:
                        info['cover_image'] = f"data:image/jpeg;base64,{base64.b64encode(img_file.read()).decode('utf-8')}"
                else:
                    info['cover_image'] = None

                contests.append(info)
        except Exception:
            continue

    contests.sort(key=lambda x: x['id'], reverse=True)
    return contests


def get_contest_submissions(contest_id):
    contest_dir, evaluation_dir, _, submissions_json = contest_paths(contest_id)
    if not os.path.exists(evaluation_dir):
        return []

    users = load_users()
    user_map = {u.get('id'): u.get('name', u.get('id')) for u in users}
    submissions = []

    submissions_data = None
    if os.path.exists(submissions_json):
        try:
            with open(submissions_json, 'r', encoding='utf-8') as f:
                submissions_data = json.load(f)
        except Exception:
            submissions_data = None

    if submissions_data:
        for entry in submissions_data.get('submissions', []):
            participant_id = entry.get('participant_id') or 'default'
            submission_id = entry.get('submission_id')
            submission_time = entry.get('timestamp')
            status_code = entry.get('status_code')
            status_desc = entry.get('status_desc') or ''
            organizer_results = entry.get('organizer_results')
            participant_output_results = entry.get('participant_output_results')
            participant_logs_path = None
            organizer_logs_path = None
            participant_output_path = entry.get('output_path')
            if participant_output_path:
                participant_output_path = participant_output_path.replace('\\', '/')

            submission_dir = resolve_submission_dir(
                contest_id=contest_id,
                submission_id=submission_id,
                participant_id=participant_id,
                storage_path=entry.get('storage_path')
            )

            participant_logs = None
            organizer_logs = None

            if submission_dir and os.path.exists(submission_dir):
                try:
                    plog = os.path.join(submission_dir, 'participant_logs.txt')
                    if os.path.exists(plog):
                        with open(plog, 'r', encoding='utf-8') as pf:
                            participant_logs = pf.read()
                            participant_logs_path = normalize_rel_path(plog, contest_dir)
                except Exception:
                    participant_logs = None

                try:
                    olog = os.path.join(submission_dir, 'organizer_logs.txt')
                    if os.path.exists(olog):
                        with open(olog, 'r', encoding='utf-8') as of:
                            organizer_logs = of.read()
                            organizer_logs_path = normalize_rel_path(olog, contest_dir)
                except Exception:
                    organizer_logs = None

                try:
                    orjson = os.path.join(submission_dir, 'organizer_results.json')
                    if os.path.exists(orjson) and organizer_results is None:
                        with open(orjson, 'r', encoding='utf-8') as orf:
                            organizer_results = json.load(orf)
                except Exception:
                    pass

                output_dir = os.path.join(submission_dir, 'output')
                if not participant_output_path and os.path.exists(output_dir):
                    participant_output_path = normalize_rel_path(output_dir, contest_dir)
                if not participant_output_results and os.path.exists(output_dir):
                    results_json = os.path.join(output_dir, 'results.json')
                    participant_output_results = read_results_file(results_json)

            participant_name = user_map.get(participant_id, participant_id)

            submissions.append({
                'participant_id': participant_id,
                'participant_name': participant_name,
                'submission_id': submission_id,
                'submission_time': submission_time,
                'status_code': status_code,
                'status_desc': status_desc,
                'participant_logs': participant_logs,
                'organizer_logs': organizer_logs,
                'organizer_results': organizer_results,
                'participant_logs_path': participant_logs_path,
                'organizer_logs_path': organizer_logs_path,
                'participant_output_path': participant_output_path,
                'participant_output_results': participant_output_results
            })
    else:
        for participant_id in os.listdir(evaluation_dir):
            participant_dir = os.path.join(evaluation_dir, participant_id)
            if not os.path.isdir(participant_dir):
                continue
            submissions_json_path = os.path.join(participant_dir, 'submissions.json')
            if not os.path.exists(submissions_json_path):
                continue
            try:
                with open(submissions_json_path, 'r', encoding='utf-8') as f:
                    old_sub_data = json.load(f)
            except Exception:
                continue
            subs = old_sub_data.get('submissions') or []
            if not subs:
                continue

            latest_submission = subs[-1]
            submission_id = latest_submission.get('submission_id')
            submission_time = latest_submission.get('timestamp')
            status_code = latest_submission.get('status_code')
            status_desc = latest_submission.get('status_desc') or ''
            organizer_results = latest_submission.get('organizer_results')
            participant_output_results = None
            participant_logs_path = None
            organizer_logs_path = None
            participant_output_path = None

            submission_dir = os.path.join(participant_dir, f'submission_{submission_id}') if submission_id else None
            participant_logs = None
            organizer_logs = None

            if submission_dir and os.path.exists(submission_dir):
                try:
                    plog = os.path.join(submission_dir, 'participant_logs.txt')
                    if os.path.exists(plog):
                        with open(plog, 'r', encoding='utf-8') as pf:
                            participant_logs = pf.read()
                            participant_logs_path = normalize_rel_path(plog, contest_dir)
                except Exception:
                    participant_logs = None

                try:
                    olog = os.path.join(submission_dir, 'organizer_logs.txt')
                    if os.path.exists(olog):
                        with open(olog, 'r', encoding='utf-8') as of:
                            organizer_logs = of.read()
                            organizer_logs_path = normalize_rel_path(olog, contest_dir)
                except Exception:
                    organizer_logs = None

                try:
                    orjson = os.path.join(submission_dir, 'organizer_results.json')
                    if os.path.exists(orjson) and organizer_results is None:
                        with open(orjson, 'r', encoding='utf-8') as orf:
                            organizer_results = json.load(orf)
                except Exception:
                    pass

                output_dir = os.path.join(submission_dir, 'output')
                if os.path.exists(output_dir):
                    participant_output_path = normalize_rel_path(output_dir, contest_dir)
                    results_json = os.path.join(output_dir, 'results.json')
                    participant_output_results = read_results_file(results_json)

            participant_name = user_map.get(participant_id, participant_id)

            submissions.append({
                'participant_id': participant_id,
                'participant_name': participant_name,
                'submission_id': submission_id,
                'submission_time': submission_time,
                'status_code': status_code,
                'status_desc': status_desc,
                'participant_logs': participant_logs,
                'organizer_logs': organizer_logs,
                'organizer_results': organizer_results,
                'participant_logs_path': participant_logs_path,
                'organizer_logs_path': organizer_logs_path,
                'participant_output_path': participant_output_path,
                'participant_output_results': participant_output_results
            })

    submissions.sort(key=lambda x: x.get('submission_time', ''), reverse=True)
    return submissions

