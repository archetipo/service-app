# Copyright INRIM (https://www.inrim.eu)
# See LICENSE file for full licensing details.
from typing import List, Optional, Dict, Any, Literal, Union

from .bson_types import *
from pydantic import BaseModel, Field
from fastapi.encoders import jsonable_encoder
from slugify import slugify
from datetime import date, datetime, time, timedelta
from typing import Type, TypeVar
from pydantic import BaseModel
import ujson
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
ModelType = TypeVar("ModelType", bound=BaseModel)

default_fields = [
    "id", "owner_uid", "owner_name", "owner_function", "owner_sector",
    "create_datetime", "update_uid", "update_datetime", "owner_personal_type", "owner_job_title",
    "owner_function_type", "owner_mail"
]

list_default_fields_update = [
    "create_datetime", "update_uid", "update_datetime"]

data_fields = ["data", "data_value"]

default_data_fields = default_fields + data_fields

default_data_fields_update = list_default_fields_update + data_fields

default_list_metadata = [
    "id", "rec_name", "owner_uid", "owner_name", "owner_sector", "owner_sector_id", "owner_function", 'update_datetime',
    'create_datetime', "owner_mail",
    "owner_function_type", "sys", "demo", "deleted", "list_order", "owner_personal_type", "owner_job_title"]

default_list_metadata_fields = [
    "id", "owner_uid", "owner_name", "owner_sector", "owner_sector_id", "owner_function", 'update_datetime',
    'create_datetime', "owner_mail", "update_uid",
    "owner_function_type", "sys", "demo", "deleted", "list_order", "owner_personal_type", "owner_job_title"]


default_list_metadata_fields_update = [
    "id", "owner_uid", "owner_name", "owner_sector", "owner_sector_id", "owner_function",
    'create_datetime', "owner_mail",  "owner_personal_type", "owner_job_title", "list_order"]

export_list_metadata = [
    "owner_uid", "owner_name", "owner_function", "owner_sector", "owner_sector_id", "owner_personal_type",
    "owner_job_title", "owner_function_type", "create_datetime", "update_uid", "update_datetime", "list_order",
    "sys", "owner_mail"
]



class BasicModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = BSON_TYPES_ENCODERS


class User(BasicModel):
    uid: str
    password: str
    token: str = ""
    req_id: str = ""
    parent: str = ""
    childs: List[Any] = []
    last_update: Decimal128 = 0
    is_admin: bool = False
    is_bot: bool = False
    use_auth: bool = False
    rec_name: str = ""
    nome: str = ""
    cognome: str = ""
    mail: str = ""
    matricola: str = ""
    codicefiscale: str = ""
    data_value: Dict = {}
    allowed_users: List = []
    user_data: Dict = {}
    list_order: int = 1
    process_id: str = ""
    process_task_id: str = ""
    user_preferences: dict = {}
    user_function: str = ""
    function: str = ""
    owner_function: str = ""
    owner_sector: Optional[str] = ""
    owner_mail: Optional[str] = ""
    owner_sector_id: Optional[int] = 0
    owner_personal_type: Optional[str] = ""
    owner_job_title: Optional[str] = ""
    create_datetime: Optional[datetime]
    update_datetime: Optional[datetime]
    last_login: Optional[datetime]
    sys: bool = False
    active: bool = True
    default: bool = True
    demo: bool = False


class AttachmentTrash(BasicModel):
    rec_name: str = ""
    parent: str = ""
    childs: List[Any] = []
    model: str = ""
    model_rec_name: str = ""
    attachments: List[Dict] = []
    req_id: str = ""
    last_update: Decimal128 = 0
    list_order: int = 1
    owner_name: str = ""
    owner_uid: str = ""
    owner_function: str = ""
    owner_sector: Optional[str] = ""
    owner_mail: Optional[str] = ""
    owner_sector_id: Optional[int] = 0
    owner_personal_type: Optional[str] = ""
    owner_job_title: Optional[str] = ""
    update_uid: str = ""
    create_datetime: Optional[datetime]
    update_datetime: Optional[datetime]
    sys: bool = False
    active: bool = True
    default: bool = True
    demo: bool = False


class Component(BasicModel):
    title: str = ""
    rec_name: str = ""
    data_model: str = ""
    path: str = ""
    parent: str = ""
    parent_name: str = ""
    components: List[Dict] = []
    childs: List[Any] = []
    links: Dict = {}
    type: str = 'form'
    no_cancel: int = 0
    display: str = ""
    action: str = ""
    tags: Optional[List[str]] = []
    deleted: Decimal128 = 0.0
    list_order: int = 10
    settings: Dict = {}
    properties: Dict = {}
    data_value: Dict = {}
    handle_global_change: int = 1
    process_tenant: str = ""
    process_id: str = ""
    process_task_id: str = ""
    owner_name: str = ""
    owner_uid: str = ""
    owner_function: str = ""
    owner_sector: Optional[str] = ""
    owner_mail: Optional[str] = ""
    owner_sector_id: Optional[int] = 0
    owner_function_type: Optional[str] = ""
    owner_personal_type: Optional[str] = ""
    owner_job_title: Optional[str] = ""
    update_uid: str = ""
    create_datetime: Optional[datetime]
    update_datetime: Optional[datetime]
    make_virtual_model: bool = False
    sys: bool = False
    default: bool = False
    active: bool = True
    demo: bool = False
    projectId: str = ""  # needed for compatibility with fomriojs


class Session(BasicModel):
    parent_session: str = ""
    uid: str
    token: str = ""
    req_id: str = ""
    childs: List[Any] = []
    login_complete: bool = False
    last_update: Decimal128 = 0
    is_admin: bool = False
    use_auth: bool = False
    is_public: bool = False
    full_name: str = ""
    divisione_uo: str = ""
    user_function: str = ""
    function: str = ""
    sector: Optional[str] = ""
    sector_id: Optional[int] = 0
    user: dict = {}
    app: dict = {}
    queries: dict = {}
    action: dict = {}
    server_settings: dict = {}
    record: dict = {}
    list_order: int = 1
    user_preferences: dict = {}
    owner_function: str = ""
    owner_sector: Optional[str] = ""
    owner_mail: Optional[str] = ""
    owner_sector_id: Optional[int] = 0
    owner_personal_type: Optional[str] = ""
    owner_job_title: Optional[str] = ""
    expire_datetime: datetime
    create_datetime: datetime
    update_datetime: Optional[datetime]
    sys: bool = False
    active: bool = True
    default: bool = True
    demo: bool = False


def update_model(source, object_o, pop_form_newobject=[], model=None):
    new_dict = ujson.loads(object_o.json())
    new_dict['id'] = source.dict()['id']
    if model is not None:
        object_o = model(**new_dict)
    else:
        object_o = type(source)(**new_dict)
    return object_o
