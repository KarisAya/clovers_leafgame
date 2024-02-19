import json
import time
from datetime import datetime, timedelta
from pydantic import BaseModel
from pathlib import Path
from collections.abc import Callable
from collections import Counter
from sys import platform

from clovers_core.plugin import Result
from .clovers import Event
from .data import Bank, Prop, Stock, Account, User, Group, Account, DataBase


# self.locate_user_bank: Callable[[Account], Bank] = {
#     0: lambda account: account[1].invest,
#     3: lambda account: account[0].bank,
# }.get(self.domain, lambda account: account[1].bank)
# self.locate_corp_bank: Callable[[Group], Bank] = {
#     0: lambda group: group.invest,
# }.get(self.domain, lambda group: group.bank)
# self.user_prop_N: Callable[[Account], int] = (
#     lambda account: self.locate_user_bank(account).get(self.object_code, 0)
# )
# self.corp_prop_N: Callable[[Group], int] = lambda group: self.locate_corp_bank(
#     group
# ).get(self.object_code, 0)

UserAccount = tuple[User, Account]


class Manager:
    """+++++++++++++++++
    ————————————————————
      ᕱ⑅ᕱ。 ᴍᴏʀɴɪɴɢ
     (｡•ᴗ-)_
    ————————————————————
    +++++++++++++++++"""

    data: DataBase
    file_path: Path
    extra: dict = {}
    group_index: dict[str, str] = {}

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.load()
        self.group_index_update()

    def save(self):
        with open(self.file_path, "w") as f:
            f.write(self.data.json(indent=4))

    def load(self):
        if self.file_path.exists():
            with open(self.file_path, "r") as f:
                self.data = DataBase.parse_obj(json.load(f))

    def group_index_update(self):
        d = self.data.group_dict
        self.group_index.clear()
        self.group_index.update({k: k for k in d})
        self.group_index.update({i: k for k, v in d.items() if (i := v.stock.name)})

    def group_search(self, group_name: str, retry: bool = True) -> Group:
        group_id = self.group_index.get(group_name)
        if group_id:
            return self.data.group_dict[group_id]
        if retry:
            self.group_index_update()
            return self.group_search(group_name, False)

    def stock_search(self, stock_name: str):
        if group := self.group_search(stock_name):
            return group.stock

    def locate_group(self, group_id: str) -> Group:
        """
        定位群组
        """
        return self.data.group_dict.setdefault(group_id, Group(group_id=group_id))

    def locate_user(self, user_id: str) -> User:
        """
        定位用户
        """
        return self.data.user_dict.setdefault(user_id, User(user_id=user_id))

    def locate_account(self, user_id: str, group_id: str) -> UserAccount:
        """
        定位账户
        """
        user = self.locate_user(user_id)
        group = self.locate_group(group_id)
        group.namelist.add(user_id)
        return user, user.connecting(group_id)

    def account(self, event: Event) -> UserAccount:
        """
        定位账户
        """
        user_id = event.user_id
        user = self.locate_user(user_id)
        if event.is_private():
            user.name = event.nickname
            return user, user.connecting()
        if not user.name:
            user.name = event.nickname
        group_id = event.group_id
        group = self.locate_group(group_id)
        group.namelist.add(user_id)
        account = user.connecting(group_id)
        account.nickname = event.nickname
        return user, account
