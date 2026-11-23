from src.config.runtime import database
from src.utils.documents import encode
from src.utils.security import password_hash

WINDOWS = [
    ('FS-1109-A', '晨间校准', '2026-11-09', '07:40', 'early'),
    ('FS-1109-B', '日班旁白前', '2026-11-09', '14:20', 'day'),
    ('FS-1109-C', '晚间收棚', '2026-11-09', '20:10', 'late'),
    ('FS-1112-A', '晨间复测', '2026-11-12', '07:45', 'early'),
    ('FS-1112-B', '日班开棚', '2026-11-12', '14:15', 'day'),
    ('FS-1112-C', '晚班留底', '2026-11-12', '20:05', 'late'),
]
METHODS = [
    ('TRF-01', '时段校正 · 车流', 'traffic', ['band', 'hvac', 'position'], '对照未调整与控制后的车流关联。'),
    ('AIR-01', '同条件比风机', 'hvac', ['band', 'position'], '将风机档位作有序解释量，控制时段与测点。'),
    ('RANK-01', '共线边界复核', 'traffic', ['band', 'session'], '每个具体时段属于唯一班带，组合后矩阵秩亏。'),
]


def seed():
    with database() as cursor:
        for role in ('admin', 'analyst', 'viewer'):
            email = role + '@demo.local'
            cursor.execute('SELECT id FROM accounts WHERE email=%s', (email,))
            if not cursor.fetchone():
                cursor.execute('''INSERT INTO accounts(email,password_hash,role) VALUES (%s,%s,%s)
                                  ON DUPLICATE KEY UPDATE id=id''', (email, password_hash('Tape2026!'), role))
        for index, (code, title, day, hour, band) in enumerate(WINDOWS):
            cursor.execute('''INSERT INTO sessions(code,title,recorded_on,start_time,band,room,note)
                              VALUES (%s,%s,%s,%s,%s,'A 棚 · 临街间','无声段 60 秒，车流和声级同步计数')
                              ON DUPLICATE KEY UPDATE id=id''', (code, title, day, hour, band))
            cursor.execute('SELECT id FROM sessions WHERE code=%s', (code,))
            session_id = cursor.fetchone()['id']
            period = {'early': 0, 'day': 2, 'late': 1}[band]
            for level, hvac in enumerate(('quiet', 'normal', 'boost')):
                for side, position in enumerate(('booth', 'street')):
                    for repeat, sign in enumerate((-1, 1), 1):
                        traffic = 8 + 16 * period + 3 * sign + index // 3
                        noise = 26 + 5 * period + 2.5 * level + 2.1 * side + .12 * sign + .95 * (2 * side - 1) * sign
                        noise += .5 * (2 * (index // 3) - 1)
                        key = f'{code}-{level + 1}{side + 1}{repeat}'
                        cursor.execute('''INSERT INTO readings(session_id, reference, hvac, position, traffic, noise, note)
                                          VALUES (%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE id=id''',
                                       (session_id, key, hvac, position, traffic, round(noise, 2), '合成 LAeq 与同步车流'))
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
