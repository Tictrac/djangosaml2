# Copyright (C) 2012 Sam Bull (lsb@pocketuniverse.ca)
# Copyright (C) 2011-2012 Yaco Sistemas (http://www.yaco.es)
# Copyright (C) 2010 Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import django

try:
    from django.contrib.auth import get_user_model
except ImportError:
    from django.contrib.auth.models import User
else:
    User = get_user_model()

from django.contrib.auth.models import User as DjangoUserModel

from django.test import TestCase, override_settings

from djangosaml2.backends import Saml2Backend

if django.VERSION < (1,7):
    from testprofiles.models import TestProfile


class Saml2BackendTests(TestCase):
    def test_update_user(self):
        # we need a user
        user = User.objects.create(username='john')

        backend = Saml2Backend()

        attribute_mapping = {
            'uid': ('username', ),
            'mail': ('email', ),
            'cn': ('first_name', ),
            'sn': ('last_name', ),
            }
        attributes = {
            'uid': ('john', ),
            'mail': ('john@example.com', ),
            'cn': ('John', ),
            'sn': ('Doe', ),
            }
        backend.update_user(user, attributes, attribute_mapping)
        self.assertEqual(user.email, 'john@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

        # now we create a user profile and link it to the user
        if django.VERSION < (1, 7):
            profile = TestProfile.objects.create(user=user)
            self.assertNotEquals(profile, None)

        attribute_mapping['saml_age'] = ('age', )
        attributes['saml_age'] = ('22', )
        backend.update_user(user, attributes, attribute_mapping)

        if django.VERSION < (1, 7):
            self.assertEqual(user.get_profile().age, '22')
        else:
            self.assertEqual(user.age, '22')

    def test_update_user_callable_attributes(self):
        user = User.objects.create(username='john')

        backend = Saml2Backend()
        attribute_mapping = {
            'uid': ('username', ),
            'mail': ('email', ),
            'cn': ('process_first_name', ),
            'sn': ('last_name', ),
            }
        attributes = {
            'uid': ('john', ),
            'mail': ('john@example.com', ),
            'cn': ('John', ),
            'sn': ('Doe', ),
            }
        backend.update_user(user, attributes, attribute_mapping)
        self.assertEqual(user.email, 'john@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')

    def test_update_user_empty_attribute(self):
        user = User.objects.create(username='john', last_name='Smith')

        backend = Saml2Backend()
        attribute_mapping = {
            'uid': ('username', ),
            'mail': ('email', ),
            'cn': ('first_name', ),
            'sn': ('last_name', ),
            }
        attributes = {
            'uid': ('john', ),
            'mail': ('john@example.com', ),
            'cn': ('John', ),
            'sn': (),
            }
        backend.update_user(user, attributes, attribute_mapping)
        self.assertEqual(user.email, 'john@example.com')
        self.assertEqual(user.first_name, 'John')
        # empty attribute list: no update
        self.assertEqual(user.last_name, 'Smith')

    def test_django_user_main_attribute(self):
        backend = Saml2Backend()

        old_username_field = User.USERNAME_FIELD
        User.USERNAME_FIELD = 'slug'
        self.assertEqual(backend.get_django_user_main_attribute(), 'slug')
        User.USERNAME_FIELD = old_username_field

        with override_settings(AUTH_USER_MODEL='auth.User'):
            self.assertEqual(
                DjangoUserModel.USERNAME_FIELD,
                backend.get_django_user_main_attribute())

        with override_settings(
                AUTH_USER_MODEL='testprofiles.StandaloneUserModel'):
            self.assertEqual(
                backend.get_django_user_main_attribute(),
                'username')

        with override_settings(SAML_DJANGO_USER_MAIN_ATTRIBUTE='foo'):
            self.assertEqual(backend.get_django_user_main_attribute(), 'foo')

    def test_django_user_main_attribute_lookup(self):
        backend = Saml2Backend()

        self.assertEqual(backend.get_django_user_main_attribute_lookup(), '')

        with override_settings(
                SAML_DJANGO_USER_MAIN_ATTRIBUTE_LOOKUP='__iexact'):
            self.assertEqual(
                backend.get_django_user_main_attribute_lookup(),
                '__iexact')
