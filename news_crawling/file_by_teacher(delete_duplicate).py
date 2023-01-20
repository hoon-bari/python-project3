import uuid
from typing import Union, AnyStr, Sequence, Mapping, Any
import pandas as pd

ObjectMappingType = Mapping[Union[AnyStr, int, float], Any]
PRIMITIVE_TYPE = (int, float, bytes, str, bool)


def obj_to_table(_obj: Union[list, dict], as_df=False, main_table_key='main'):
    if isinstance(_obj, list):
        main, new_item = list_to_table(_obj)
    elif isinstance(_obj, dict):
        main, new_item = dict_to_table(_obj)
    else:
        raise ValueError("param _obj는 dict 또는 list 타입이어야만 합니다.")
    _result = {
        'main_table_key': main,
        **new_item
    }
    if as_df:
        for table_name in _result:
            _result[table_name] = pd.DataFrame(_result[table_name])

    return _result


def list_to_table(_list: list, table_name=None, rel_table_name: str = None, rel_id=None):
    """list 는 새로운 new_table 이 나온다"""
    new_list = []

    new_table_dict = {}
    for item in _list:
        if isinstance(item, PRIMITIVE_TYPE):
            new_list.append({
                f'_rel_{rel_table_name}_id': rel_id,
                'value': item
            })
        if isinstance(item, dict):
            new_item, _new_table_dict = dict_to_table(item, table_name=table_name)
            if rel_table_name is not None:
                new_item[f'_rel_{rel_table_name}_id'] = rel_id
            new_list.append(new_item)
            for k in _new_table_dict:
                if k in new_table_dict:
                    if not isinstance(new_table_dict[k], list):
                        new_table_dict[k] = [new_table_dict[k]]

                    if not isinstance(_new_table_dict[k], list):
                        _new_table_dict[k] = [_new_table_dict[k]]

                    new_table_dict[k].extend(_new_table_dict[k])
                else:
                    new_table_dict[k] = _new_table_dict[k]

    return new_list, new_table_dict


def dict_to_table(_dict, parent_key: str = None, _id=None, table_name=None):
    if _id is None:
        _id = str(uuid.uuid4())
    if table_name is None:
        table_name = 'main'
    new_dict = {}

    new_table_dict = {}

    pre_key = ''
    if parent_key:
        pre_key = f'{parent_key}.'

    for k in _dict:
        new_key = pre_key + str(k)
        if isinstance(_dict[k], PRIMITIVE_TYPE):
            new_dict[new_key] = _dict[k]
        if isinstance(_dict[k], dict):
            nested_dict, new_table = dict_to_table(_dict[k], parent_key=new_key, _id=_id, table_name=table_name)
            new_dict.update(nested_dict)
            new_table_dict.update(new_table)
        if isinstance(_dict[k], list):
            new_table, _new_table_dict = list_to_table(_dict[k], table_name=new_key, rel_table_name=table_name,
                                                       rel_id=_id)
            new_table_dict[new_key] = new_table
            new_table_dict.update(_new_table_dict)
    if '_table_id' not in new_dict:
        new_dict['_table_id'] = _id

    return new_dict, new_table_dict