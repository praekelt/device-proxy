from setuptools import setup, find_packages


def listify(filename):
    return filter(None, open(filename, 'r').read().split('\n'))

setup(
    name="device-proxy",
    version="0.1b",
    url='http://github.com/smn/device-proxy',
    license='BSD',
    description="Device Proxy. A reverse HTTP Proxy that can inspect and " \
                "manipulate HTTP Headers before sending upstream.",
    long_description=open('README.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekeltfoundation.org',
    packages=find_packages(),
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
