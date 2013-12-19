from setuptools import setup


def listify(filename):
    return filter(None, open(filename, 'r').read().strip('\n').split('\n'))

setup(
    name="device-proxy",
    version="0.2",
    url='http://github.com/praekelt/device-proxy',
    license='BSD',
    description="Device Proxy. A reverse HTTP Proxy that can inspect and "
                "manipulate HTTP Headers before sending upstream.",
    long_description=open('README.rst', 'r').read(),
    author='Praekelt Foundation',
    author_email='dev@praekeltfoundation.org',
    packages=[
        "devproxy",
        "twisted.plugins",
    ],
    package_data={
        'twisted.plugins': ['twisted/plugins/devproxy_plugin.py'],
        'devproxy.etc': ['devproxy/etc/*']
    },
    data_files=[
        ('/etc/supervisor/conf.d/', ['devproxy/etc/device-proxy.conf']),
        ('/etc/device-proxy/', ['devproxy/etc/config.yaml']),
        ('/etc/device-proxy/', ['devproxy/etc/haproxy.cfg'])
    ],
    include_package_data=True,
    install_requires=listify('requirements.txt'),
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
