from .core.data import Bank
from .core.clovers import Event
from .library import prop_search
from .utils.linecard import FontManager, linecard_to_png, linecard, info_splicing


def bank_info(bank: Bank):
    data = sorted(bank.items(), key=lambda x: int(x[0][0]))

    def output(font_manager: FontManager, detailed: bool = False):
        if detailed:

            def result(object_code: str, n):
                prop = prop_search(object_code)
                quant = {0: "天", 1: "个"}[prop.flow]
                return linecard(
                    (
                        f"[color][{prop.color}]【{prop.name}】[nowrap][passport]\n[right]{'{:,}'.format(n)}{quant}\n"
                        "----\n"
                        f"[font][][40]{prop.intro.replace('\n','[passport]\n')}\n[font][][40][right]{prop.tip}"
                    ),
                    font_manager,
                    60,
                    width=880,
                    padding=(0, 20),
                    autowrap=True,
                )

            info = [result(*args) for args in data]
        else:

            def result(object_code, n):
                prop = prop_search(object_code)
                quant = {0: "天", 1: "个"}[prop.flow]
                return f"[color][{prop.color}]【{prop.name}】[nowrap][passport]\n[right]{'{:,}'.format(n)}{quant}"

            info = [
                linecard(
                    "\n".join(result(*args) for args in data),
                    font_manager,
                    60,
                    width=880,
                    padding=(0, 0),
                    spacing=1.0,
                )
            ]
        return info

    return output
