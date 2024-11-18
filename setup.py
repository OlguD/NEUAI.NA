from setuptools import setup, find_packages

setup(
    name="NEUAI.NA",
    version="1.0.0",
    description="NEU Face and Document Recognition System",
    author="Olgu DEĞİRMENCİ, Atakan UZUN",
    author_email="olgudegirmenci34@gmail.com, atakanuzun09@gmail.com",
    packages=find_packages(),
    install_requires=[
        "opencv-python",
        "numpy",
        "easyocr",
        "torch",
        "Flask",
        "python-dotenv",
        "deepface",
        "tf-keras",
    ],
    # extras_require={
    #     'dev': [
    #         'pytest>=6.0.0',
    #         'black>=21.0.0',
    #         'flake8>=3.9.0',
    #         'isort>=5.9.0',
    #     ]
    # },
    entry_points={
        'console_scripts': [
            'NEUAI.NA=app:main',
        ],
    },
    python_requires='>=3.11',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Flask',
        'Topic :: Scientific/Engineering :: Image Recognition',
    ],
    package_data={
        'neuai': [
            'static/css/*.css',
            'static/js/*.js',
            'templates/*.html',
            'core/*.xml',
            'core/*.jpg',
        ],
    },
    include_package_data=True,
    project_urls={
        'Source': 'https://github.com/OlguD/neuai-recognition',
    },
)