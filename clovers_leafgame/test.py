from typing_extensions import Unpack
from pydantic import BaseModel
from typing import Any
import json
from collections.abc import Callable


class ModelB(BaseModel):
    name: str = None
    data: int = 0


class ModelA(BaseModel):
    name: str = None
    B_dict: dict[Any, ModelB] = {}
    func = lambda: 10


a = ModelA()
a.name = "karisaya"
a.B_dict["1"] = ModelB(name="hello", data=1)
a.B_dict["2"] = ModelB(name="wrold", data=2)
print(a)
json_a = a.model_dump_json(indent=4)
print(json_a)
# data_a = json.loads(json_a)
# print(data_a)
# print(data_a)

# print(ModelA.model_validate(data_a))
# # print(ModelA.parse_obj(data))
