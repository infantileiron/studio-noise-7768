import json
import logging
import os
import time
from pathlib import Path

from src.config.runtime import cache, database
from src.models.studio import audit
from src.services import correlation, standardize
from src.utils.documents import encode, fingerprint

logger = logging.getLogger(__name__)

QUEUES = (
    ('diagnostics', 'diagnostic', 'result', correlation.calculate),
    ('acceptances', 'acceptance', 'acceptance-result', standardize.calculate),
)


def process():
    with database() as cursor:
        for table, subject, prefix, calculate in QUEUES:
            cursor.execute(f'''SELECT id, snapshot, fingerprint FROM {table} WHERE state='queued'
                               ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED''')
            task = cursor.fetchone()
            if not task:
                continue
            identifier = task['id']
            try:
                snapshot = json.loads(task['snapshot'])
                if fingerprint(snapshot) != task['fingerprint']:
                    raise ValueError('snapshot fingerprint mismatch')
                state, result = calculate(snapshot)
                pending = Path(f'/exports/.{prefix}-{identifier}.tmp')
                pending.write_text(encode(result), encoding='utf-8')
                os.replace(pending, f'/exports/{prefix}-{identifier}.json')
            except Exception:
                logger.exception('%s %s failed', subject, identifier)
                state, result = 'failed', {'warnings': ['CALCULATION_FAILED']}
            cursor.execute(f'UPDATE {table} SET state=%s, result=%s, finished_at=CURRENT_TIMESTAMP WHERE id=%s',
                           (state, encode(result), identifier))
            audit(cursor, None, f'{subject}.{state}', str(identifier))
            return True
    return False


def main():
    logging.basicConfig(level=logging.INFO)
    while True:
        try:
            completed = process()
            cache.set('studio:worker:heartbeat', 'ready', ex=12)
            if not completed:
                time.sleep(0.5)
        except Exception:
            logger.exception('Worker dependency unavailable')
            time.sleep(2)


if __name__ == '__main__':
    main()
