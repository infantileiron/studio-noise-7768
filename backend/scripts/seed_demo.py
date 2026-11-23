from scripts.demo_data import METHODS, POST_WINDOWS, WINDOWS, post_readings, pre_readings
from src.config.runtime import database
from src.utils.documents import encode
from src.utils.security import password_hash


def add_window(cursor, index, window, readings):
    code, title, day, hour, band = window
    cursor.execute('''INSERT INTO sessions(code,title,recorded_on,start_time,band,room,note)
                      VALUES (%s,%s,%s,%s,%s,'A 棚 · 临街间','无声段 60 秒，车流和声级同步计数')
                      ON DUPLICATE KEY UPDATE id=id''', (code, title, day, hour, band))
    cursor.execute('SELECT id FROM sessions WHERE code=%s', (code,))
    session_id = cursor.fetchone()['id']
    for suffix, hvac, position, traffic, noise, note in readings(index, band):
        cursor.execute('''INSERT INTO readings(session_id, reference, hvac, position, traffic, noise, note)
                          VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE id=id''',
                       (session_id, f'{code}-{suffix}', hvac, position, traffic, noise, note))


def seed():
    with database() as cursor:
        for role in ('admin', 'analyst', 'viewer'):
            email = role + '@demo.local'
            cursor.execute('SELECT id FROM accounts WHERE email=%s', (email,))
            if not cursor.fetchone():
                cursor.execute('''INSERT INTO accounts(email,password_hash,role) VALUES (%s,%s,%s)
                                  ON DUPLICATE KEY UPDATE id=id''', (email, password_hash('Tape2026!'), role))
        for index, window in enumerate(WINDOWS):
            add_window(cursor, index, window, pre_readings)
        for index, window in enumerate(POST_WINDOWS):
            add_window(cursor, index, window, post_readings)
        for version, title, predictor, controls, note in METHODS:
            cursor.execute('''INSERT INTO methods(version,title,predictor,controls,note) VALUES (%s,%s,%s,%s,%s)
                              ON DUPLICATE KEY UPDATE id=id''', (version, title, predictor, encode(controls), note))
        summary = {}
        for table, keys in [('accounts', 'email'), ('sessions', 'code'), ('readings', 'session_id,reference'), ('methods', 'version')]:
            cursor.execute(f'SELECT {keys} FROM {table} ORDER BY {keys}')
            rows = cursor.fetchall()
            summary[table] = {'count': len(rows), 'keys': rows}
        print(encode(summary))


if __name__ == '__main__':
    seed()
