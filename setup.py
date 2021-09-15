from setuptools import setup

with open("README.md", "r") as rdm:
    long_desc = rdm.read().replace("(./", "(https://github.com/RivenSkaye/rvsfunc/blob/master/")

with open("requirements.txt", "r") as rq:
    req = rq.read()

with open(".version", "r") as v:
    ver = v.read().strip()

setup(
    name="rvsfunc",
    version=ver,
    author="Riven Skaye",
    author_email="riven@tae.moe",
    description="VapourSynth functions written or modified by Riven Skaye",
    long_description=long_desc,
    long_description_content_type="text/markdown",
    url="https://github.com/RivenSkaye/rvsfunc",
    packages=["rvsfunc"],
    install_requires=req,
    python_requires=">=3.8",
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Topic :: Multimedia :: Graphics"
    ],
    project_urls={
        "tracker": "https://github.com/RivenSkaye/rvsfunc/issues"
    }
)
