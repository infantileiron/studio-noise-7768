import logging
from pathlib import Path

from fastapi import HTTPException
from pymysql.err import IntegrityError

from src.config.runtime import database
from src.constants.labels import Role
from src.models.studio import ACCEPTANCE_COLUMNS, ACCEPTANCE_FROM, READING_SELECT, audit, decode_json
from src.services.standardize import ALGORITHM
from src.utils.documents import encode, fingerprint

logger = logging.getLogger(__name__)

PHASES = (('pre', 'pre_session_ids'), ('post', 'post_session_ids'))


def queue(data, account):
    # 两期在同一事务内取数：补录与验收同时提交时，快照仍对应同一时点。
    with database() as cursor:
        cursor.execute('SELECT CURRENT_TIMESTAMP(3) AS taken_at')
        snapshot = {'algorithm': ALGORITHM, 'taken_at': cursor.fetchone()['taken_at'].isoformat()}
        total = 0
        for phase, key in PHASES:
            session_ids = sorted(data[key])
            placeholders = ','.join(['%s'] * len(session_ids))
            cursor.execute(f'SELECT id, code FROM sessions WHERE id IN ({placeholders}) ORDER BY id', session_ids)
            selected = cursor.fetchall()
            if len(selected) != len(session_ids):
                raise HTTPException(404, '部分测量时段不存在，请重新选择')
            cursor.execute(READING_SELECT + f' WHERE r.session_id IN ({placeholders}) ORDER BY r.id LIMIT 4001',
                           session_ids)
            readings = cursor.fetchall()
            total += len(readings)
            if total > 4000:
                raise HTTPException(422, '单次验收最多处理 4000 条声测，请缩小时段范围')
            snapshot[phase] = {'sessions': selected, 'readings': readings}
        checksum = fingerprint(snapshot)
        try:
            cursor.execute('''INSERT INTO acceptances(title, owner_id, fingerprint, snapshot)
                              VALUES (%s,%s,%s,%s)''',
                           (data['title'], account['id'], checksum, encode(snapshot)))
        except IntegrityError as error:
            raise HTTPException(409, '验收单名称已使用') from error
        identifier = cursor.lastrowid
        audit(cursor, account['id'], 'acceptance.queue', str(identifier))
    return {'id': identifier, 'state': 'queued', 'fingerprint': checksum, 'n': total}


def list_runs(account):
    scope = ' WHERE x.reviewed_at IS NOT NULL' if account['role'] == Role.viewer else ''
    columns = ACCEPTANCE_COLUMNS.replace('x.result,', 'NULL AS result,')
    with database() as cursor:
        cursor.execute('SELECT ' + columns + ' ' + ACCEPTANCE_FROM + scope + ' ORDER BY x.id DESC LIMIT 100')
        return cursor.fetchall()


def get_run(identifier, account, snapshot=False):
    scope = ' AND x.reviewed_at IS NOT NULL' if account['role'] == Role.viewer else ''
    columns = ACCEPTANCE_COLUMNS + (', x.snapshot' if snapshot else '')
    with database() as cursor:
        cursor.execute('SELECT ' + columns + ' ' + ACCEPTANCE_FROM + ' WHERE x.id=%s' + scope, (identifier,))
        row = cursor.fetchone()
    if row is None:
        raise HTTPException(404, '找不到可阅验收单')
    return decode_json(row, 'result', *(['snapshot'] if snapshot else []))


def publish(identifier, text, account):
    with database() as cursor:
        cursor.execute('SELECT state, reviewed_at FROM acceptances WHERE id=%s FOR UPDATE', (identifier,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(404, '找不到验收单')
        if row['state'] != 'complete' or row['reviewed_at']:
            raise HTTPException(409, '仅可发布已算完且未发布的验收')
        cursor.execute('''UPDATE acceptances SET decision=%s, reviewer_id=%s, reviewed_at=CURRENT_TIMESTAMP
                          WHERE id=%s''', (text, account['id'], identifier))
        audit(cursor, account['id'], 'acceptance.publish', str(identifier))
    return get_run(identifier, account)


def export(identifier, account):
    run = get_run(identifier, account, snapshot=True)
    if run['state'] not in ('complete', 'blocked'):
        raise HTTPException(409, '验收尚无可导出的计算证据')
    prefix = 'published' if run['reviewed_at'] else 'working'
    path = Path(f'/exports/acceptance-{identifier}-{prefix}.json')
    document = encode({**run, **{key: run[key].isoformat() if run[key] else None
                                for key in ('created_at', 'finished_at', 'reviewed_at')}})
    with database() as cursor:
        audit(cursor, account['id'], 'acceptance.export', str(identifier))
    return path.name, document
