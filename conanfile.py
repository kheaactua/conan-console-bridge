import os, re
from conans import ConanFile, CMake


class ConsolebridgeConan(ConanFile):
    name = 'console_bridge'
    version = 'indigo'
    # version = '0.4.0'
    license = 'Creative Commons Attribution 3.0'
    url = 'http://wiki.ros.org/console_bridge'
    description = 'console_bridge is a ROS-independent, pure CMake (i.e. non-catkin and non-rosbuild package) that provides logging calls that mirror those found in rosconsole, but for applications that are not necessarily using ROS.'
    settings = 'os', 'compiler', 'build_type', 'arch'
    generators = 'cmake'
    requires = (
        'Boost/[>1.46]@conan/stable',
    )
    options = {
        'shared': [True, False],
    }
    default_options = ("shared=True")

    def configure(self):
        self.options["Boost"].shared = self.options.shared

    def source(self):
        self.run(f'git clone https://github.com/ros/console_bridge.git {self.name}')

        version = self.version
        if self.version in ['indigo', 'hydro']:
            version = f'{self.version}-devel'
        self.run(f'cd {self.name} && git checkout {version}')

    def build(self):

        args = []
        args.append('-DBOOST_ROOT:PATH=%s'%self.deps_cpp_info['Boost'].rootpath)
        args.append('-DBUILD_SHARED_LIBS=%s'%('TRUE' if self.options.shared else 'FALSE'))

        cmake = CMake(self)
        cmake.configure(source_folder=self.name, args=args)
        cmake.build()
        cmake.install()

        self.fixFindPackage(os.path.join(self.package_folder, 'share', 'console_bridge', 'cmake', 'console_bridge-config.cmake'))

    def fixFindPackage(self, path):
        """
        Insert some variables into the console_bridge find script generated in
        the build so that we can use it in our CMake scripts
        """

        if not os.path.exists(path):
            self.output.warn('Could not fix non-existant file: %s'%path)
            return

        with open(path) as f: data = f.read()

        m = re.search(r'console_bridge_INCLUDE_DIRS ("|)(?P<path>(?P<base>.*?)(?P<type>(build|package)).(?P<hash>.\w+)).include', data)
        if not m:
            self.output.warn('Could not find console_bridge source directory in CMake file')
            return
        data = data.replace(m.group('path'), '${CONAN_CONSOLE_BRIDGE_ROOT}')

        data = data.replace('find_library(onelib ${lib})', 'find_library(onelib ${lib} PATH ${CONAN_CONSOLE_BRIDGE_ROOT}/lib)')

        with open(path, 'w') as f: f.write(data)

    def package(self):
        pass

    def package_info(self):
        pass

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
