import os
import json
import random
import numpy as np
from pathlib import Path
from .core.data import Prop

resource_file = Path(os.path.join(os.path.dirname(__file__), "./resource"))


with open(resource_file / "props_library.json", "r", encoding="utf8") as f:
    props_library: dict[str, Prop] = {k: Prop(k, **v) for k, v in json.load(f).items()}

props_index = {}
props_index.update({v.name: k for k, v in props_library.items()})
props_index.update({k: k for k in props_library})


def prop_search(prop_name: str):
    if not (prop_code := props_index.get(prop_name)):
        return

    return props_library[prop_code]


GOLD = props_library["12101"]
VIP_CARD = props_library["42001"]
RED_PACK = props_library["52103"]
AIR = props_library["11001"]
AIR_PACK = props_library["03103"]
LICENSE = props_library["33001"]

prop_pool = {}
prop_pool[3] = ["优质空气", "四叶草标记", "挑战徽章", "设置许可证", "初级元素"]
prop_pool[4] = ["高级空气", "铂金会员卡"]
prop_pool[5] = [
    "特级空气",
    "进口空气",
    "10%结算补贴",
    "10%额外奖励",
    "神秘天平",
    "幸运硬币",
]
prop_pool[6] = ["纯净空气", "钻石", "道具兑换券", "超级幸运硬币", "重开券"]

for k, v in prop_pool.items():
    prop_pool[k] = [prop_search(i).object_code for i in v]


def gacha() -> str:
    """
    随机获取道具。
        return: object_code
    """
    rand = random.uniform(0.0, 1.0)
    prob_list = [0.3, 0.1, 0.1, 0.02]
    rare = 3
    for prob in prob_list:
        rand -= prob
        if rand <= 0:
            break
        rare += 1
    if rare_pool := prop_pool.get(rare):
        return random.choice(rare_pool)
    return "11001"


curve_fit = {
    1: lambda x: 0.339438628551138 * np.log(2.7606559801569316e-13 * x)
    + -0.0012286453324789554 * x
    + 9.310675305999386,
    2: lambda x: 0.2622830460672209 * np.log(1.0565997436401555e-10 * x)
    + -0.0013800074822243364 * x
    + 6.079586419253099,
    3: lambda x: 0.16563555661021917 * np.log(652.209392293454 * x)
    + -0.0009688421476907207 * x
    + -0.5084815403474984,
    4: lambda x: -0.11977280212351049 * np.log(3.53822027614143e-11 * x)
    + 0.0005645672140693966 * x
    + -0.9186502372819698,
    5: lambda x: -0.27071466714377795 * np.log(1.2743174700041504e-11 * x)
    + 0.0014031052967047675 * x
    + -4.106094299018067,
    6: lambda x: -0.5213387432196357 * np.log(16.300736342820436 * x)
    + 0.0027842719423569447 * x
    + 5.3464181044586425,
}
