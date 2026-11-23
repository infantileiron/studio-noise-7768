"""演示数据的确定性生成：不依赖数据库，便于复核与测试。"""

WINDOWS = [
    ('FS-1109-A', '晨间校准', '2026-11-09', '07:40', 'early'),
    ('FS-1109-B', '日班旁白前', '2026-11-09', '14:20', 'day'),
    ('FS-1109-C', '晚间收棚', '2026-11-09', '20:10', 'late'),
    ('FS-1112-A', '晨间复测', '2026-11-12', '07:45', 'early'),
    ('FS-1112-B', '日班开棚', '2026-11-12', '14:15', 'day'),
    ('FS-1112-C', '晚班留底', '2026-11-12', '20:05', 'late'),
]
POST_WINDOWS = [
    ('FS-1117-A', '改造后晨间验收', '2026-11-17', '07:50', 'early'),
    ('FS-1117-B', '改造后日班验收', '2026-11-17', '14:25', 'day'),
    ('FS-1117-C', '改造后晚间验收', '2026-11-17', '20:15', 'late'),
    ('FS-1119-A', '复验晨间', '2026-11-19', '07:45', 'early'),
    ('FS-1119-B', '复验日班', '2026-11-19', '14:20', 'day'),
    ('FS-1119-C', '复验晚间', '2026-11-19', '20:10', 'late'),
]
METHODS = [
    ('TRF-01', '时段校正 · 车流', 'traffic', ['band', 'hvac', 'position'], '对照未调整与控制后的车流关联。'),
    ('AIR-01', '同条件比风机', 'hvac', ['band', 'position'], '将风机档位作有序解释量，控制时段与测点。'),
    ('RANK-01', '共线边界复核', 'traffic', ['band', 'session'], '每个具体时段属于唯一班带，组合后矩阵秩亏。'),
]
HVACS = ('quiet', 'normal', 'boost')
POSITIONS = ('booth', 'street')
POST_POSITIONS = ('booth', 'street', 'door')
PERIOD = {'early': 0, 'day': 2, 'late': 1}
POSITION_OFFSET = {'booth': 0.0, 'street': 2.1, 'door': 1.2}
POSITION_SIGN = {'booth': -0.95, 'street': 0.95, 'door': 0.3}
INSULATION = {'booth': 4.2, 'street': 2.8, 'door': 5.0}


def pre_readings(index, band):
    period = PERIOD[band]
    for level, hvac in enumerate(HVACS):
        for side, position in enumerate(POSITIONS):
            for repeat, sign in enumerate((-1, 1), 1):
                traffic = 8 + 16 * period + 3 * sign + index // 3
                noise = 26 + 5 * period + 2.5 * level + 2.1 * side + .12 * sign + .95 * (2 * side - 1) * sign
                noise += .5 * (2 * (index // 3) - 1)
                yield (f'{level + 1}{side + 1}{repeat}', hvac, position, traffic, round(noise, 2),
                       '合成 LAeq 与同步车流')


def post_readings(index, band):
    period = PERIOD[band]
    for level, hvac in enumerate(HVACS):
        for side, position in enumerate(POST_POSITIONS):
            for repeat, sign in enumerate((-1, 1), 1):
                traffic = 10 + 15 * period + 3 * sign + 2 * (index // 3)
                note = '改造后合成 LAeq 与同步车流'
                if hvac == 'boost' and position == 'street':
                    traffic += 45
                    note = '高档临街测点改在路口旁同步计数'
                noise = 26 + 5 * period + 2.5 * level + POSITION_OFFSET[position] + .12 * sign
                noise += POSITION_SIGN[position] * sign + .5 * (2 * (index // 3) - 1)
                noise -= INSULATION[position]
                yield (f'{level + 1}{side + 1}{repeat}', hvac, position, traffic, round(noise, 2), note)
