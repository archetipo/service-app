# Copyright INRIM (https://www.inrim.eu)
# See LICENSE file for full licensing details.
import sys
from copy import deepcopy
import logging
import ujson
from .builder_custom import *
from .widgets_content import PageWidget, BaseClass
from .base.base_class import PluginBase
import uuid
import re

logger = logging.getLogger(__name__)


class DashboardCardWidget(PageWidget):
    @classmethod
    def create(
            cls, templates_engine, session, request, settings, **kwargs):
        self = DashboardCardWidget()
        self.init(
            templates_engine, session, request, settings, disabled=False, **kwargs)
        logger.info("DashboardCardWidget init complete")
        return self

    def render_actions(self, list_actions):
        actions = []
        for action in list_actions:
            action['customClass'] = " d-inline-block  mr-3 mt-3 "
            actions.append(
                self.render_custom(
                    self.theme_cfg.get_template("components", 'htmlelement'),
                    action.copy()
                )
            )
        return actions

    def chunks(self, l, n):
        n = max(1, n)
        return (l[i:i + n] for i in range(0, len(l), n))

    def render_row_actions(self, list_actions):
        actions = self.render_actions(list_actions)
        # rows = self.chunks(actions, 3)
        cfg = {'rows': actions, 'customClass': "col-12 text-center mt-3"}
        row = self.render_custom(
            self.theme_cfg.get_template("components", 'card_base_act_row'),
            cfg.copy()
        )
        return row

    def render_card(self, cards_data):
        row = self.render_row_actions(cards_data.get("buttons"))
        cfg = {
            'title': cards_data.get("title"),
            'cls': " col-lg-3 ",
            'tit_cls': "text-center",
            'text_cls': "text-center",
            'items': row
        }
        card = self.render_custom(
            self.theme_cfg.get_template("components", 'card_base'),
            cfg.copy()
        )
        return card


class DashboardWidget(PluginBase):
    plugins = []

    def __init_subclass__(cls, **kwargs):
        cls.plugins.append(cls())


class DashboardWidgetBase(DashboardWidget, PageWidget):

    @classmethod
    def create(
            cls, templates_engine, session, request, settings, content, **kwargs):
        self = DashboardWidgetBase()
        self.content = deepcopy(content)
        self.init(
            templates_engine, session, request, settings, disabled=False, **kwargs)
        self.cards_data = self.content.get("cards")[:]
        self.card_widget = DashboardCardWidget.create(
            templates_engine=templates_engine, request=request,
            session=session, settings=settings
        )
        logger.info("DashboardWidget init complete")
        return self


    def make_row(self, row_cards_data):
        cards_html = []
        for card in row_cards_data:
            cards_html.append(self.card_widget.render_card(card))

        cfg = {"rows": cards_html[:], "customClass": "mt-0"}
        card_row = self.render_custom(
            self.theme_cfg.get_template("components", 'cards_row'),
            cfg.copy()
        )
        return card_row

    def make_dashboard(self):
        logger.info("make_dashboard")
        card_row = self.make_row(self.cards_data)

        return self.render_custom(
            self.theme_cfg.get_template("components", 'card_base_container'),
            {"rows": [card_row]}
        )
