class AppNotFound(Exception):
    def __init__(self, app_id: int = 0, slug: str = ""):
        self.app_id = app_id
        self.slug = slug
        super().__init__(f"App 不存在: id={app_id} slug={slug}")


class SlugTaken(Exception):
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"slug '{slug}' 已被占用")


class UserNotFound(Exception):
    def __init__(self, user_id: int = 0, username: str = ""):
        super().__init__(f"用户不存在: id={user_id} username={username}")


class UsernameExists(Exception):
    def __init__(self, username: str):
        self.username = username
        super().__init__(f"用户名 {username} 已存在")


class Unauthorized(Exception):
    def __init__(self, detail: str = "无效的 Token"):
        self.detail = detail
        super().__init__(detail)


class Forbidden(Exception):
    def __init__(self, detail: str = "无权限操作"):
        self.detail = detail
        super().__init__(detail)


class SessionConflict(Exception):
    def __init__(self):
        super().__init__("您的账号已在其他地方登录")


class AccountExpired(Exception):
    def __init__(self):
        super().__init__("账号已过期，请联系管理员")


class AccountDisabled(Exception):
    def __init__(self):
        super().__init__("账号已被禁用")


class InvalidPassword(Exception):
    def __init__(self, detail: str = "用户名或密码错误"):
        self.detail = detail
        super().__init__(detail)


class AppBuildInProgress(Exception):
    def __init__(self):
        super().__init__("正在构建中，请等待")


class NoUploadedCode(Exception):
    def __init__(self):
        super().__init__("请先上传代码文件")


class NoContainer(Exception):
    def __init__(self):
        super().__init__("容器不存在，请重新部署")


class PromptNotFound(Exception):
    def __init__(self, prompt_id: int):
        super().__init__(f"Prompt 不存在: id={prompt_id}")


class SkillNotFound(Exception):
    def __init__(self, name: str):
        super().__init__(f"Skill 不存在: {name}")


class InvalidFile(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class CannotDeleteSelf(Exception):
    def __init__(self):
        super().__init__("不能删除自己的账号")
