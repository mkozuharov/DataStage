from __future__ import with_statement
from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
from distutils.command.sdist import sdist as _sdist
from distutils.command.clean import clean as _clean
import contextlib
import functools
import os
import shutil
import subprocess
import urllib
import zipfile

#################################
# BEGIN borrowed from Django    #
# licensed under the BSD        #
# http://www.djangoproject.com/ #
#################################

def fullsplit(path, result=None):
    """
Split a pathname into components (the opposite of os.path.join) in a
platform-neutral way.
"""
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('datastage'):
    # Ignore dirnames that start with '.'
    dirnames[:] = [dirname for dirname in dirnames if not dirname.startswith('.')]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, map(functools.partial(os.path.join, dirpath), filenames)])

#################################
# END borrowed from Django      #
#################################

# Idea borrowed from http://cburgmer.posterous.com/pip-requirementstxt-and-setuppy
install_requires, dependency_links = [], []
for line in open('requirements.txt'):
    line = line.strip()
    if line.startswith('-e'):
        dependency_links.append(line[2:].strip())
    elif line:
        install_requires.append(line)

class sdist(_sdist):
    relative_path = staticmethod(functools.partial(os.path.join, os.path.dirname(__file__)))

    JQUERY_UI_LOCATION = 'http://jqueryui.com/download/jquery-ui-1.8.16.custom.zip'
    JQUERY_UI_FILENAME = 'jquery-ui.zip'

    def run(self):
        try:
            self.compile_jquery()
            self.retrieve_flot()
            self.retrieve_jquery_ui()
            self.copy_jslibs()
            self.generate_manifest_in()

            # Remove broken symlinks. See http://bugs.python.org/issue12885 for
            # an explanation.
            for root, dirs, files in os.walk(os.curdir):
                for name in files:
                    name = os.path.join(root, name)
                    if os.path.islink(name) and not os.path.exists(os.path.join(name, os.readlink(name))):
                        os.unlink(name)

            _sdist.run(self)
        except:
            import traceback
            traceback.print_exc()
            raise

    def compile_jquery(self):
        subprocess.call(['make'], cwd=self.relative_path('jquery'))

    def retrieve_flot(self):
        if not os.path.exists(self.relative_path('flot')):
            subprocess.call(['svn', 'checkout', 'http://flot.googlecode.com/svn/trunk/', 'flot'])
        subprocess.call(['svn', 'update', '-r', '342'])

    def retrieve_jquery_ui(self):
        if not os.path.exists(self.relative_path(self.JQUERY_UI_FILENAME)):
            urllib.urlretrieve(self.JQUERY_UI_LOCATION, self.relative_path(self.JQUERY_UI_FILENAME))
        if os.path.exists(self.relative_path('jquery-ui')):
            shutil.rmtree(self.relative_path('jquery-ui'))
        zip = zipfile.ZipFile(self.relative_path(self.JQUERY_UI_FILENAME))
        zip.extractall(self.relative_path('jquery-ui'))

        for path in ('js', 'development-bundle/external', 'development-bundle/ui/minified'):
            shutil.rmtree(self.relative_path('jquery-ui', *path.split('/')))

        for path in ('ui', 'themes'):
            os.rename(self.relative_path('jquery-ui', 'development-bundle', path),
                      self.relative_path('jquery-ui', path))

        shutil.rmtree(self.relative_path('jquery-ui', 'development-bundle'))
        os.unlink(self.relative_path('jquery-ui', 'index.html'))

        for path in os.listdir(self.relative_path('jquery-ui', 'ui')):
            if path.startswith('jquery-ui-') and path.endswith('.custom.js'):
                os.symlink(os.path.join('ui', path),
                           self.relative_path('jquery-ui', 'jquery-ui.js'))
        for path in os.listdir(self.relative_path('jquery-ui', 'css', 'smoothness')):
            if path.startswith('jquery-ui-') and path.endswith('.custom.css'):
                os.symlink(os.path.join(path),
                           self.relative_path('jquery-ui', 'css', 'smoothness', 'jquery-ui.css'))

        minify = [self.relative_path('jquery-ui', 'jquery-ui.js'),
                  self.relative_path('jquery-ui', 'css', 'smoothness', 'jquery-ui.css')]

        for path in minify:
            with open(path+'.min', 'w') as stdout:
                subprocess.call(['java', '-jar', self.relative_path('jquery', 'build', 'yuicompressor-2.4.2.jar'),
                                         path],
                                stdout=stdout)



    def copy_jslibs(self):
        # Copy the jQuery dist directory verbatim.
        if os.path.exists(self.relative_path('datastage', 'jquery')):
            shutil.rmtree(self.relative_path('datastage', 'jquery'))
        shutil.copytree(self.relative_path('jquery', 'dist'), self.relative_path('datastage', 'jquery'))

        # MochiKit needs more work. First, we create the directory if it
        # doesn't already exist...
        if not os.path.exists(self.relative_path('datastage', 'mochikit')):
            os.makedirs(self.relative_path('datastage', 'mochikit'))

        # Then we copy the main JS file:
        shutil.copy(self.relative_path('mochikit', 'packed', 'MochiKit', 'MochiKit.js'),
                    self.relative_path('datastage', 'mochikit', 'MochiKit.js'))

        # Finally we use jQuery's minifier to create a .js.min version:
        with open(self.relative_path('datastage', 'mochikit', 'MochiKit.js.min'), 'w') as stdout:
            subprocess.call(['java', '-jar', self.relative_path('jquery', 'build', 'yuicompressor-2.4.2.jar'),
                                     self.relative_path('datastage', 'mochikit', 'MochiKit.js')],
                            stdout=stdout)

        # Copy jQuery-treeview
        if os.path.exists(self.relative_path('datastage', 'jquery-treeview')):
            shutil.rmtree(self.relative_path('datastage', 'jquery-treeview'))
        os.makedirs(self.relative_path('datastage', 'jquery-treeview'))
        for path in os.listdir(self.relative_path('jquery-treeview')):
            if path in ('changelog.txt', 'demo', '.git', '.gitignore', 'lib', 'README.md', 'todo'):
                continue
            source = self.relative_path('jquery-treeview', path)
            target = self.relative_path('datastage', 'jquery-treeview', path)
            if os.path.isdir(source):
                shutil.copytree(source, target)
            else:
                shutil.copy(source, target)

        # Copy flot
        if not os.path.exists(self.relative_path('datastage', 'flot')):
            os.makedirs(self.relative_path('datastage', 'flot'))
        for path in os.listdir(self.relative_path('flot')):
            if os.path.splitext(path) == '.js':
                shutil.copy(self.relative_path('flot', path),
                            self.relative_path('datastage', 'flot', path))

        if os.path.exists(self.relative_path('datastage', 'jquery-ui')):
            shutil.rmtree(self.relative_path('datastage', 'jquery-ui'))
        shutil.copytree(self.relative_path('jquery-ui'),
                        self.relative_path('datastage', 'jquery-ui'))




    def generate_manifest_in(self):
        # Old versions of distutils don't handle data files properly. We'll generate
        # a MANIFEST.in file from data_files. See
        # http://stackoverflow.com/questions/2994396/python-distutils-does-not-include-data-files
        # for more information.
        with open('MANIFEST.in', 'w') as manifest:
            manifest.write('# This file generated by setup.py; any changes made to it will be lost. Edit\n')
            manifest.write('# MANIFEST.in.in instead.\n')
            with open('MANIFEST.in.in', 'r') as manifest_in:
                manifest.writelines(manifest_in)
        
            manifest.write('# Lines below generated by setup.py.\n')
            for dirpath, filenames in data_files:
                manifest.write('recursive-include %s *\n' % dirpath)

class clean(_clean):
    paths_to_remove = [
        ('jquery', 'dist'),
        ('jquery', 'speed'),
        ('jquery-ui',),
        ('jquery-ui.zip',),
        ('datastage', 'jquery'),
        ('datastage', 'jquery-ui'),
        ('datastage', 'mochikit'),
        ('datastage', 'jquery-treeview'),
        ('flot',),
        ('datastage', 'flot'),
        ('MANIFEST',),
        ('MANIFEST.in',),
    ]
        
    def run(self):
        self.remove_paths()
        _clean.run(self)

    def remove_paths(self):
        for path in self.paths_to_remove:
            path = os.path.join(os.path.dirname(__file__), *path)
            if not os.path.exists(path):
                continue
            elif os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.unlink(path)
            else:
                raise AssertionError("Unexpected file type: %r" % path)


setup(
    name='datastage',
    description='A framework for secure personalized file management environments for use at the research group level.',
    author='The DataFlow Project',
    author_email='jisc.dataflow@gmail.com',
    version='0.1',
    packages=packages,
    long_description=open('README.rst').read(),
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: Science/Research',
                 'Natural Language :: English',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python',
                 'Topic :: Internet :: WWW/HTTP :: Dynamic Content'],
    data_files=data_files,
    install_requires=install_requires,
    dependency_links=dependency_links,
    cmdclass={'sdist': sdist,
              'clean': clean},
)
