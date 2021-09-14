import importlib
import os

from fastapi import APIRouter

from app.api.endpoints import health_check

api_router = APIRouter()


module_path = ["app", "api", "endpoints"]
modules_tree = os.listdir(os.path.abspath(os.path.join(*module_path)))
for module_name in modules_tree:
    if "__" not in module_name:
        module_base_name = module_name.split(".")[0]
        absolute_module_path = ".".join(module_path) + "." + module_base_name
        module = importlib.import_module(absolute_module_path)
        for attribute_name in dir(module):
            if "_" not in attribute_name and attribute_name == "router":
                attribute = getattr(module, attribute_name)
                if module_base_name == "health_check":
                    api_router.include_router(health_check.router, prefix="")
                else:
                    api_router.include_router(
                        attribute, prefix=f"/{module_base_name}"
                    )
