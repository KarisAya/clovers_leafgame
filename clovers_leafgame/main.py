import random
import math
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

from clovers_core.plugin import Result

from .core.clovers import Event
from .core.account import Manager
from .core.data import Prop, Bank, Group
from .core.utils import to_int

from .config import config, BG_PATH
from .clover import plugin, check_to_me, check_superuser, check_group_admin, check_at
from .library import prop_search, GOLD, VIP_CARD, AIR_PACK, LICENSE, gacha, curve_fit
from .utils.linecard import FontManager, linecard_to_png, linecard, info_splicing
from .utils.tools import download_url
from .output import bank_info

sign_gold = config.sign_gold
revolt_gold = config.revolt_gold
company_public_gold = config.company_public_gold
gacha_gold = config.gacha_gold

manager = Manager()
manager.file_path = Path(config.main_path) / "russian_data.json"
manager.load()

font_manager = FontManager(config.fontname, config.fallback_fonts, (30, 40, 60))


def info_card(info, user_id):
    extra = manager.locate_user(user_id).extra
    BG_type = extra.get("BG_type", "#FFFFFF99")
    bg_path = BG_PATH / f"{user_id}.png"
    if not bg_path.exists():
        bg_path = BG_PATH / "default.png"
    try:
        return info_splicing(info, bg_path, spacing=10, BG_type=BG_type)
    except:
        del extra["BG_type"]
        return f"你的自定义背景 {BG_type} 出错了，背景已重置。"


@plugin.handle({"金币签到", "轮盘签到"}, {"user_id", "group_id", "nickname", "avatar"})
async def _(event: Event) -> Result:
    account = manager.locate_account(event)
    user, group_account = account
    user.avatar_url = event.avatar
    today = datetime.today()
    delta_days = (today - group_account.sign_date).days
    if delta_days == 0:
        return "你已经签过到了哦"
    else:
        N = random.randint(*sign_gold) * delta_days
        manager.user_deal(account, GOLD, N)
    return random.choice(["祝你好运~", "可别花光了哦~"]) + f"\n你获得了 {N} 金币"


@plugin.handle({"重置签到", "领取金币"}, {"user_id", "group_id", "nickname", "avatar"})
async def _(event: Event) -> Result:
    account = manager.locate_account(event)
    user, group_account = account
    user.avatar_url = event.avatar
    if group_account.revolution:
        return "你没有待领取的金币"
    else:
        N = random.randint(*revolt_gold)
        manager.user_deal(account, GOLD, N)
        group_account.revolution = True
    return f"这是你重置后获得的金币！你获得了 {N} 金币"


@plugin.handle(
    {"发红包", "赠送金币"},
    {"user_id", "group_id", "nickname", "at", "permission"},
)
@check_at.wrapper
async def _(event: Event) -> Result:
    at = event.at[0]
    group_id = event.group_id
    N = event.args_to_int(random.randint(*sign_gold))
    account_out = manager.locate_account(event)
    account_in = manager.setdefault_account(at, group_id)
    if N < 0:
        if event.permission < 2:
            return "你发了负数的红包，请不要这样做。"
        account_out, account_in = account_in, account_out
        N = -N
        sender = "对方"
    else:
        sender = "你"
    if manager.u > 0:
        tax = 0
        tip = f"『{VIP_CARD.name}』免手续费"
    else:
        tax = int(N * 0.02)
        tip = f"扣除2%手续费：{tax}，实际到账金额{N - tax}"

    manager.user_deal(account_out, -N)
    if GOLD.deal(bank_out, -N):
        return f"数量不足。\n——{sender}还有{bank_out.get(GOLD.object_code, 0)}枚金币。"
    GOLD.deal(GOLD.locate_user_bank(account_in), N - tax)
    group = manager.locate_group(group_id)
    GOLD.deal(GOLD.locate_corp_bank(group), tax)
    return f"{account_out[1].nickname} 向 {account_in[1].nickname} 赠送{N}金币\n{tip}"


@plugin.handle(
    {"送道具", "赠送道具"},
    {"user_id", "group_id", "nickname", "at", "permission"},
)
@check_at.wrapper
async def _(event: Event) -> Result:
    at = event.at[0]
    group_id = event.group_id
    if not (args := event.args_parse()):
        return
    prop_name, N, _ = args
    prop = prop_search(prop_name)
    if not prop:
        return f"没有【{prop_name}】这种道具。"
    account_out = manager.locate_account(event)
    account_in = manager.setdefault_account(at, group_id)
    if N < 0:
        if event.permission < 2:
            return "你送了负数的道具，请不要这样做。"
        account_out, account_in = account_in, account_out
        N = -N
        sender = "对方"
    else:
        sender = "你"

    if prop is GOLD:
        tax = int(N * 0.1)
        tip = f"消耗10%道具转换成本：{tax}，实际到账金额{N - tax}"
    else:
        tax, tip = 0, ""

    bank_out = prop.locate_user_bank(account_out)
    if prop.deal(bank_out, -N):
        return f"数量不足。\n——{sender}还有{bank_out.get(prop.object_code, 0)}个{prop.name}"
    prop.deal(prop.locate_user_bank(account_in), N - tax)
    prop.deal(manager.locate_group(group_id).bank, tax)
    return f"{account_out[1].nickname} 向 {account_in[1].nickname} 赠送{N}个{prop.name}\n{tip}"


@plugin.handle({"金币转移"}, {"user_id", "group_id"})
async def _(event: Event) -> Result:
    if not (args := event.args_parse()):
        return
    group_name, xfer_out, _ = args

    group_in = manager.group_search(group_name)
    if not group_in:
        return f"没有 {group_name} 的注册信息"
    account_in = manager.setdefault_account(event.user_id, group_in.group_id)

    group_out = manager.locate_group(event.user_id)
    account_out = manager.locate_account(event)

    if xfer_out < 0:
        account_out, account_in = account_in, account_out
        group_out, group_in = group_in, group_out
        xfer_out = -xfer_out

    def get_xfer_record(extra: dict) -> dict:
        return extra.setdefault(
            "xfers",
            {
                "record": 0,
                "limit": int((extra.get("group_gold") or company_public_gold) / 20),
            },
        )

    xfer_record_out = get_xfer_record(group_out.extra)
    limit = xfer_record_out["limit"]
    record = xfer_record_out["record"]

    info = []

    def return_info():
        return "\n".join(info)

    # 计算转出
    if limit <= abs(record - xfer_out):
        info.append(f"{group_out.name} 转出金币已到达限制：{limit}")
        if limit <= record:
            return return_info()
        xfer_out = limit - record
        info.append(f"重新转出：{xfer_out}金币")

    # 计算转入
    ExRate = group_out.level / group_in.level
    xfer_in = int(ExRate * xfer_out)

    xfer_record_in = get_xfer_record(group_in.extra)
    limit = xfer_record_in["limit"]
    record = xfer_record_in["record"]

    if limit <= record + xfer_in:
        info.append(f"{group_in.name} 转入金币已到达限制：{limit}")
        if limit <= record:
            return return_info()
        xfer_in_OK = limit - record
        xfer_out_OK = math.ceil(xfer_in_OK / ExRate)
        info.append(f"重新转入：{xfer_in_OK} 金币")
    else:
        xfer_in_OK = xfer_in
        xfer_out_OK = xfer_out

    bank_out = GOLD.locate_user_bank(account_out)
    if not GOLD.deal(bank_out, -xfer_out_OK):
        info.append(f"数量不足。\n——你还有{bank_out.get(GOLD.object_code,0)}枚金币。")
        return return_info()
    bank_in = GOLD.locate_user_bank(account_in)
    GOLD.deal(bank_in, xfer_in_OK)
    info.append(f"{group_out.name} 向 {group_in.name} 转移{xfer_out_OK}金币")
    info.append(f"汇率 {round(ExRate,2)}\n实际到账金额 {xfer_in_OK}")
    xfer_record_out["record"] -= xfer_out_OK
    xfer_record_in["record"] += xfer_in_OK

    return return_info()


@plugin.handle({"设置背景"}, {"user_id", "to_me", "image_list"})
@check_to_me.wrapper
async def _(event: Event) -> Result:
    user_id = event.user_id
    user = manager.locate_user(user_id)
    if user.bank.get(LICENSE.object_code) < 1:
        return f"你的【{LICENSE.name}】已失效"
    log = []
    BG_type = event.single_arg()
    if BG_type in {"高斯模糊", "模糊"}:
        user.extra["BG_type"] = "GAUSS"
        log.append("背景蒙版类型设置为：GAUSS")
    elif BG_type in {"无", "透明"}:
        log.append("背景蒙版类型设置为：NONE")
        user.extra["BG_type"] = "NONE"
    else:
        log.append(f"背景蒙版类型设置为：{BG_type}")
        user.extra["BG_type"] = BG_type

    if url_list := event.raw_event.kwargs["image_list"]:
        image = await download_url(url_list[0])
        if not image:
            log.append("图片下载失败")
        else:
            with open(BG_PATH / f"{event.user_id}.png", "wb") as f:
                f.write(image.getvalue())
            log.append("图片下载成功")
    return "\n".join(log) if log else None


@plugin.handle({"删除背景"}, {"user_id", "to_me"})
@check_to_me.wrapper
async def _(event: Event) -> Result:
    Path.unlink(BG_PATH / f"{event.user_id}.png", True)
    return "背景图片删除成功！"


@plugin.handle({"我的金币"}, {"user_id", "group_id"})
async def _(event: Event) -> Result:
    user = manager.locate_user(event.user_id)
    if event.is_private():
        info = []
        for group_account in user.group_accounts.values():
            group = manager.group_search(group_account.group_id)
            if not group:
                group_name = "账户已失效"
            else:
                group_name = group.name
            N = group_account.bank.get(GOLD.object_code)
            if N:
                info.append(f"【{group_name}】金币{N}枚")
        return "你的账户:\n" + "\n".join(info) if info else None
    group_account = user.connecting(event.group_id)
    return f"你还有 {group_account.bank.get(GOLD.object_code,0)} 枚金币"


@plugin.handle({"我的道具", "我的仓库"}, {"user_id", "group_id", "nickname"})
async def _(event: Event) -> Result:
    user, group_account = manager.locate_account(event)
    props = {}
    props.update(user.bank)
    props.update(group_account.bank)
    props = {k: v for k, v in props.items() if v > 0}
    flag = len(props) < 10 or event.single_arg() in {"信息", "介绍", "详情"}
    output = bank_info(props)
    info = output(font_manager, flag)
    return info_card(info, event.user_id) if info else "您的仓库空空如也。"


@plugin.handle({"群金库"}, {"user_id", "group_id", "nickname", "permission"})
async def _(event: Event) -> Result:
    if not (args := event.args_parse()):
        return
    command, N, _ = args
    group_id = event.group_id
    company = manager.get_company(group_id)
    if not company:
        return
    if command == "查看":
        company.bank = {k: v for k, v in company.bank.items() if v != 0}
        info = bank_info(company.bank)(font_manager, len(company.bank < 6))
        invest_info = []
        for stock_id, n in company.invest.items():
            stock_company = manager.get_company(stock_id)
            stock_name = stock_company.name
            stock_value = "{:,}".format(
                round(stock_company.float_gold / stock_company.issuance, 2)
            )
            invest_info.append(
                f"[pixel][20]公司 {stock_name}\n"
                f"[pixel][20]结算 [nowrap]\n[color][green]{stock_value}[nowrap]\n"
                f"[pixel][400]数量 [nowrap]\n[color][green]{n}"
            )
        invest_info.append("----\n[right][color][grey][font][][30]群金库")
        info.append(linecard("\n".join(invest_info), font_manager, 40, width=880))
        return info_card(info, event.user_id)
    sign, name = command[0], command[1:]
    if prop := prop_search(name):
        if sign == "取":
            if not event.permission:
                return f"你的权限不足。"
            N = -1
        elif sign != "存":
            return
        account = manager.locate_account(event)
        priv_check = manager.deal(account, (prop, -N), True)
        if not priv_check:
            return f"{command}失败，你还有{prop.stock(account)}个{prop.name}。"
        corp_check = manager.corp_deal(group_id, (prop, N), True)
        if not corp_check:
            return f"{command}失败，群金库还有{company.bank.get(prop.object_code)}个{prop.name}。"
        priv_check()
        corp_check()
        return f"你在群金库{sign}了{abs(N)}个{prop.name}"
    elif shares_company := manager.get_company(name):
        user, group_account = manager.locate_account(event)

    else:
        return f"没有名为【{name}】的道具或股票。"


@plugin.handle(r"^.+连抽?卡?|单抽", {"user_id", "group_id", "nickname", "to_me"})
@check_to_me.wrapper
async def _(event: Event) -> Result:
    N = re.search(r"^(.*)连抽?卡?$", event.raw_event.raw_command)
    if not N:
        return
    N = to_int(N.group(1), 1)
    N = 200 if N > 200 else 1 if N < 1 else N
    gold = N * gacha_gold
    account = manager.locate_account(event)
    if not manager.deal(account, (GOLD, -gold)):
        return f"{N}连抽卡需要{gold}金币，你的金币：{GOLD.stock(account)}。"
    bank: Bank = {}
    for _ in range(N):
        object_code = gacha()
        bank[object_code] = bank.get(object_code, 0) + 1

    data = sorted(bank.items(), key=lambda x: int(x[0][0]), reverse=True)

    def single_result(prop: Prop, n: int):
        quant = {0: "天", 1: "个"}
        return (
            f"[color][{prop.color}]{prop.name}[nowrap][passport]\n"
            f"[pixel][450]{prop.rare*'☆'}[nowrap][passport]\n"
            f"[right]{n}{quant[prop.flow]}"
        )

    prop_star, n_prop, air_star, n_air = 0, 0, 0, 0
    prop_result = []
    air_result = []
    for object_code, n in data:
        prop = prop_search(object_code)
        rare = prop.rare * n
        x = single_result(prop, n)
        if prop.domain == 1:
            air_star += rare
            n_air += n
            air_result.append(x)
        else:
            prop_star += rare
            n_prop += n
            prop_result.append(x)
            manager.deal(account, (prop, n))

    title = []
    if N >= 10:
        pt = prop_star / N
        if n_air == N:
            title = "[center][color][#003300]理 想 气 体"
            air_result.append(f"本次抽卡已免费（{gold}金币）")
            manager.deal(account, (GOLD, gold))
            manager.deal(account, (AIR_PACK, 1))
            air_result.append(single_result(AIR_PACK, n))
        elif pt < curve_fit[1](N):
            title.append("[center][color][#003300]很多空气")
        elif pt < curve_fit[2](N):
            title.append(
                "[left][color][#003333]☆[nowrap][passport]\n[center]数据异常[nowrap][passport]\n[right]☆"
            )
        elif pt < curve_fit[3](N):
            title.append(
                "[left][color][#003366]☆ ☆[nowrap][passport]\n[center]一枚硬币[nowrap][passport]\n[right]☆ ☆"
            )
        elif pt < curve_fit[4](N):
            title.append(
                "[left][color][#003399]☆ ☆ ☆[nowrap][passport]\n[center]高斯分布[nowrap][passport]\n[right]☆ ☆ ☆"
            )
        elif pt < curve_fit[5](N):
            title.append(
                "[left][color][#0033CC]☆ ☆ ☆ ☆[nowrap][passport]\n[center]对称破缺[nowrap][passport]\n[right]☆ ☆ ☆ ☆"
            )
        elif pt < curve_fit[6](N):
            title.append(
                "[left][color][#0033FF]☆ ☆ ☆ ☆ ☆[nowrap][passport]\n[center]概率之子[nowrap][passport]\n[right]☆ ☆ ☆ ☆ ☆"
            )
        else:
            title.append("[center][color][#FF0000]☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆☆")
    else:
        title.append(f"{account[1].nickname}\n" "----\n" f"抽卡次数：{N}\n" "----")
    title.append(
        "----\n"
        f"抽卡次数 {N}[nowrap]\n"
        f"[pixel][450]空气占比 {round(n_air*100/N,2)}%\n"
        f"获得☆ {prop_star}[nowrap]\n"
        f"[pixel][450]获得☆ {air_star}\n"
        f"道具平均☆ {round(air_star/n_prop,3)}[nowrap]\n"
        f"[pixel][450]空气平均☆ {round(air_star/n_air,3)}\n"
        f"数据来源：{account[1].nickname}\n"
        f"----"
    )
    result = "\n".join(
        [
            "\n".join(title),
            "\n".join(prop_result),
            "\n".join(air_result),
            "----",
            "[right][color][grey][font][][30]抽卡结果",
        ]
    )
    return linecard_to_png(
        result,
        font_manager,
        font_size=40,
        width=880,
        bg_color="#FFFFFF",
    )


"""+++++++++++++++++++++++++++++++++++++
————————————————————
   ᕱ⑅ᕱ。    超管权限指令
  (｡•ᴗ-)_
————————————————————
+++++++++++++++++++++++++++++++++++++"""


@plugin.handle({"获取金币"}, {"user_id", "group_id", "nickname", "permission"})
@check_superuser.wrapper
async def _(event: Event) -> Result:
    N = event.args_to_int()
    account = manager.locate_account(event)
    if manager.deal(account, (GOLD, N)):
        return f"你获得了 {N} 金币"
    return f"获取金币失败，你的金币不足。"


@plugin.handle({"获取道具"}, {"user_id", "group_id", "nickname", "permission"})
@check_superuser.wrapper
async def _(event: Event) -> Result:
    if not (args := event.args_parse()):
        return
    name, N, _ = args
    prop = prop_search(name)
    if not prop:
        return f"没有【{name}】这种道具。"

    account = manager.locate_account(event)
    if manager.deal(account, (prop, N)):
        return f"你获得了{N}个【{prop.name}】！"
    return f"获取道具失败，你的【{prop.name}】不足。"


@plugin.handle({"保存游戏"})
@check_superuser.wrapper
async def _(event: Event) -> Result:
    print("游戏数据已保存！")
    manager.save()
