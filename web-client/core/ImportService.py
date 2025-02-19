# Copyright INRIM (https://www.inrim.eu)
# See LICENSE file for full licensing details.
import httpx
import logging
import ujson
import json
from fastapi.responses import RedirectResponse, FileResponse, StreamingResponse
from datetime import datetime, timedelta
from .main.base.base_class import BaseClass, PluginBase
from .MailService import MailService
import shutil
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from .main.widgets_content import PageWidget
from jinja2 import Template
import pandas as pd
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


# https://github.com/TonyGermaneri/canvas-datagrid

class ImportService(MailService):

    @classmethod
    def create(cls, gateway, remote_data):
        self = ImportService()
        self.init(gateway, remote_data)
        return self

    async def import_data(self, data_model, submit_data):
        logger.info(f" {data_model}")
        res_err = []
        res_ok = []

        schema_model = await self.gateway.get_remote_object(f"/schema_model/{data_model}")
        if not schema_model:
            return {"status": "error", "msg": "Errore nel Form"}
        model_fields_names = schema_model['fields']
        file_fields_names = [row['name'] for row in submit_data['fields']]
        if not all(item in model_fields_names for item in file_fields_names):
            return {
                "status": "error",
                "msg": "Impossibile importate il documento, i campi non coincidono, scaricare il templete e compilare"
            }
        schama = schema_model['schema']
        field_types = {k: schama['properties'][k]['type'] for k, v in schama['properties'].items()}
        typesd = {
            "array": list,
            "object": dict,
        }

        for row in submit_data['data']:
            row_data = {}
            for k, v in row.items():
                if field_types[k] in typesd and not type(v) == typesd[field_types[k]]:
                    row_data[k] = eval(v)
                else:
                    row_data[k] = v
            if data_model == "component":
                import_data = row_data.copy()
            else:
                import_data = await self.form_post_handler(row_data)
            server_response = await self.gateway.post_remote_object(
                f"/import/{data_model}", data=import_data)
            if "error" in server_response.get('status', ""):
                res_err.append(server_response)
            else:
                res_ok.append(server_response)

        response_import = {
            "status": "done",
            "ok": len(res_ok),
            "error": len(res_err),
            "error_list": res_err[:]
        }
        return response_import.copy()

    async def template_xls(self, data_model, with_data=False):
        logger.info("template Xls")
        dt_report = datetime.now().strftime(
            self.gateway.local_settings.server_datetime_mask
        )
        schema_model = await self.gateway.get_remote_object(f"/schema_model/{data_model}")
        if not schema_model:
            return {"status": "error", "msg": "Errore nel Form"}
        model_fields_names = schema_model['fields']
        data = {}
        if with_data:
            data_res = await self.gateway.get_remote_object(
                f"/resource/data/{data_model}?fields={','.join(model_fields_names)}")
            data = data_res.get("content", {}).get("data", {})
        file_name = f"{data_model}_{dt_report}.xlsx"
        df = pd.DataFrame(data, columns=model_fields_names)
        buffer = BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, header=model_fields_names, index=False)
        buffer.seek(0)

        headers = {
            'Content-Disposition': f'attachment; filename="{file_name}"'
        }
        return StreamingResponse(buffer, headers=headers)
