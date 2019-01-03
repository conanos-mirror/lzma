from conans import ConanFile,tools,MSBuild
from conanos.build import config_scheme
import os, shutil

class LzmaConan(ConanFile):
    name = "lzma"
    version = "5.2.4"
    description = "liblzma is a lzma compression library with API similar to that of zlib"
    url = "https://github.com/conanos/lzma"
    homepage = " https://www.7-zip.org/sdk.html"
    license = "LGPL-v2.1+, GPLv2+"
    generators = "visual_studio", "gcc"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = { 'shared': True, 'fPIC': True }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def source(self):
        url_ = 'https://github.com/ShiftMediaProject/liblzma/archive/v{version}.tar.gz'
        tools.get(url_.format(version=self.version))
        extracted_dir = "lib" + self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"SMP")):
                msbuild = MSBuild(self)
                build_type = str(self.settings.build_type) + ("DLL" if self.options.shared else "")
                msbuild.build("liblzma.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'},build_type=build_type)

    def package(self):
        if self.settings.os == 'Windows':
            platforms={'x86': 'Win32', 'x86_64': 'x64'}
            rplatform = platforms.get(str(self.settings.arch))
            self.copy("*", dst=os.path.join(self.package_folder,"include"), src=os.path.join(self.build_folder,"..", "msvc","include"))
            if self.options.shared:
                for i in ["lib","bin"]:
                    self.copy("*", dst=os.path.join(self.package_folder,i), src=os.path.join(self.build_folder,"..","msvc",i,rplatform))
            self.copy("*", dst=os.path.join(self.package_folder,"licenses"), src=os.path.join(self.build_folder,"..", "msvc","licenses"))
            
            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copy(os.path.join(self.build_folder,self._source_subfolder,"src","liblzma","liblzma.pc.in"),
                        os.path.join(self.package_folder,"lib","pkgconfig","liblzma.pc"))
            lib = "-llzmad" if self.options.shared else "-llzma"
            replacements = {
                "@prefix@"                   : self.package_folder,
                "@exec_prefix@"              : "${prefix}/lib",
                "@libdir@"                   : "${prefix}/lib",
                "@includedir@"               : "${prefix}/include",
                "@PACKAGE_URL@"              : self.url,
                "@PACKAGE_VERSION@"          : self.version,
                "@PTHREAD_CFLAGS@"           : "",
                "@LIBS@"                     : "",
                "-llzma"                     : lib
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig","liblzma.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

