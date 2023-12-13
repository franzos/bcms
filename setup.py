import pathlib
from setuptools import setup, find_packages

HERE = pathlib.Path(__file__).parent

VERSION = "0.0.3"
PACKAGE_NAME = "bcms"
AUTHOR = "Franz Geffke"
AUTHOR_EMAIL = "franz@pantherx.org"
URL = "https://git.pantherx.org/development/applications/bcms"

DESCRIPTION = "Retrieves and saves device assigned user."
LONG_DESCRIPTION = (HERE / "README.md").read_text()
LONG_DESC_TYPE = "text/markdown"

INSTALL_REQUIRES = [
    "bleak",
    "requests",
    "pycapnp",
    "px-device-identity",
    "vhh-bluetooth-terminal-assigned-user",
]

setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type=LONG_DESC_TYPE,
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    install_requires=INSTALL_REQUIRES,
    include_package_data=True,
    package_data={
        "": [
            "rpc/bcms.capnp",
        ]
    },
    entry_points={
        "console_scripts": ["bcms-daemon=bcms.main:main", "bcms=bcms.rpc_client:main"],
    },
    packages=find_packages(),
    zip_safe=False,
)
