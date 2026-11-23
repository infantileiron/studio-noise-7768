from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

from src.config.runtime import database
from src.constants.labels import Role
from src.models.studio import audit
from src.utils.security import make_token, token_subject, verify_password

bearer = HTTPBearer(auto_error=False)


def login(data):
    with database() as cursor:
        cursor.execute('SELECT id, email, role, password_hash FROM accounts WHERE email=%s', (data.email.lower(),))
        account = cursor.fetchone()
        if account is None or not verify_password(data.password, account.pop('password_hash')):
            raise HTTPException(401, '邮箱或密码有误')
        audit(cursor, account['id'], 'account.login', account['email'])
        return {'token': make_token(account), 'account': account}


def current_account(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    if credentials is None:
        raise HTTPException(401, '请先登录')
    try:
        identifier = token_subject(credentials.credentials)
    except (InvalidTokenError, TypeError, ValueError) as error:
        raise HTTPException(401, '登录已失效，请重新登录') from error
    with database() as cursor:
        cursor.execute('SELECT id, email, role FROM accounts WHERE id=%s', (identifier,))
        account = cursor.fetchone()
    if account is None:
        raise HTTPException(401, '账号不可用')
    return account


Reader = Annotated[dict, Depends(current_account)]


def writer(account: Reader):
    if account['role'] not in (Role.admin, Role.analyst):
        raise HTTPException(403, '此操作需要分析员或业务负责人权限')
    return account


def reviewer(account: Reader):
    if account['role'] != Role.admin:
        raise HTTPException(403, '发布复测清单需要业务负责人权限')
    return account


Writer = Annotated[dict, Depends(writer)]
Reviewer = Annotated[dict, Depends(reviewer)]
