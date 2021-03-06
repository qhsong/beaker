
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

from bkr.server.model import session, SystemStatus
from bkr.inttest import data_setup
from bkr.inttest.client import run_client, ClientError, ClientTestCase

class SystemReleaseTest(ClientTestCase):

    # https://bugzilla.redhat.com/show_bug.cgi?id=1252503
    def test_releasing_unreserved_system_shows_an_error(self):
        with session.begin():
            system = data_setup.create_system()
        try:
            res = run_client(['bkr', 'system-release', system.fqdn])
            self.fail('Must fail')
        except ClientError as e:
            self.assertIn('System %s is not currently reserved' % system.fqdn,
                          e.stderr_output)

    def test_can_release_system(self):
        with session.begin():
            system = data_setup.create_system(status=SystemStatus.manual)
            user = data_setup.create_user()
            system.reserve_manually(u'TESTING', user=user)
        self.assertEqual(system.user, user)
        run_client(['bkr', 'system-release', system.fqdn])
        with session.begin():
            session.refresh(system)
            self.assertEqual(system.user, None)
