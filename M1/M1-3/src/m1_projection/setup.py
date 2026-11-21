import os
from glob import glob

from setuptools import setup

package_name = "m1_projection"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Student",
    maintainer_email="student@example.com",
    description="M1-3 laser-to-camera projection workspace.",
    license="Apache-2.0",
    entry_points={
        "console_scripts": [
            "static_tf_node = m1_projection.static_tf_node:main",
            "projection_node = m1_projection.projection_node:main",
        ],
        
    },
)
