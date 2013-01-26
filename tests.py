from collections import namedtuple
import unittest
import mock
from txdevserver import servicemaker, service
import sys


class MockModule(object):
    def __init__(self, file):
        self.__file__ = file

MockStat = namedtuple('MockOsStat', 'st_mtime')


class ServiceMakerTests(unittest.TestCase):
    def test_options(self):
        """Test that options support `-s urlpart=directory`, `-s directory` static
        resource registration and `-r urlpart=import.name` twisted.web's Resource
        registration.
        Also test the last argument is the app import.name
        """

        o = servicemaker.Options()
        o.parseOptions(['-s', 'foo=bar', '-s', 'baz', '-r', 'qux=qux.quux'])

        self.assertEqual(o['static'], {'foo': 'bar', 'baz': 'baz'})
        self.assertEqual(o['resources'], {'qux': 'qux.quux'})
        self.assertEqual(o['app'], None)

        o.parseOptions(['foo.bar'])

        self.assertEqual(o['app'], 'foo.bar')


class DevServerResourceTests(unittest.TestCase):
    @mock.patch('os.stat')
    def test_can_detect_code_changes(self, mock_os_stat):
        """Test if DevServer.code_changed can detect a change of a module file's mtime
        This requires mocking out sys.modules and os.stat, i think.
        """

        old_sys_modules = sys.modules.copy()

        class MockDevServer(service.DevServer):
            """A DevServer that won't run the standard initialization process
            Basically we need only the .code_changed method here.
            This method is not a function because it keeps the mtimes on the instance
            """
            def __init__(self, options):
                self._mtimes = {}

        res = MockDevServer({})

        # let's say we have 2 modules imported and the mtime of their files is 1
        sys.modules = {'foo': MockModule('foo.py'), 'bar': MockModule('bar.py')}
        _mtimes = {'foo.py': MockStat(1), 'bar.py': MockStat(1)}

        mock_os_stat.side_effect = _mtimes.get

        # first run - the mtimes aren't cached yet
        needReload = res.code_changed()
        self.assertFalse(needReload)

        # now let's change the mtime of foo.py
        _mtimes['foo.py'] = MockStat(2)

        needReload = res.code_changed()

        self.assertIs(needReload[0], sys.modules['foo'])

        sys.modules = old_sys_modules


if __name__ == '__main__':
    unittest.main()
