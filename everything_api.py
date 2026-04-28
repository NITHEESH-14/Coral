import ctypes
import os
import platform

class EverythingAPI:
    def __init__(self):
        is_64bits = platform.machine().endswith('64')
        dll_name = "Everything64.dll" if is_64bits else "Everything32.dll"
        
        dll_path = os.path.join(os.path.dirname(__file__), dll_name)
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"Missing {dll_name} in Coral directory.")
            
        self.everything_dll = ctypes.WinDLL(dll_path)
        
        self.everything_dll.Everything_SetSearchW.argtypes = [ctypes.c_wchar_p]
        self.everything_dll.Everything_QueryW.argtypes = [ctypes.c_bool]
        self.everything_dll.Everything_GetNumResults.restype = ctypes.c_uint32
        self.everything_dll.Everything_GetResultFullPathNameW.argtypes = [ctypes.c_uint32, ctypes.c_wchar_p, ctypes.c_uint32]

    def search(self, query: str, limit=5):
        self.everything_dll.Everything_SetSearchW(query)
        self.everything_dll.Everything_QueryW(True)
        
        num_results = self.everything_dll.Everything_GetNumResults()
        results = []
        
        buf = ctypes.create_unicode_buffer(500)
        for i in range(min(num_results, limit)):
            self.everything_dll.Everything_GetResultFullPathNameW(i, buf, 500)
            results.append(buf.value)
            
        return results
