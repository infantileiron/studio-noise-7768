from fastapi import HTTPException
from pymysql.err import IntegrityError

from src.config.runtime import database
from src.models.studio import METHOD_COLUMNS, READING_SELECT, audit, decode_json
from src.utils.documents import encode


def sessions():
    with database() as cursor:
        cursor.execute('''SELECT s.*, (SELECT COUNT(*) FROM readings r WHERE r.session_id=s.id) AS reading_count
                          FROM sessions s ORDER BY s.recorded_on DESC, s.start_time DESC, s.id DESC''')
        return cursor.fetchall()


def add_session(data, account):
    try:
        with database() as cursor:
            cursor.execute('''INSERT INTO sessions(code, title, recorded_on, start_time, band, room, note)
                              VALUES (%(code)s,%(title)s,%(recorded_on)s,%(start_time)s,%(band)s,%(room)s,%(note)s)''', data)
            identifier = cursor.lastrowid
            audit(cursor, account['id'], 'session.create', data['code'])
    except IntegrityError as error:
        raise HTTPException(409, '时段编号已使用') from error
    return {'id': identifier, **data, 'reading_count': 0}


def readings(session_id):
    with database() as cursor:
        if session_id is None:
            cursor.execute(READING_SELECT + ' ORDER BY r.id DESC LIMIT 4000')
        else:
            cursor.execute(READING_SELECT + ' WHERE r.session_id=%s ORDER BY r.id DESC LIMIT 4000', (session_id,))
        return cursor.fetchall()


def add_reading(data, account):
    try:
        with database() as cursor:
            cursor.execute('SELECT id FROM sessions WHERE id=%s', (data['session_id'],))
            if cursor.fetchone() is None:
                raise HTTPException(404, '找不到测量时段')
            cursor.execute('''INSERT INTO readings(session_id, reference, hvac, position, traffic, noise, note)
                              VALUES (%(session_id)s,%(reference)s,%(hvac)s,%(position)s,%(traffic)s,%(noise)s,%(note)s)''', data)
            identifier = cursor.lastrowid
            audit(cursor, account['id'], 'reading.create', data['reference'])
            cursor.execute(READING_SELECT + ' WHERE r.id=%s', (identifier,))
            return cursor.fetchone()
    except IntegrityError as error:
        raise HTTPException(409, '同一时段的声测编号已使用') from error


def methods():
    with database() as cursor:
        cursor.execute(f'SELECT {METHOD_COLUMNS} FROM methods ORDER BY id DESC')
        return [decode_json(row, 'controls') for row in cursor.fetchall()]


def add_method(data, account):
    try:
        with database() as cursor:
            cursor.execute('''INSERT INTO methods(version, title, predictor, controls, note)
                              VALUES (%(version)s,%(title)s,%(predictor)s,%(controls)s,%(note)s)''',
                           {**data, 'controls': encode(data['controls'])})
            identifier = cursor.lastrowid
            audit(cursor, account['id'], 'method.create', data['version'])
    except IntegrityError as error:
        raise HTTPException(409, '版本号已使用，请新建版本') from error
    return {'id': identifier, **data}
