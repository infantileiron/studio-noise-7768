import numpy as np

from src.constants.labels import HVAC_RANK

ALGORITHM = 'residual-pearson-v1'


def pearson(x, y):
    if len(x) < 2:
        return None
    left = x - x.mean()
    right = y - y.mean()
    divisor = np.linalg.norm(left) * np.linalg.norm(right)
    return None if divisor == 0 else float(np.clip(left @ right / divisor, -1, 1))


def control_matrix(rows, controls):
    columns = [np.ones(len(rows), dtype=float)]
    labels = ['intercept']
    levels = {}
    for group in controls:
        key = 'session_id' if group == 'session' else group
        values = [str(row[key]) for row in rows]
        categories = sorted(set(values))
        if group == 'hvac':
            categories.sort(key=HVAC_RANK.__getitem__)
        levels[group] = categories
        for category in categories[1:]:
            columns.append(np.array([value == category for value in values], dtype=float))
            labels.append(f'{group}={category}')
    return np.column_stack(columns), labels, levels


def calculate(snapshot):
    rows, method = snapshot['readings'], snapshot['method']
    predictor = method['predictor']
    controls = method['controls']
    x = np.array([row['traffic'] if predictor == 'traffic' else HVAC_RANK[row['hvac']] for row in rows], dtype=float)
    y = np.array([row['noise'] for row in rows], dtype=float)
    raw = pearson(x, y)
    matrix, labels, levels = control_matrix(rows, controls)
    result = {
        'algorithm': ALGORITHM, 'n': len(rows), 'raw': raw, 'partial': None,
        'rows': [{'reference': row['reference'], 'session': row['code'], 'band': row['band'],
                  'x': float(value), 'y': row['noise']} for row, value in zip(rows, x)],
        'columns': labels, 'levels': levels, 'rank': 0, 'df': None, 'warnings': [],
    }
    if len(rows) < 4:
        result['warnings'].append('TOO_FEW_ROWS')
        return 'blocked', result

    measured = np.column_stack((x, y))
    # NumPy's relative cutoff is shared by rank estimation and the least-squares fit.
    coefficients, _, rank, _ = np.linalg.lstsq(matrix, measured, rcond=None)
    result['rank'] = int(rank)
    result['df'] = int(len(rows) - rank - 1)
    absent = [name for name, categories in levels.items() if len(categories) < 2]
    if rank < matrix.shape[1]:
        result['warnings'].append('RANK_DEFICIENT')
    if absent:
        result['warnings'].append('NO_CONTROL_VARIATION')
    if result['df'] < 2:
        result['warnings'].append('LOW_RESIDUAL_DF')
    if result['warnings']:
        return 'blocked', result

    residuals = measured - matrix @ coefficients
    centered_scale = np.maximum(1, np.linalg.norm(measured - measured.mean(axis=0), axis=0))
    if np.any(np.linalg.norm(residuals, axis=0) <= 1e-10 * centered_scale):
        result['warnings'].append('ZERO_RESIDUAL_VARIATION')
        return 'blocked', result

    for point, (left, right) in zip(result['rows'], residuals):
        point.update(rx=float(left), ry=float(right))
    partial = pearson(*residuals.T)
    result['partial'] = partial
    result['absolute_drop'] = abs(raw) - abs(partial)
    return 'complete', result
