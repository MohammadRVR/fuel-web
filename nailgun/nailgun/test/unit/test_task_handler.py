# -*- coding: utf-8 -*-
#    Copyright 2013 Mirantis, Inc.
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

from nailgun import consts
from nailgun.db.sqlalchemy.models import Task
from nailgun.test.base import BaseTestCase
from nailgun.utils import reverse


class TestTaskHandlers(BaseTestCase):

    def setUp(self):
        super(TestTaskHandlers, self).setUp()
        self.env.create(
            nodes_kwargs=[
                {"roles": ["controller"]}
            ]
        )
        self.cluster_db = self.env.clusters[0]

    def test_task_deletion(self):
        task = Task(
            name='deployment',
            cluster=self.cluster_db,
            status=consts.TASK_STATUSES.ready,
            progress=100
        )
        self.db.add(task)
        self.db.flush()
        resp = self.app.delete(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ),
            headers=self.default_headers
        )
        self.assertEqual(resp.status_code, 204)
        resp = self.app.get(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status_code, 404)

    def test_running_task_deletion(self):
        task = Task(
            name='deployment',
            cluster=self.cluster_db,
            status=consts.TASK_STATUSES.running,
            progress=10
        )
        self.db.add(task)
        self.db.flush()
        resp = self.app.delete(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ) + "?force=0",
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status_code, 400)

    def test_forced_deletion_of_running_task_(self):
        task = Task(
            name='deployment',
            cluster=self.cluster_db,
            status=consts.TASK_STATUSES.running,
            progress=10
        )
        self.db.add(task)
        self.db.flush()

        resp = self.app.delete(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ) + "?force=1",
            headers=self.default_headers
        )
        self.assertEqual(resp.status_code, 204)
        resp = self.app.get(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status_code, 404)

    def test_soft_deletion_behavior(self):
        task = Task(
            name=consts.TASK_NAMES.deployment,
            cluster=self.cluster_db,
            status=consts.TASK_STATUSES.running,
            progress=10
        )
        self.db.add(task)
        self.db.flush()
        resp = self.app.delete(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ) + "?force=1",
            headers=self.default_headers
        )
        self.assertEqual(resp.status_code, 204)
        resp = self.app.get(
            reverse(
                'TaskHandler',
                kwargs={'obj_id': task.id}
            ),
            headers=self.default_headers,
            expect_errors=True
        )
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(self.db().query(Task).get(task.id))
