from collections.abc import Iterable

from dishka import Provider

from core.config.database import DatabaseProvider
from core.config.settings import SettingsProvider
from core.services.user_profile_provider import UserProfileProvider
from modules.auth import AuthProvider
from modules.reports.report_provider import ReportsProvider
from modules.rules.rule_provider import RulesProvider
from modules.users.user_provider import UsersProvider


def get_providers() -> Iterable[Provider]:
    return (
        SettingsProvider(),
        DatabaseProvider(),
        AuthProvider(),
        RulesProvider(),
        ReportsProvider(),
        UsersProvider(),
        UserProfileProvider(),
    )
