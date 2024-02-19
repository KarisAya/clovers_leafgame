import os
import json
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Union

resource_file = Path(os.path.dirname(__file__))


with open(resource_file / "props_library.json", "r", encoding="utf8") as f:
    props_library: dict = json.load(f)

Bank = dict[str, int]


class Stock(BaseModel):
    id: str = None
    name: str = None


class OldGroupAccount(BaseModel):
    """
    用户群账户
    """

    user_id: str = None
    group_id: str = None
    nickname: str = None
    is_sign: bool = False
    revolution: bool = False
    security: int = 0
    gold: int = 0
    invest: dict[str, int] = {}
    props: dict[str, int] = {}
    bank: Bank = {}


class OldUserDict(BaseModel):
    """
    用户字典
    """

    user_id: str = None
    nickname: str = None
    avatar_url: str = "https://avatars.githubusercontent.com/u/51886078"
    gold: int = 0
    win: int = 0
    lose: int = 0
    Achieve_win: int = 0
    Achieve_lose: int = 0
    accounts: dict[str, OldGroupAccount] = {}
    connect: str = 0
    bank: Bank = {}
    props: dict[str, int] = {}
    alchemy: dict[str, int] = {}


class OldUserData(dict[str, OldUserDict]):
    """
    用户数据
    """


class ExchangeInfo(BaseModel):
    """
    交易信息
    """

    group_id: str = None
    quote: float = 0.0
    n: int = 0


class OldCompany(BaseModel):
    """
    公司账户
    """

    company_id: str = None
    """群号"""
    company_name: str = None
    """公司名称"""
    level: int = 1
    """公司等级"""
    time: float = 0.0
    """注册时间"""
    stock: Union[int, Stock] = Stock()
    """正在发行的股票数"""
    issuance: int = 0
    """股票发行量"""
    gold: float = 0.0
    """固定资产"""
    float_gold: float = 0.0
    """浮动资产"""
    group_gold: float = 0.0
    """全群资产"""
    bank: Union[int, Bank] = 0
    """群金库"""
    invest: dict[str, int] = {}
    """群投资"""
    transfer_limit: float = 0.0
    """每日转账限制"""
    transfer: int = 0
    """今日转账额"""
    intro: str = None
    """群介绍"""
    exchange: dict[str, ExchangeInfo] = {}
    """本群交易市场"""
    orders: dict = {}
    """当前订单"""


class OldGroupDict(BaseModel):
    """
    群字典
    """

    group_id: str = None
    namelist: set = set()
    revolution_time: float = 0.0
    Achieve_revolution: dict[str, int] = {}
    company: OldCompany = OldCompany()


class OldGroupData(dict[str, OldGroupDict]):
    """
    群数据
    """

    pass


class OldDataBase(BaseModel):
    user: OldUserData = OldUserData()
    user_dict: OldUserData = None
    group: OldGroupData = OldGroupData()
    group_dict: OldGroupData = None
    file: Path

    def save(self):
        """
        保存数据
        """
        with open(self.file, "w") as f:
            f.write(self.json(indent=4))

    @classmethod
    def loads(cls, data: str):
        """
        从json字符串中加载数据
        """
        data_dict = json.loads(data)
        return cls.parse_obj(data_dict)


data_file = resource_file / "russian_data.json"
with open(data_file, "r") as f:
    data = OldDataBase.loads(f.read())

data.file = data_file

for user in data.user.values():
    for group_account in user.group_accounts.values():
        group_account.bank = group_account.props
        group_account.bank["1111"] = group_account.gold
    user.bank = user.props

for group in data.group.values():
    N = group.company.bank
    if isinstance(N, int):
        group.company.bank = {"1111": N}

data.group_dict = data.group
data.user_dict = data.user

data.save()
