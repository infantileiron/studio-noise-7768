import math

from src.constants.labels import HVAC_RANK

ALGORITHM = 'traffic-standardized-laeq-v1'
BIN_WIDTH = 5  # 车流分档宽度，辆/分钟
MIN_ROWS = 4
POSITION_RANK = {'booth': 0, 'street': 1, 'door': 2}
PHASES = ('pre', 'post')


def energetic(levels):
    """等效声级：能量平均后再取对数。"""
    return 10 * math.log10(sum(10 ** (level / 10) for level in levels) / len(levels))


def combine(weighted):
    """按权重把多组等效声级能量合成。"""
    total = sum(weight for weight, _ in weighted)
    return 10 * math.log10(sum(weight * 10 ** (level / 10) for weight, level in weighted) / total)


def bin_of(traffic):
    low = traffic // BIN_WIDTH * BIN_WIDTH
    return low, low + BIN_WIDTH - 1


def exclude(entry, reason, slot=None):
    entry['status'] = 'excluded'
    entry['reason'] = reason
    if slot is not None:
        entry['bin'] = [slot[0], slot[1]]


def span(entries):
    return [min(row['traffic'] for row in entries), max(row['traffic'] for row in entries)] if entries else None


def evaluate(key, pair):
    hvac, position = key
    pre, post = pair['pre'], pair['post']
    group = {'hvac': hvac, 'position': position,
             'pre_count': len(pre), 'post_count': len(post),
             'pre_traffic': span(pre), 'post_traffic': span(post),
             'overlap': None, 'comparable': False, 'flags': [], 'bins': [],
             'level_pre': None, 'level_post': None, 'reduction': None, 'weight': 0}
    if not pre or not post:
        group['flags'].append('GROUP_SINGLE_PHASE')
        for entry in pre + post:
            exclude(entry, 'GROUP_SINGLE_PHASE')
        return group
    low = max(group['pre_traffic'][0], group['post_traffic'][0])
    high = min(group['pre_traffic'][1], group['post_traffic'][1])
    if low > high:
        group['flags'].append('NO_TRAFFIC_OVERLAP')
        for entry in pre + post:
            exclude(entry, 'NO_TRAFFIC_OVERLAP')
        return group
    group['overlap'] = [low, high]
    union = [min(group['pre_traffic'][0], group['post_traffic'][0]),
             max(group['pre_traffic'][1], group['post_traffic'][1])]
    if (high - low) * 2 < union[1] - union[0]:
        group['flags'].append('NARROW_TRAFFIC_OVERLAP')
    cells = {}
    for phase, entries in (('pre', pre), ('post', post)):
        for entry in entries:
            if not low <= entry['traffic'] <= high:
                exclude(entry, 'OUTSIDE_TRAFFIC_OVERLAP')
                continue
            cells.setdefault(bin_of(entry['traffic']), {'pre': [], 'post': []})[phase].append(entry)
    shared = []
    for slot in sorted(cells):
        cell = cells[slot]
        if cell['pre'] and cell['post']:
            shared.append((slot, cell))
        else:
            for entry in cell['pre'] + cell['post']:
                exclude(entry, 'BIN_MISSING_COUNTERPART', slot)
    if not shared:
        group['flags'].append('NO_COMPARABLE_BIN')
        return group
    total = sum(len(cell['pre']) + len(cell['post']) for _, cell in shared)
    pre_weighted, post_weighted = [], []
    for slot, cell in shared:
        weight = (len(cell['pre']) + len(cell['post'])) / total
        levels = {phase: energetic([entry['noise'] for entry in cell[phase]]) for phase in PHASES}
        group['bins'].append({'lo': slot[0], 'hi': slot[1], 'weight': weight,
                              'pre_n': len(cell['pre']), 'post_n': len(cell['post']),
                              'pre_level': levels['pre'], 'post_level': levels['post']})
        pre_weighted.append((weight, levels['pre']))
        post_weighted.append((weight, levels['post']))
        for phase in PHASES:
            for entry in cell[phase]:
                entry['bin'] = [slot[0], slot[1]]
    group['level_pre'] = combine(pre_weighted)
    group['level_post'] = combine(post_weighted)
    group['reduction'] = group['level_pre'] - group['level_post']
    group['weight'] = total
    group['comparable'] = True
    return group


def calculate(snapshot):
    ledger = []
    grouped = {}
    counts = {}
    for phase in PHASES:
        rows = snapshot[phase]['readings']
        counts[phase] = len(rows)
        for row in rows:
            entry = {'id': row['id'], 'reference': row['reference'], 'session': row['code'],
                     'phase': phase, 'hvac': row['hvac'], 'position': row['position'],
                     'traffic': row['traffic'], 'noise': row['noise'],
                     'status': 'included', 'reason': None, 'bin': None}
            ledger.append(entry)
            grouped.setdefault((row['hvac'], row['position']),
                               {phase: [] for phase in PHASES})[phase].append(entry)
    result = {'algorithm': ALGORITHM, 'taken_at': snapshot.get('taken_at'), 'bin_width': BIN_WIDTH,
              'n_pre': counts['pre'], 'n_post': counts['post'],
              'overall': None, 'groups': [], 'readings': ledger, 'warnings': []}
    order = sorted(grouped, key=lambda key: (HVAC_RANK[key[0]], POSITION_RANK[key[1]]))
    result['groups'] = [evaluate(key, grouped[key]) for key in order]
    if counts['pre'] + counts['post'] < MIN_ROWS:
        result['warnings'].append('TOO_FEW_ROWS')
    elif not all(counts[phase] for phase in PHASES):
        result['warnings'].append('EMPTY_PHASE')
    used = [group for group in result['groups'] if group['comparable']]
    if result['warnings'] or not used:
        if not used and not result['warnings']:
            result['warnings'].append('NO_COMPARABLE_GROUP')
        return 'blocked', result
    level_pre = combine([(group['weight'], group['level_pre']) for group in used])
    level_post = combine([(group['weight'], group['level_post']) for group in used])
    included = {phase: sum(1 for entry in ledger if entry['phase'] == phase and entry['status'] == 'included')
                for phase in PHASES}
    result['overall'] = {'level_pre': level_pre, 'level_post': level_post,
                         'reduction': level_pre - level_post,
                         'groups_used': len(used), 'groups_total': len(result['groups']),
                         'included_pre': included['pre'], 'included_post': included['post']}
    return 'complete', result
