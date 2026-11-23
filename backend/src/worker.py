import json
import logging
import os
import time
from pathlib import Path

from src.config.runtime import cache, database
from src.models.studio import audit
from src.services.correlation import calculate
from src.utils.documents import encode, fingerprint

logger = logging.getLogger(__name__)


def process():
    with database() as cursor:
        cursor.execute('''SELECT id, snapshot, fingerprint FROM diagnostics WHERE state='queued'
                          ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED''')
        task = cursor.fetchone()
        if not task:
            return False
        identifier = task['id']
        try:
            snapshot = json.loads(task['snapshot'])
            if fingerprint(snapshot) != task['fingerprint']:
                raise ValueError('snapshot fingerprint mismatch')
            state, result = calculate(snapshot)
            pending = Path(f'/exports/.{identifier}.tmp')
            pending.write_text(encode(result), encoding='utf-8')
            os.replace(pending, f'/exports/result-{identifier}.json')
        except Exception:
            logger.exception('Diagnostic %s failed', identifier)
            state, result = 'failed', {'warnings': ['CALCULATION_FAILED']}
        cursor.execute('UPDATE diagnostics SET state=%s, result=%s, finished_at=CURRENT_TIMESTAMP WHERE id=%s',
                       (state, encode(result), identifier))
        audit(cursor, None, f'diagnostic.{state}', str(identifier))
        return True


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
