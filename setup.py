from setuptools import setup, find_packages


def listify(filename):
    return filter(None, open(filename, 'r').read().split('\n'))

setup(
    name="http-request-bouncer",
    version="0.1a",
    url='http://github.com/smn/http-request-bouncer',
    license='BSD',
    description="Bounce http requests back to a client after setting "
                "headers & cookies. Useful for User-Agent based backend "
                "routing with HAProxy",
    long_description=open('README.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekeltfoundation.org',
    packages=find_packages() + [
        # NOTE:2012-01-18: This is commented out for now, pending a fix for
        # https://github.com/pypa/pip/issues/355
        #'twisted.plugins',
    ],
    package_data={'twisted.plugins': ['twisted/plugins/*.py']},
    include_package_data=True,
    install_requires=listify('requirements.pip'),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking',
    ],
)
