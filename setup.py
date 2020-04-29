import setuptools

setuptools.setup(
    name="jupyter-infinite",
    py_modules=['hydro_kernel', 'proxying_client', 'serverless_kernel_client'],
    version="0.0.1",
    author="Xiayue Charles Lin",
    author_email="charles.lin@berkeley.edu",
    description="Hydro kernel for Python.",
    long_description="Hydro kernel for Python.",
    long_description_content_type="text/markdown",
    url="https://github.com/xcharleslin/jupyter-infinite",
    packages=setuptools.find_packages(),
    classifiers=[],
    python_requires='>=3.6',
)
