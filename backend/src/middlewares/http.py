import logging
from uuid import uuid4

from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def install(app):
    @app.middleware('http')
    async def handle_errors(request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception('Request failed: %s', request.state.request_id)
            return JSONResponse({'detail': '服务暂不可用，请稍后重试'}, status_code=500)

    @app.middleware('http')
    async def request_context(request, call_next):
        request.state.request_id = str(uuid4())
        response = await call_next(request)
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['Cache-Control'] = 'no-store'
        return response
