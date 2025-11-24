import os
import json
import time
from worker import run_worker
from task_queue import dequeue_task
from services.submissions import update_submission_status


def run_queue_worker():
    print('[Queue Runner] started')
    while True:
        try:
            task = dequeue_task()
            if task:
                process_task(task)
            else:
                time.sleep(1)
        except Exception as e:
            print(f'[Queue Runner] error: {e}')
            time.sleep(2)


def process_task(task):
    submission_id = task.get('submission_id')
    contest_id = task.get('contest_id')
    print(f'[Queue Runner] processing task {submission_id}')

    update_submission_status(contest_id, submission_id, 'RUNNING', '评测中...')

    result = None
    try:
        result = run_worker(
            image_tar_path=task['image_tar_path'],
            output_dir=task['output_dir'],
            input_dir=task['input_dir'],
            contest_dir=task['contest_dir'],
            timeout=300,
            participant_id=task.get('participant_id')
        )
    except Exception as e:
        result = {'code': 3, 'desc': f'执行异常: {str(e)}'}

    save_logs_and_results(task, result)

    status_code = result.get('code', 3)
    status_desc = result.get('desc', '执行出错')
    update_submission_status(contest_id, submission_id, status_code, status_desc)

    print(f'[Queue Runner] finished task {submission_id} -> {status_code}')


def save_logs_and_results(task, result):
    submission_dir = task['submission_dir']
    try:
        participant_logs_path = os.path.join(submission_dir, 'participant_logs.txt')
        with open(participant_logs_path, 'w', encoding='utf-8') as f:
            f.write(result.get('participant_logs', ''))

        if result.get('organizer_logs'):
            organizer_logs_path = os.path.join(submission_dir, 'organizer_logs.txt')
            with open(organizer_logs_path, 'w', encoding='utf-8') as f:
                f.write(result.get('organizer_logs', ''))

        if result.get('organizer_results'):
            organizer_results_path = os.path.join(submission_dir, 'organizer_results.json')
            with open(organizer_results_path, 'w', encoding='utf-8') as f:
                json.dump(result.get('organizer_results'), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'[Queue Runner] failed to save artifacts: {e}')

