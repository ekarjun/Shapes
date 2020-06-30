#!/usr/bin/env python

import inspect
import optparse
import os
import sys
try:
    import requests
except ImportError:
    print 'Please install the "requests" python library, e.g., by'
    print 'sudo apt-get install python-requests # on Ubuntu systems'
    print 'sudo pip install requests # on most Linux systems and Mac'
    sys.exit(1)

try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass

from plugins.porch_api_lib import PorchApiLib, Plugin, PorchApiConfig

class TestCli(PorchApiLib):

    DEFAULT_CMD = "listresources"

    def __init__(self, args):

        plugins = self.load_plugins()
        parser = optparse.OptionParser()

        cmd_map = {}
        for plugin in plugins:
            if plugin.__dict__.get("__abstract__") == True:
                continue
            name = plugin.__name__.lower()
            a = [plugin.LONG_OPTION,]
            short_option = getattr(plugin, 'SHORT_OPTION', None)
            if short_option is not None:
                a.insert(0, short_option)
            kw = (
                dict(action="store", dest=name, metavar="<%s>" % plugin.PARAM_NAME,
                     help=plugin.__doc__.strip()) if plugin.PARAM_NAME else
                dict(action="store_true", dest=name, default=False, help=plugin.__doc__.strip().lower())
            )
            cmd_map[name] = plugin
            parser.add_option(*a, **kw)

        parser.add_option('-i', '--init-file', type='string',
            help="Load host, port, authentication, etc. from this configuration file", default=None)

        (options, args) = parser.parse_args(args=args)
        self.options = options

        self.initialize_config()

        self.cmd_map = cmd_map

    def run_default(self):
        self.cmd_map[self.DEFAULT_CMD]().run()

    def run(self):
        ran_something = False
        for (name, plugin) in self.cmd_map.iteritems():
            cmd_arg = getattr(self.options, name)
            if cmd_arg: # this may be a True or an actual string passed in the command line
                ran_something = True
                args = (cmd_arg,) if plugin.PARAM_NAME else ()
                plugin().run(*args)
        if not ran_something:
            self.run_default()

    def load_plugins(self):
        _dir = os.path.join(os.path.dirname(__file__), "plugins")
        files = [f for f in os.listdir(_dir)
                 if os.path.isfile(os.path.join(_dir, f)) and f.endswith(".py") and f != '__init__.py']
        files.sort()
        plugins = []
        #print 'Potential plugins: %s' % string.join(files, ', ')
        for fname in files:
            # print 'Loading: %s' % fname
            m = __import__('plugins.' + fname[:-3], globals(), locals(), [fname[:-3]], -1)
            for name in dir(m):
                o = m.__dict__[name]
                if inspect.isclass(o) and issubclass(o, Plugin) and o.__name__ != 'Plugin':
                    #print '  Loading plugin class %s' % o.__name__
                    plugins.append(o)
        return plugins

    def initialize_config(self):
        options = self.options

        # default initialization file
        def_init_file = PorchApiConfig.DEFAULT_CFG_FILE

        init_file = getattr(options, "init_file", None)

        if init_file == None and os.path.exists(def_init_file):
            init_file = def_init_file
        elif init_file == None and os.path.islink(def_init_file):
            print("Warning: Default configuration file symlink (%s) does not resolve to a file") % (def_init_file)

        if (init_file != None):
            try:
                cfg = PorchApiConfig.read(init_file)
                PorchApiLib.cfg = cfg
            except Exception as e:
                print("Error reading initialization file (%s): %s") % (init_file, str(e))
                sys.exit(1)

        self.cfg.print_config()

if __name__ == '__main__':

    cli = TestCli(sys.argv)
    cli.run()
    sys.exit(0)


