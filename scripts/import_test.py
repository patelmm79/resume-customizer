import importlib
try:
    importlib.invalidate_caches()
    import utils.llm_client as mod
    print('IMPORT_OK')
except Exception as e:
    print('IMPORT_ERROR', type(e).__name__, str(e))
