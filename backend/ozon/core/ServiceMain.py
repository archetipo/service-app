# Copyright INRIM (https://www.inrim.eu)
# See LICENSE file for full licensing details.
import sys
import os
from os import listdir
from os.path import isfile, join
import ujson
from ozon.settings import get_settings
from .database.mongo_core import *
from collections import OrderedDict
from pathlib import Path
from fastapi import Request
from .ServiceSecurity import ServiceSecurity
from .ServiceAction import ServiceAction
from .ServiceActionTask import ActionTask
from .ServiceMenuManager import ServiceMenuManager
from .QueryEngine import QueryEngine
from .ModelData import ModelData
from .BaseClass import BaseClass, PluginBase
from pydantic import ValidationError
import logging
import pymongo
import requests
import httpx
import uuid

logger = logging.getLogger(__name__)


# basedir = os.path.abspath(os.path.dirname(__file__))
# UPLOAD_FOLDER = f'/uploads'
# Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

class ServiceMain(PluginBase):
    plugins = []

    def __init_subclass__(cls, **kwargs):
        cls.plugins.append(cls())


class ServiceBase(ServiceMain):

    @classmethod
    def create(
            cls, request
    ):
        self = ServiceBase()
        self.init(request)
        return self

    def init(self, request):
        self.session = request.scope['ozon'].session
        self.pwd_context = request.scope['ozon'].pwd_context
        self.action_service = None
        self.mdata = ModelData.new(session=self.session, pwd_context=self.pwd_context)
        self.menu_manager = ServiceMenuManager.new(session=self.session, pwd_context=self.pwd_context)
        self.acl = ServiceSecurity.new(session=self.session, pwd_context=self.pwd_context)
        self.qe = QueryEngine.new(session=self.session)
        self.asc = 1
        self.desc = -1

    async def service_handle_action(
            self, action_name: str, data: dict = {}, rec_name: str = "",
            parent="", iframe="", execute=False, container_act=""):
        logger.info(f"service_handle_action -> name:{action_name}, rec_name:{rec_name}, "
                    f"execute:{execute}, data:{data.keys()}, container_act: {container_act}")
        if not data:
            data = {
                "limit": 0,
                "skip": 0,
                "sort": "",
                "query": {}
            }

        self.action_service = ServiceAction.new(
            session=self.session, service_main=self, action_name=action_name,
            rec_name=rec_name, parent=parent, iframe=iframe, execute=execute,
            pwd_context=self.pwd_context, container_act=container_act
        )

        return {
            "settings": {
                "app_name": get_settings().app_name,
                "app_version": get_settings().app_version,
                "logo_img_url": get_settings().logo_img_url
            },
            "menu": await self.menu_manager.make_main_menu(),
            "content": await self.action_service.compute_action(data=data)
        }

    async def service_get_layout(self, name):
        logger.info("service_get_default_layout")
        if not name:
            name = self.session.app.get("layout")
        else:
            session.app['layout'] = name
        layout = await search_by_name(Component, rec_name=name)
        return {
            "settings": {
                "app_name": get_settings().app_name,
                "app_version": get_settings().app_version,
                "logo_img_url": get_settings().logo_img_url
            },
            "menu": await self.menu_manager.make_main_menu(),
            "schema": layout
        }

    async def service_get_dashboard(self):
        logger.info("service_get_dashboard")
        return {
            "model": "action",
            "content": {"cards": await self.menu_manager.make_dashboard_menu()}
        }

    async def service_get_schema(self, model_name):
        logger.info(f"service_get_schema by name {model_name}")
        # TODO add check rules for model
        schema = await self.mdata.component_by_name(model_name)
        return schema or {}

    async def service_get_schema_model(self, model_name):
        logger.info(f"service_get_schema by name {model_name}")
        schema_model = await self.mdata.gen_model(model_name)
        if not schema_model.schema():
            return {}
        schema = schema_model.schema()
        model_fields_names = [k for k, v in schema['properties'].items()]
        fields = [item for item in model_fields_names if item not in default_list_metadata_fields]
        if "data_value" in fields:
            fields.remove("data_value")
        res = {
            "schema": schema,
            "fields": fields,
            "metadata": default_list_metadata_fields
        }
        return res

    async def service_reorder_record(self, data):
        logger.info(f"service_reorder_record by name {data}")
        # TODO add check rules for model
        model_data = await self.mdata.gen_model(data['model_name'])
        list_to_save = []
        for record_data in data['columns']:
            record = await self.mdata.by_name(model_data, record_data['key'])
            record.list_order = record_data['value']
            if not data['model_name'] == "component":
                record.data_value['list_order'] = record_data['value']
            list_to_save.append(record)
        await self.mdata.save_all(list_to_save, remove_meta=False)
        return {"status": "ok"}

    async def service_get_schemas_by_type(self, schema_type="form", query={}, fields=[], additional_key=[]):
        logger.info(
            f"service_get_schemas_by_type  schema_type:{schema_type}, query:{query}, "
            f"fields:{fields},additional_key:{additional_key}"
        )
        # TODO add check rules
        query = {
            "$and": [
                {"deleted": 0},
                {"type": {"$eq": schema_type}}
            ]
        }
        data = await self.mdata.all_distinct(
            Component, "rec_name", query=query, additional_key=additional_key)
        return {
            "content": {
                "data": data or [],
            }
        }

    async def service_get_schemas_by_parent_and_type(
            self, parent_model, schema_type="form", fields=[], additional_key=[]):
        logger.info(f"service_get_schema by name {parent_model}")
        # TODO add check rules parent_model
        query = {
            "$and": [
                {"parent": {"$eq": parent_model}},
                {"deleted": 0}
            ]
        }
        data = await self.mdata.get_list_base(
            Component, fields=fields, query=query, model_type=schema_type, additional_key=additional_key)
        return {
            "content": {
                "data": data or [],
            }
        }

    async def service_get_data_for_model(
            self, model_name, query={}, fields=[], additional_key=[]):
        logger.info(f"get_data_model {model_name}")
        # TODO add check read rules model_name
        data_model = await self.mdata.gen_model(model_name)
        query = self.qe.default_query(
            data_model, query)
        data = await self.mdata.get_list_base(
            data_model, fields=fields, query=query)
        return {
            "content": {
                "data": data or []
            }
        }

    async def service_get_record(self, model_name, rec_name):
        logger.info(f"service_get_schema by name model_name:{model_name}, rec_name:{rec_name}")
        # TODO add check read rules for model
        schema = await self.mdata.component_by_name(model_name)
        data_model = await self.mdata.gen_model(model_name)
        data = await self.mdata.by_name(
            data_model, record_name=rec_name)
        if not data:
            data = data_model(**{})
        can_edit = await self.acl.can_update(schema, data)
        return {
            "content": {
                "editable": can_edit,
                "model": model_name,
                "schema": schema or {},
                "data": data or {},
            }
        }

    async def service_component_distinct_model(self):
        logger.info(f"service_component_distinct_model")
        # TODO add check read rules for model
        query = {
            "$and": [
                # {"type": {"$eq": "form"}},
                {"deleted": 0},
                {"data_model": {"$eq": ""}}
            ]
        }
        data = await self.mdata.all_distinct(
            Component, "rec_name", query=query)
        return {
            "content": {
                "data": data or [],
            }
        }

    async def service_distinct_rec_name_by_model(
            self, model_name="component", domain={}, props={}):
        logger.info(
            f"service_component_distinct_model model_name:{model_name}, domain:{domain}, props:{props}")
        # TODO add check read rules for model
        data = []
        if model_name:
            model_data = await self.mdata.gen_model(model_name)
            data = await self.mdata.all_distinct(
                model_data, "rec_name", query=domain, compute_label=props.get("compute_label", ""))
            if model_name == "component":
                data.append(
                    {
                        "_id": "component",
                        "rec_name": "component",
                        "title": "Component",
                        "type": ""
                    },
                )
        return {
            "content": {
                "data": data or [],
            }
        }

    async def service_freq_for_field_model(
            self, model_name="", field="", field_query={}, min_occurence=2, add_fields="", sort=-1):
        logger.info(
            f"gen freq model_name:{model_name}, field:{field}, field_query:{field_query}, min_occurence: {min_occurence}")

        data = []
        if model_name and field:
            model_data = await self.mdata.gen_model(model_name)
            data = await self.mdata.freq_for_all_by_field_value(
                model_data, field=field, field_query=field_query, min_occurence=min_occurence, add_fields=add_fields,
                sort=sort)
        return {
            "content": {
                "data": data or [],
            }
        }

    async def get_remote_data_select(self, url, path_value, header_key, header_value_key):
        if path_value:
            url = f"{url}/{path_value}"
        header_value = get_settings().get_by_name(header_value_key)
        headers = {}
        remote_data = await self.get_remote_data(headers, header_key, header_value, url)
        return {
            "content": {
                "data": remote_data or [],
            }
        }

    async def get_remote_data(self, headers, header_key, header_value, url):
        logger.info(f"server get_remote_data --> {url}, header_key:{header_key}, header_value:{header_value} ")
        headers.update({
            "Content-Type": "application/json",
            header_key: header_value
        })
        async with httpx.AsyncClient(timeout=None) as client:
            res = await client.get(
                url=url, headers=headers
            )
        if res.status_code == 200:
            logger.info(f"server get_remote_data --> {url} SUCCESS ")
            return res.json()
        else:
            logger.info(f"server get_remote_data --> {url} Error {res.status_code} ")
            return {}

    async def export_data(self, model_name, datas, parent_name=""):
        logger.info(f" model:{model_name}, query:{datas}, parent_name:{parent_name}")
        # data_mode = json | value
        data_mode = datas.get('data_mode', 'json')

        data_model = await self.mdata.gen_model(model_name)
        query = self.qe.default_query(data_model, datas['query'])

        if model_name == 'component':
            model = await self.mdata.gen_model(model_name)
            list_schema = await self.mdata.search_base(model, query=query)
            if list_schema:
                schema_dict = list_schema[0]
                schema = BaseClass(**schema_dict)
        else:
            schema = await self.mdata.component_by_name(model_name)

        if not data_mode == 'json':
            data = await self.mdata.search_export(
                data_model, fields=['data_value'], merge_field="data_value", query=query, parent=parent_name,
                remove_keys=["_id", "id"]
            )
        else:
            if schema.sys:
                to_rm = default_fields[:]
            else:
                to_rm = []
            to_rm.append("_id")
            data = await self.mdata.search_export(
                data_model, fields=[], query=query, parent=parent_name, remove_keys=to_rm)
        logger.info(f"export {len(data)} lines")
        return {
            "content": {
                "model": model_name,
                "schema": schema or {},
                "data": data or {},
            }
        }

    async def import_raw_data(self, model_name, record_data):
        data_model = await self.mdata.gen_model(model_name)
        record = data_model(**record_data)
        object_o = await self.mdata.save_object(
            self.session, record, model_name=model_name, copy=False)

        if isinstance(object_o, dict):
            return object_o
        return {
            "status": "ok",
            "rec_name": object_o.rec_name,
            "model": model_name
        }

    async def get_mail_template(self, model_name, template_name=""):
        logger.info(f" model:{model_name}, template_name:{template_name}")
        # data_mode = json |

        template_model = await self.mdata.gen_model("mail_template")
        query = {"$and": [{"model": model_name}, {"default": True}]}
        if template_name:
            query = {"rec_name": template_name}
        query = self.qe.default_query(template_model, query)

        list_template = await self.mdata.search(template_model, query=query)
        tmp_dict = {}
        if list_template:
            tmp_dict = list_template[0]

        return {
            "content": {
                "model": model_name,
                "data": tmp_dict or {},
            }
        }

    async def get_mail_server_out(self, server_name=""):
        logger.info(f" server_name:{server_name}")

        server_model = await self.mdata.gen_model("mail_server_out")

        query = self.qe.default_query(server_model, {"rec_name": server_name})

        list_server = await self.mdata.search(server_model, query=query)
        server_dict = {}
        if list_server:
            server_dict = list_server[0]

        return {
            "content": {
                "model": "mail_server_out",
                "data": server_dict or {},
            }
        }

    async def attachment_to_trash(self, model_name, rec_name, data):
        logger.info(f"model:{model_name}, rec_name:{rec_name}")
        # data_mode = json | value
        try:
            key = data.get('key')
            file_field = data.get("field")

            data_model = await self.mdata.gen_model(model_name)
            trash_model = await self.mdata.gen_model("attachment_trash")
            record = await self.mdata.by_name(
                data_model, record_name=rec_name)
            record_dict = record.dict()

            list_files = []
            rec_to_save = []
            for file_todo in record_dict[file_field]:
                if not file_todo['key'] == key:
                    list_files.append(file_todo)
                else:
                    rec_to_save.append(file_todo)
            record_dict[file_field] = list_files[:]
            new_record = data_model(**record_dict)

            trash = trash_model(**{
                "rec_name": f"trash.{str(uuid.uuid4())}",
                "model": model_name,
                "model_rec_name": rec_name,
                "attachments": rec_to_save[:],
            })
            record = await self.mdata.save_object(
                self.session, trash, rec_name="", model_name="attachment_trash")
            # if error record is dict
            if isinstance(record, dict):
                return record
            await self.mdata.save_record(new_record)
            return {
                "link": "#",
                "reload": True
            }
        except Exception as e:
            logger.error(e)
            return {
                "status": "error",
                "message": f"Errore  {e}",
                "model": model_name,
                "rec_name": rec_name
            }

    async def clean_all_to_delete_action(self):
        logger.info(f"clean expired to_delete_action ")
        return await self.mdata.clean_expired_to_delete_record()
