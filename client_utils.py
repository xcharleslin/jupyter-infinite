

def get_or_register_function(droplet_client, func, func_name):
    cloud_func = droplet_client.get_function(func_name)
    if cloud_func is None:
        # print("Function '{}' not found in Hydro. Registering..."
        #     .format(func_name))
        # Hack to get cloudpickle to serialize the whole function.
        func.__module__ = '__main__'
        cloud_func = droplet_client.register(func, func_name)
        if not cloud_func:
            raise Exception("Function registration failed.")

    return cloud_func

