import importlib
try:
    importlib.import_module('agent.answer_local')
    print('IMPORT_OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    print('IMPORT_FAIL')
