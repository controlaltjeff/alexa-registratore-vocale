import ask_sdk_webservice_support
print(dir(ask_sdk_webservice_support))
try:
    from ask_sdk_webservice_support.webservice_handler import WebserviceHandler
    print("Import successful from submodule")
except ImportError:
    print("Import failed from submodule")

try:
    from ask_sdk_webservice_support import WebserviceHandler
    print("Import successful from top level")
except ImportError:
    print("Import failed from top level")
