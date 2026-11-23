import logging
from pathlib import Path

from fastapi import HTTPException
from pymysql.err import IntegrityError

from src.config.runtime import database
from src.constants.labels import Role
from src.models.studio import METHOD_COLUMNS, READING_SELECT, RUN_COLUMNS, RUN_FROM, audit, decode_json
from src.services.correlation import ALGORITHM
from src.utils.documents import encode, fingerprint

logger = logging.getLogger(__name__)


def queue(data, account):
    session_ids = sorted(data['session_ids'])
    placeholders = ','.join(['%s'] * len(session_ids))
    try:
        with database() as cursor:
            cursor.execute(f'SELECT {METHOD_COLUMNS} FROM methods WHERE id=%s', (data['method_id'],))
            method = decode_json(cursor.fetchone(), 'controls')
            if method is None:
                raise HTTPException(404, '找不到变量版本')
            cursor.execute(f'SELECT id, code FROM sessions WHERE id IN ({placeholders}) ORDER BY id', session_ids)
            selected = cursor.fetchall()
            if len(selected) != len(session_ids):
                raise HTTPException(404, '部分测量时段不存在，请重新选择')
            cursor.execute(READING_SELECT + f' WHERE r.session_id IN ({placeholders}) ORDER BY r.id LIMIT 4001', session_ids)
            readings = cursor.fetchall()
            if len(readings) > 4000:
                raise HTTPException(422, '单次诊断最多处理 4000 条声测，请缩小时段范围')
            snapshot = {'algorithm': ALGORITHM, 'method': method, 'sessions': selected, 'readings': readings}
            checksum = fingerprint(snapshot)
            cursor.execute('''INSERT INTO diagnostics(method_id, title, owner_id, fingerprint, snapshot)
                              VALUES (%s,%s,%s,%s,%s)''',
                           (method['id'], data['title'], account['id'], checksum, encode(snapshot)))
            identifier = cursor.lastrowid
            audit(cursor, account['id'], 'diagnostic.queue', str(identifier))
    except IntegrityError as error:
        raise HTTPException(409, '诊断单名称已使用') from error
    return {'id': identifier, 'state': 'queued', 'fingerprint': checksum, 'n': len(readings)}


def list_runs(account):
    scope = ' WHERE d.reviewed_at IS NOT NULL' if account['role'] == Role.viewer else ''
    columns = RUN_COLUMNS.replace('d.result,', 'NULL AS result,')
    with database() as cursor:
        cursor.execute('SELECT ' + columns + ' ' + RUN_FROM + scope + ' ORDER BY d.id DESC LIMIT 100')
        return cursor.fetchall()


def get_run(identifier, account, snapshot=False):
    scope = ' AND d.reviewed_at IS NOT NULL' if account['role'] == Role.viewer else ''
    columns = RUN_COLUMNS + (', d.snapshot' if snapshot else '')
    with database() as cursor:
        cursor.execute('SELECT ' + columns + ' ' + RUN_FROM + ' WHERE d.id=%s' + scope, (identifier,))
        row = cursor.fetchone()
    if row is None:
        raise HTTPException(404, '找不到可阅诊断单')
    return decode_json(row, 'result', *(['snapshot'] if snapshot else []))


def publish(identifier, text, account):
    with database() as cursor:
        cursor.execute('SELECT state, reviewed_at FROM diagnostics WHERE id=%s FOR UPDATE', (identifier,))
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(404, '找不到诊断单')
        if row['state'] != 'complete' or row['reviewed_at']:
            raise HTTPException(409, '仅可发布已算完且未发布的诊断')
        cursor.execute('''UPDATE diagnostics SET decision=%s, reviewer_id=%s, reviewed_at=CURRENT_TIMESTAMP
                          WHERE id=%s''', (text, account['id'], identifier))
        audit(cursor, account['id'], 'diagnostic.publish', str(identifier))
    return get_run(identifier, account)


def export(identifier, account):
    run = get_run(identifier, account, snapshot=True)
    if run['state'] not in ('complete', 'blocked'):
        raise HTTPException(409, '诊断尚无可导出的计算证据')
    prefix = 'published' if run['reviewed_at'] else 'working'
    path = Path(f'/exports/studio-{identifier}-{prefix}.json')
    document = encode({**run, **{key: run[key].isoformat() if run[key] else None
                                for key in ('created_at', 'finished_at', 'reviewed_at')}})
    with database() as cursor:
        audit(cursor, account['id'], 'diagnostic.export', str(identifier))
    return path.name, document
