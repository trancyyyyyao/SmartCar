from setuptools import setup

package_name = "m1_ultrasonic"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Student",
    maintainer_email="student@example.com",
    description="M1-1 ultrasonic sensor, filter, and alarm nodes.",
    license="Apache-2.0",
    entry_points={"console_scripts": [
                    "node_a_sensor = m1_ultrasonic.node_a_sensor:main",
                    ]
    },
)
