# Copyright INRIM (https://www.inrim.eu)
# See LICENSE file for full licensing details.
import logging
import uuid
from .BaseClass import BaseClass, PluginBase
from .ModelData import ModelData
from .database.mongo_core import *

logger = logging.getLogger(__name__)


class ServiceSecurity(PluginBase):
    plugins = []

    def __init_subclass__(cls, **kwargs):
        cls.plugins.append(cls())


class SecurityBase(ServiceSecurity):

    @classmethod
    def create(cls, session: Session = None, pwd_context=None):
        self = SecurityBase()
        self.init(session, pwd_context)
        return self

    def init(self, session, pwd_context):
        self.session = session
        self.pwd_context = pwd_context
        self.mdata = ModelData.new(session=self.session, pwd_context=self.pwd_context)

    # il modello ACL e' collogato al singolo componente
    # nel caso un model sia figlio di un altro model
    # le policy rules vengono copiate dal parent e poi possono essere modificate
    # si po' ad esempio dare un accesso ad un form di un progetto con restrizioni
    # ma lo si potra' raggiungere solo con un link diretto.

    # TODO imp load schema and eval from rule model
    async def can_create(self, schema: BaseModel, data: BaseModel, action=None):
        logger.debug(
            f"ACL can_create {self.session.user.get('uid')} -> {data.owner_uid} | user Admin {self.session.is_admin}")
        editable = False

        if data.owner_uid == self.session.user.get('uid') or self.session.user_function == "resp":
            editable = True

        if self.session.is_admin:
            return True

        logger.debug(f"ACL can_edit {self.session.user.get('uid')} ->  {readable}")
        return editable

    async def can_read(self, action=None):
        logger.debug(
            f"ACL can_read {self.session.user.get('uid')}, user Admin {self.session.is_admin}, action {action.rec_name}")
        readable = True

        if action.no_public_user and self.session.is_public:
            readable = False

        logger.debug(f"ACL can_read {self.session.user.get('uid')} ->  {readable}")
        return readable

    async def can_update(self, schema: BaseModel, data: BaseModel, action=None):
        logger.debug(
            f"ACL can_update req user: {self.session.user.get('uid')} -> data owner: {data.owner_uid},"
            f" req user Admin: {self.session.is_admin}"
        )

        editable = False

        if data.owner_uid == self.session.user.get('uid') or (
                self.session.function == "resp" and data.owner_sector_id == self.session.sector_id):
            editable = True

        if not data.rec_name:
            editable = True

        if self.session.is_admin:
            editable = True

        logger.debug(f"ACL can_edit {self.session.user.get('uid')} ->  {editable}")
        return editable

    async def can_update_fields(self, schema: BaseModel, data: BaseModel, action=None):
        logger.debug(f"ACL Fields")
        fields = []
        logger.info(f"ACL editable_fields {self.session.user.get('uid')} ->  {fields}")
        return fields

    async def can_delete(self, schema: BaseModel, data: BaseModel, action=None):
        logger.debug(
            f"ACL can_delete {self.session.user.get('uid')} -> {data.owner_uid} | user Admin {self.session.is_admin}")

        editable = False

        if data.owner_uid == self.session.user.get('uid') or self.session.user_function == "resp":
            editable = True
        if self.session.is_admin:
            return True

        logger.debug(f"ACL can_edit {self.session.user.get('uid')} ->  {editable}")
        return editable

    async def make_user_action_query(self):
        logger.debug(
            f"ACL user_action_query {self.session.user.get('uid')}  | user Admin {self.session.is_admin}")
        query_list = []
        user = self.session.user
        if self.session.is_admin:
            return []

        function = user.get('user_function')
        query_list.append({"admin": False, "sys": False})
        if function == "resp":
            query_list.append({
                "user_function": {"$elemMatch": {"$eq": ['user', 'resp']}}
            })
        else:
            query_list.append({"user_function": "user"})
        if self.session.is_public:
            query_list.append({"no_public_user": False})

        return query_list
