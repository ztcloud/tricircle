# Copyright (c) 2015 Huawei Tech. Co., Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
from mock import patch
import six
import unittest

import pecan

from tricircle.api.controllers import pod
from tricircle.common import context
from tricircle.common import policy
from tricircle.db import core
from tricircle.db import models


class PodsControllerTest(unittest.TestCase):
    def setUp(self):
        core.initialize()
        core.ModelBase.metadata.create_all(core.get_engine())
        self.controller = pod.PodsController()
        self.context = context.get_admin_context()
        policy.populate_default_rules()

    @patch.object(context, 'extract_context_from_environ')
    def test_post_top_pod(self, mock_context):
        mock_context.return_value = self.context
        kw = {'pod': {'region_name': 'TopPod', 'az_name': ''}}
        pod_id = self.controller.post(**kw)['pod']['pod_id']

        with self.context.session.begin():
            pod = core.get_resource(self.context, models.Pod, pod_id)
            self.assertEqual('TopPod', pod['region_name'])
            self.assertEqual('', pod['az_name'])
            pods = core.query_resource(self.context, models.Pod,
                                       [{'key': 'region_name',
                                         'comparator': 'eq',
                                         'value': 'TopPod'}], [])
            self.assertEqual(1, len(pods))

    @patch.object(context, 'extract_context_from_environ')
    def test_post_bottom_pod(self, mock_context):
        mock_context.return_value = self.context
        kw = {'pod': {'region_name': 'BottomPod', 'az_name': 'TopAZ'}}
        pod_id = self.controller.post(**kw)['pod']['pod_id']

        with self.context.session.begin():
            pod = core.get_resource(self.context, models.Pod, pod_id)
            self.assertEqual('BottomPod', pod['region_name'])
            self.assertEqual('TopAZ', pod['az_name'])
            pods = core.query_resource(self.context, models.Pod,
                                       [{'key': 'region_name',
                                         'comparator': 'eq',
                                         'value': 'BottomPod'}], [])
            self.assertEqual(1, len(pods))

    @patch.object(context, 'extract_context_from_environ')
    def test_get_one(self, mock_context):
        mock_context.return_value = self.context
        kw = {'pod': {'region_name': 'TopPod', 'az_name': ''}}
        pod_id = self.controller.post(**kw)['pod']['pod_id']

        pod = self.controller.get_one(pod_id)
        self.assertEqual('TopPod', pod['pod']['region_name'])
        self.assertEqual('', pod['pod']['az_name'])

    @patch.object(context, 'extract_context_from_environ')
    def test_get_all(self, mock_context):
        mock_context.return_value = self.context
        kw1 = {'pod': {'region_name': 'TopPod', 'az_name': ''}}
        kw2 = {'pod': {'region_name': 'BottomPod', 'az_name': 'TopAZ'}}
        self.controller.post(**kw1)
        self.controller.post(**kw2)

        pods = self.controller.get_all()
        actual = [(pod['region_name'],
                   pod['az_name']) for pod in pods['pods']]
        expect = [('TopPod', ''), ('BottomPod', 'TopAZ')]
        six.assertCountEqual(self, expect, actual)

    @patch.object(pecan, 'response', new=mock.Mock)
    @patch.object(context, 'extract_context_from_environ')
    def test_delete(self, mock_context):
        mock_context.return_value = self.context
        kw = {'pod': {'region_name': 'BottomPod', 'az_name': 'TopAZ'}}
        pod_id = self.controller.post(**kw)['pod']['pod_id']
        self.controller.delete(pod_id)

        with self.context.session.begin():
            pods = core.query_resource(self.context, models.Pod,
                                       [{'key': 'region_name',
                                         'comparator': 'eq',
                                         'value': 'BottomPod'}], [])
            self.assertEqual(0, len(pods))

    def tearDown(self):
        core.ModelBase.metadata.drop_all(core.get_engine())
        policy.reset()
