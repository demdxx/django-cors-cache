from setuptools import setup

setup(
    name='django-cors-cache',
    version='0.0.0',
    author='Dmitriy Ponomarev',
    author_email='demdxx@gmail.com',

    description='slick ORM cache and invalidation for Django',
    long_description=open('README.md').read(),
    url='http://github.com/demdxx/django-cors-cache',
    license='BSD',

    packages=['corscache'],
    install_requires=[
        'django>=1.2',
        #'simplejson>=2.1.5',
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',

        'Framework :: Django',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

