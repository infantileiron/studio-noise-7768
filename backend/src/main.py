from fastapi import FastAPI, HTTPException
from pymysql import MySQLError
from redis.exceptions import RedisError

from src.config.runtime import cache, database
from src.middlewares.http import install
from src.routes.studio import router

app = FastAPI(title='伏声录制 · 棚内底噪归因')
install(app)
app.include_router(router)


@app.get('/health')
def health():
    try:
        with database() as cursor:
            cursor.execute('SELECT id FROM sessions LIMIT 0')
        cache.ping()
    except (MySQLError, RedisError) as error:
        raise HTTPException(503, '依赖未就绪') from error
    return {'status': 'ok', 'database': 'mysql', 'cache': 'redis'}
