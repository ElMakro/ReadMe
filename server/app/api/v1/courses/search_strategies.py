from abc import ABC, abstractmethod

from server.app.api.v1.courses.courses import CourseFullListResponse
from server.app.api.v1.courses.courses_manager import CoursesManager


class CourseSearchStrategy(ABC):
    @abstractmethod
    async def search(self, manager: CoursesManager, value: str) -> CourseFullListResponse:
        pass

class NamePrefixSearchStrategy(CourseSearchStrategy):
    async def search(self, manager, value):
        return await manager.search_courses_by_name_prefix(value)

class TagSearchStrategy(CourseSearchStrategy):
    async def search(self, manager, value):
        return await manager.search_courses_by_tag(value)


SEARCH_STRATEGIES: dict[str, CourseSearchStrategy] = {
    "name_prefix": NamePrefixSearchStrategy(),
    "tag": TagSearchStrategy(),
}
