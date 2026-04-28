import struct
import time
import win32gui
import win32api
import win32con
import win32process
import commctrl

def get_desktop_listview():
    progman = win32gui.FindWindow("Progman", None)
    shelldll = win32gui.FindWindowEx(progman, 0, "SHELLDLL_DefView", None)
    syslist = win32gui.FindWindowEx(shelldll, 0, "SysListView32", None)
    if not syslist:
        res = []
        def enum_cb(hwnd, lparam):
            shelldll = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
            if shelldll:
                syslist = win32gui.FindWindowEx(shelldll, 0, "SysListView32", None)
                if syslist:
                    lparam.append(syslist)
            return True
        win32gui.EnumWindows(enum_cb, res)
        if res:
            syslist = res[0]
    return syslist

def position_desktop_icon(icon_name, x, y):
    hwnd = get_desktop_listview()
    if not hwnd:
        print("Could not find Desktop SysListView32")
        return False
        
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    
    # OpenProcess
    hproc = win32api.OpenProcess(win32con.PROCESS_VM_OPERATION | win32con.PROCESS_VM_READ | win32con.PROCESS_VM_WRITE, False, pid)
    
    # Allocate memory in explorer.exe for LVITEMW string buffer
    buf_size = 512
    p_buf = win32process.VirtualAllocEx(hproc, 0, buf_size, win32con.MEM_RESERVE | win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
    
    # Allocate memory for LVITEMW struct
    # LVITEMW struct in x64: 88 bytes
    # UINT mask; int iItem; int iSubItem; UINT state; UINT stateMask; LPWSTR pszText; int cchTextMax; int iImage; LPARAM lParam; int iIndent; int iGroupId; UINT cColumns; PUINT puColumns; piColFmt; int iGroup;
    lvitem_size = 88
    p_lvitem = win32process.VirtualAllocEx(hproc, 0, lvitem_size, win32con.MEM_RESERVE | win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
    
    try:
        count = win32gui.SendMessage(hwnd, commctrl.LVM_GETITEMCOUNT, 0, 0)
        found_idx = -1
        
        for i in range(count):
            # Write LVITEMW to target memory
            # mask = LVIF_TEXT (0x0001)
            # pszText = p_buf (offset 24 in x64)
            # cchTextMax = 255 (offset 32 in x64)
            # struct format for 64-bit: I i i I I pad Q i i q i i I Q Q i
            lvitem = struct.pack('IiiiIxxxxQiiqiiIQQi', commctrl.LVIF_TEXT, i, 0, 0, 0, p_buf, 255, 0, 0, 0, 0, 0, 0, 0, 0)
            # wait, it's easier to just use WriteProcessMemory with ctypes
            import ctypes
            from ctypes.wintypes import DWORD, LPVOID, HANDLE, BOOL
            kernel32 = ctypes.windll.kernel32
            
            kernel32.WriteProcessMemory(int(hproc), p_lvitem, lvitem, len(lvitem), None)
            
            # Send LVM_GETITEMW
            res = win32gui.SendMessage(hwnd, commctrl.LVM_GETITEMW, i, p_lvitem)
            
            # Read text buffer
            text_buf = ctypes.create_string_buffer(512)
            kernel32.ReadProcessMemory(int(hproc), p_buf, text_buf, 512, None)
            
            item_text = text_buf.raw.decode('utf-16-le').split('\0')[0]
            if item_text == icon_name:
                found_idx = i
                break
                
        if found_idx != -1:
            print(f"Found '{icon_name}' at index {found_idx}. Moving to {x}, {y}")
            # Position item
            lparam = (y << 16) | (x & 0xFFFF)
            win32gui.SendMessage(hwnd, commctrl.LVM_SETITEMPOSITION, found_idx, lparam)
            return True
            
        print(f"Item '{icon_name}' not found.")
        return False
        
    finally:
        win32process.VirtualFreeEx(hproc, p_buf, 0, win32con.MEM_RELEASE)
        win32process.VirtualFreeEx(hproc, p_lvitem, 0, win32con.MEM_RELEASE)
        win32api.CloseHandle(hproc)

if __name__ == "__main__":
    position_desktop_icon("New Folder", 500, 500)
