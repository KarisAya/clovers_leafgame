from datetime import datetime, timedelta
from pydantic import BaseModel
from pathlib import Path
from collections.abc import Callable
import json


Bank = dict[str, int]


class Prop:
    rare: int
    """稀有度"""
    domain: int
    """
    作用域   
        0:无(空气)
        1:群内
        2:全局
        3:股票 
    """
    flow: int
    """
    道具时效
        0:永久道具
        1:时效道具
    """
    number: int
    """道具编号"""

    def __init__(
        self,
        object_code: str,
        name: str,
        color: str,
        intro: str,
        tip: str,
    ) -> None:
        self.object_code: str = object_code
        self.name: str = name
        self.color: str = color
        self.intro: str = intro
        self.tip: str = tip
        self.rare, self.domain, self.flow, self.number = self.code_info()

    def code_info(self):
        """
        return
            rare:稀有度
            domain:作用域
                0:无(空气)
                1:全局
                2:群内
                3:股票
            flow:道具时效
                0:时效道具
                1:永久道具
            number:道具编号
        """
        rare = int(self.object_code[0])
        domain = int(self.object_code[1])
        flow = int(self.object_code[2])
        number = int(self.object_code[3:])
        return rare, domain, flow, number

    def deal(self, bank: Bank, unsettled: int):
        """
        账户结算
        """
        object_code = self.object_code
        n = bank.get(object_code, 0)
        if unsettled < 0 and n < (-unsettled):
            return n
        bank[object_code] = n + unsettled

    def func(self):
        return f"道具{self.name}不可使用"

    def set_usage(self, **kwargs):
        def decorator(func: Callable):
            def wrapper(event):
                return func(self, event, **kwargs)

            self.func = wrapper

        return decorator

    def __call__(self, **kwargs):
        return self.func(**kwargs)


class Account(BaseModel):
    """
    用户群账户
    """

    nickname: str = None
    sign_date: datetime = datetime.today() - timedelta(days=1)
    revolution: bool = False
    invest: Bank = Bank()
    bank: Bank = Bank()
    extra: dict = {}


class User(BaseModel):
    """
    用户数据
    """

    user_id: str = None
    nickname: str = None
    avatar_url: str = None
    win: int = 0
    lose: int = 0
    Achieve_win: int = 0
    Achieve_lose: int = 0
    accounts: dict[str, Account] = {}
    connect: str = 0
    bank: Bank = Bank()
    extra: dict = {}

    def connecting(self, group_id: str = None) -> Account:
        """连接到账户"""
        group_id = group_id or self.connect
        return self.accounts.setdefault(group_id, Account(nickname=self.nickname))

    def locate_bank(self, group_id: str, domain: int) -> Bank:
        return locate_bank(self, group_id, domain).get(domain)

    def deal(self, group_id: str, prop: Prop, unsettled: int):
        return prop.deal(self.locate_bank(group_id, prop.domain), unsettled)


def locate_bank(user: User, group_id: str, domain: int) -> Bank:
    {
        1: user.bank,
        2: user.connecting(group_id).bank,
        3: user.connecting(group_id).invest,
    }.get(domain)


class Group(BaseModel):
    """
    群字典
    """

    group_id: str = None
    """群号"""
    namelist: set = set()
    """群员名单"""
    stock_id: str = None
    """发行ID"""
    stock_name: str = None
    """公司名称"""
    level: int = 1
    """群等级"""
    issuance: int = 0
    """股票发行量"""
    bank: Bank = Bank()
    """群金库"""
    intro: str = None
    """群介绍"""
    extra: dict = {}

    @property
    def name(self) -> str:
        return self.stock_name or self.group_id


class DataBase(BaseModel):
    user_dict: dict[str, User] = {}
    group_dict: dict[str, Group] = {}

    def save(self, file_path: Path):
        """
        保存数据
        """
        with open(file_path, "w") as f:
            f.write(self.json(indent=4))

    def load(self, file_path: Path):
        """
        从json文件中加载数据
        """
        with open(file_path, "r") as f:
            raw_data = json.load(f)

        user_dict: dict = raw_data["user_dict"]
        for user_id, user in user_dict.items():
            accounts: dict = user["accounts"]
            for group_id, account in accounts.items():
                accounts[group_id] = Account.parse_obj(account)
            self.user_dict[user_id] = User.parse_obj(user)

        group_dict = raw_data["group_dict"]
        for group_id, group in group_dict.items():
            self.group_dict[group_id] = Group.parse_obj(group)
