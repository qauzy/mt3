from setuptools import setup, find_packages

setup(
    name='mt3',
    version='0.1',
    packages=find_packages(),
    package_data={
        'mt3': [
            'pretrained/*',
            'config/*',
        ]
    },
    install_requires=[
        # 列出您的项目所需的依赖项
        'transformers == 4.23.0',
        'torch',
        'librosa == 0.9.1',
        't5 == 0.9.3',
        'note-seq == 0.0.3',
        'note-seq == 0.0.3',
        'pretty-midi == 0.2.9',
        'einops == 0.4.1',
        'PyQt6'
        # ddsp==3.3.4


    ],
    entry_points={
        'console_scripts': [
            'mt3 = mt3.__main__:main',
        ],
    },
)