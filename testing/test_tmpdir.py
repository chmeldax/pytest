import py
import pytest

from _pytest.tmpdir import tmpdir

def test_funcarg(testdir):
    testdir.makepyfile("""
            def pytest_generate_tests(metafunc):
                metafunc.addcall(id='a')
                metafunc.addcall(id='b')
            def test_func(tmpdir): pass
    """)
    from _pytest.tmpdir import TempdirFactory
    reprec = testdir.inline_run()
    calls = reprec.getcalls("pytest_runtest_setup")
    item = calls[0].item
    config = item.config
    tmpdirhandler = TempdirFactory(config)
    item._initrequest()
    p = tmpdir(item._request, tmpdirhandler)
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn.endswith("test_func_a_")
    item.name = "qwe/\\abc"
    p = tmpdir(item._request, tmpdirhandler)
    assert p.check()
    bn = p.basename.strip("0123456789")
    assert bn == "qwe__abc"

def test_ensuretemp(recwarn):
    #pytest.deprecated_call(pytest.ensuretemp, 'hello')
    d1 = pytest.ensuretemp('hello')
    d2 = pytest.ensuretemp('hello')
    assert d1 == d2
    assert d1.check(dir=1)

class TestTempdirHandler:
    def test_mktemp(self, testdir):
        from _pytest.tmpdir import TempdirFactory
        config = testdir.parseconfig()
        config.option.basetemp = testdir.mkdir("hello")
        t = TempdirFactory(config)
        tmp = t.mktemp("world")
        assert tmp.relto(t.getbasetemp()) == "world0"
        tmp = t.mktemp("this")
        assert tmp.relto(t.getbasetemp()).startswith("this")
        tmp2 = t.mktemp("this")
        assert tmp2.relto(t.getbasetemp()).startswith("this")
        assert tmp2 != tmp

class TestConfigTmpdir:
    def test_getbasetemp_custom_removes_old(self, testdir):
        mytemp = testdir.tmpdir.join("xyz")
        p = testdir.makepyfile("""
            def test_1(tmpdir):
                pass
        """)
        testdir.runpytest(p, '--basetemp=%s' % mytemp)
        mytemp.check()
        mytemp.ensure("hello")

        testdir.runpytest(p, '--basetemp=%s' % mytemp)
        mytemp.check()
        assert not mytemp.join("hello").check()


def test_basetemp(testdir):
    mytemp = testdir.tmpdir.mkdir("mytemp")
    p = testdir.makepyfile("""
        import pytest
        def test_1():
            pytest.ensuretemp("hello")
    """)
    result = testdir.runpytest(p, '--basetemp=%s' % mytemp)
    assert result.ret == 0
    assert mytemp.join('hello').check()

@pytest.mark.skipif(not hasattr(py.path.local, 'mksymlinkto'),
                    reason="symlink not available on this platform")
def test_tmpdir_always_is_realpath(testdir):
    # the reason why tmpdir should be a realpath is that
    # when you cd to it and do "os.getcwd()" you will anyway
    # get the realpath.  Using the symlinked path can thus
    # easily result in path-inequality
    # XXX if that proves to be a problem, consider using
    # os.environ["PWD"]
    realtemp = testdir.tmpdir.mkdir("myrealtemp")
    linktemp = testdir.tmpdir.join("symlinktemp")
    linktemp.mksymlinkto(realtemp)
    p = testdir.makepyfile("""
        def test_1(tmpdir):
            import os
            assert os.path.realpath(str(tmpdir)) == str(tmpdir)
    """)
    result = testdir.runpytest("-s", p, '--basetemp=%s/bt' % linktemp)
    assert not result.ret

def test_tmpdir_too_long_on_parametrization(testdir):
    testdir.makepyfile("""
        import pytest
        @pytest.mark.parametrize("arg", ["1"*1000])
        def test_some(arg, tmpdir):
            tmpdir.ensure("hello")
    """)
    reprec = testdir.inline_run()
    reprec.assertoutcome(passed=1)
