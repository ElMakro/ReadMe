from fastapi import Depends

from server.config.db_dependency import DBDependency
from server.database.models import Courses, Users


class CoursesManager:
    def __init__(self, db: DBDependency = Depends(DBDependency)) -> None:
        self.db = db
        self.courses_model = Courses
        self.users_model = Users
