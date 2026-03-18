from app.core.errors import InvalidPassword
from app.core.ports.auth_provider import IAuthProvider
from app.core.ports.user_repo import IUserRepo
from app.core.shared.time_utils import now_cst


class ChangePassword:
    def __init__(self, user_repo: IUserRepo, auth_provider: IAuthProvider) -> None:
        self._user_repo = user_repo
        self._auth_provider = auth_provider

    def execute(self, user_id: int, old_password: str, new_password: str) -> dict:
        user = self._user_repo.get(user_id)
        if not self._auth_provider.verify_password(old_password, user.hashed_pw):
            raise InvalidPassword("原密码错误")
        if len(new_password) < 6:
            raise ValueError("新密码至少 6 位")

        user.hashed_pw = self._auth_provider.hash_password(new_password)
        user.updated_at = now_cst()
        self._user_repo.update(user)
        return {"message": "密码修改成功"}
