#!/usr/bin/env python
# -*- coding: future_fstrings -*-
# -*- coding: utf-8 -*-

import os, re
from conans import ConanFile, CMake, tools


class ConsolebridgeConan(ConanFile):
    """ Testing with indigo and 0.4.0 """

    name        = 'console_bridge'
    version     = 'indigo'
    license     = 'Creative Commons Attribution 3.0'
    url         = 'http://wiki.ros.org/console_bridge'
    description = 'console_bridge is a ROS-independent, pure CMake (i.e. non-catkin and non-rosbuild package) that provides logging calls that mirror those found in rosconsole, but for applications that are not necessarily using ROS.'
    settings = 'os', 'compiler', 'build_type', 'arch'
    generators = 'cmake'
    requires = (
        'boost/[>1.46]@ntc/stable',
    )
    options = {
        'shared': [True, False],
        'fPIC':   [True, False],
        'cxx11':  [True, False],
    }
    default_options = ('shared=True', 'fPIC=True', 'cxx11=True')

    def config_options(self):
        if self.settings.compiler == "Visual Studio":
            self.options.remove("fPIC")

    def configure(self):
        self.options['boost'].shared = self.options.shared
        if self.settings.compiler != "Visual Studio":
            self.options['boost'].fPIC = self.options['boost'].shared

    def source(self):
        self.run(f'git clone https://github.com/ros/console_bridge.git {self.name}')

        version = self.version
        if self.version in ['indigo', 'hydro']:
            version = f'{self.version}-devel'
        self.run(f'cd {self.name} && git checkout {version}')

    def build(self):

        # The way the config file is written to is dumb, and breaks on windows.
        tools.replace_in_file(
            file_path=os.path.join(self.name, 'CMakeLists.txt'),
            search=r'configure_file("${cmake_conf_file}.in" "${CMAKE_BINARY_DIR}/${cmake_conf_file}" @ONLY)',
            replace='get_filename_component(cmake_conf_file_basename ${cmake_conf_file} NAME)\nconfigure_file("${cmake_conf_file}.in" "${CMAKE_BINARY_DIR}/${cmake_conf_file_basename}" @ONLY)'
        )
        tools.replace_in_file(
            file_path=os.path.join(self.name, 'CMakeLists.txt'),
            search='install(FILES ${CMAKE_BINARY_DIR}/${cmake_conf_file}',
            replace='install(FILES ${CMAKE_BINARY_DIR}/${cmake_conf_file_basename}',
        )

        cmake = CMake(self)

        if 'fPIC' in self.options and self.options.fPIC:
            cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = 'ON'
        if self.options.cxx11:
            cmake.definitions['CMAKE_CXX_STANDARD'] = 11

        cmake.definitions['BOOST_ROOT:PATH'] = self.deps_cpp_info['boost'].rootpath
        cmake.definitions['BUILD_SHARED_LIBS:BOOL'] = 'TRUE' if self.options.shared else 'FALSE'

        s = '\nCMake Definitions:\n'
        for k,v in cmake.definitions.items():
            s += ' - %s=%s\n'%(k, v)
        self.output.info(s)

        cmake.configure(source_folder=self.name)
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
        if 'Windows' == self.settings.os:
            # console_bridge installs the dll to the lib directory.  We prefer to
            # see it in the bin/ directory, but because there are CMake files and
            # stuff, we're just going to point bin at lib for simplicity.
            self.cpp_info.bindirs = self.cpp_info.libdirs

# vim: ts=4 sw=4 expandtab ffs=unix ft=python foldmethod=marker :
