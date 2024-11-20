from setuptools import setup


setup(
    name='cldfbench_allen2016resource',
    py_modules=['cldfbench_allen2016resource'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'cldfbench.dataset': [
            'allen2016resource=cldfbench_allen2016resource:Dataset',
        ]
    },
    install_requires=[
        'cldfbench',
    ],
    extras_require={
        'test': [
            'pytest-cldf',
        ],
    },
)
