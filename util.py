#encoding = utf-8
import os
import struct
from typing import Tuple
import bpy
from bpy.types import Collection, Context, Material, Object, UILayout
import numpy as np
from datetime import datetime

def to_float(bs) -> float:
	return struct.unpack("<f", bs)[0]

def to_float16(bs) -> float:
	return float(np.frombuffer(bs, np.float16)[0])

def to_int(bs) -> int:
	return (int.from_bytes(bs, byteorder='little', signed=True))

def to_uint(bs) -> int:
	return (int.from_bytes(bs, byteorder='little', signed=False))

def to_ushort(bs) -> int:
	return struct.unpack("<H", bs)[0]

def to_string(bs, encoding = 'utf8') -> str:
	return bs.split(b'\x00')[0].decode(encoding, 'replace')

def alignRelative(openFile, relativeStart, alignment):
	alignOffset = (((openFile.tell() - relativeStart) // alignment) + 1) * alignment
	openFile.seek(relativeStart + alignOffset)

def fnv1(data) -> int:
	"""Calculate FNV-1 32-bit hash of a string or bytes."""
	if isinstance(data, str):
		data = data.encode('utf-8')

	# FNV-1 32-bit parameters
	FNV_PRIME = 16777619
	FNV_OFFSET_BASIS = 2166136261

	hash_value = FNV_OFFSET_BASIS
	for byte in data:
		hash_value = (hash_value * FNV_PRIME) & 0xFFFFFFFF
		hash_value = hash_value ^ byte

	return hash_value

def str_to_bytes(var):
	return bytearray(var, 'utf-8')

def uint32_to_bytes(var):
	return var.to_bytes(4, byteorder='little', signed=False)

def int32_to_bytes(var):
	return var.to_bytes(4, byteorder='little', signed=True)

def readFloatX3(f) -> Tuple[float, float, float]:
	return struct.unpack("<fff", f.read(12))

def readFloatX4(f) -> Tuple[float, float, float, float]:
	return struct.unpack("<ffff", f.read(16))

def search_texture(textures_dir: str, texture_filename: str) -> str | None:
    for root, dirs, files in os.walk(textures_dir):
        for file in files:
            if file == texture_filename:
                return os.path.join(root, file)
    return None

def show_blender_system_console():
	import os
	if os.name != 'nt':
		return
	
	import ctypes
	from ctypes import wintypes

	EnumWindows = ctypes.windll.user32.EnumWindows
	EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
	IsWindowVisible = ctypes.windll.user32.IsWindowVisible
	GetWindowText = ctypes.windll.user32.GetWindowTextW
	GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
	SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow

	windows = []
	def foreach_window(hwnd, lParam):
		if IsWindowVisible(hwnd):
			length = GetWindowTextLength(hwnd)
			if length > 0:
				title = ctypes.create_unicode_buffer(length + 1)
				GetWindowText(hwnd, title, length + 1)
				windows.append((hwnd, title.value))
		return True

	EnumWindows(EnumWindowsProc(foreach_window), 0)

	system_console = None
	for hwnd, title in windows:
		if "blender.exe" in title:
			system_console = hwnd
			break

	if system_console is not None and IsWindowVisible(system_console):
		log.d("System Console already open, bringing to foreground...")
		SetForegroundWindow(system_console)
	else:
		log.d("Opening system console...")
		import bpy
		bpy.ops.wm.console_toggle()

class Logger:
    def __init__(self, name: str):
        self.name = name
        self.HEADER = '\033[95m'
        self.OKBLUE = '\033[94m'
        self.OKCYAN = '\033[96m'
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'
        self.UNDERLINE = '\033[4m'

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def d(self, message: str) -> None:
        print(f"{self.OKCYAN}[{self._get_timestamp()}] [DEBUG] {self.name}: {message}{self.ENDC}")

    def i(self, message: str) -> None:
        print(f"{self.OKGREEN}[{self._get_timestamp()}] [INFO] {self.name}: {message}{self.ENDC}")

    def w(self, message: str) -> None:
        print(f"{self.WARNING}[{self._get_timestamp()}] [WARN] {self.name}: {message}{self.ENDC}")

    def e(self, message: str) -> None:
        print(f"{self.FAIL}[{self._get_timestamp()}] [ERROR] {self.name}: {message}{self.ENDC}")

# Global logger instance
log = Logger("Replicant2Blender")

def get_collection_objects(collections: list[Collection], collection_name: str) -> list[Object]:
    for collection in collections:
        if collection.name != collection_name:
            continue
        return [o for o in collection.objects if o.type == 'MESH']
    return []

def get_collection_materials(collections: list[Collection], collection_name: str) -> list[Material]:
	return [mat for o in get_collection_objects(collections, collection_name) for mat in o.data.materials if mat is not None]

def get_export_collections_materials() -> list[Material]:
	root_collections_to_export = [col for col in bpy.context.scene.collection.children if any(obj.type == 'MESH' for obj in col.all_objects) and col.replicant_export]
	collections_to_export = [col for root_col in root_collections_to_export for col in root_col.children if any(obj.type == 'MESH' for obj in col.objects) and col.replicant_export]
	collections_objects = [o for c in collections_to_export for o in c.objects if o.type == 'MESH']
	return list(set([mat for o in collections_objects for mat in o.data.materials if mat is not None]))

def label_multiline(context: Context, parent: UILayout, text: str):
	import textwrap
	uifontscale = 6.6 * context.preferences.view.ui_scale
	chars = int(context.region.width / uifontscale)
	wrapper = textwrap.TextWrapper(width=chars)
	text_lines = wrapper.wrap(text=text)
	for text_line in text_lines:
		parent.label(text=text_line)

def get_export_collections() -> dict[Collection, list[Collection]]:
	out: dict[Collection, list[Collection]] = {}
	root_collections_to_export = [col for col in bpy.context.scene.collection.children if any(obj.type == 'MESH' for obj in col.all_objects) and col.replicant_export]
	for root_col in root_collections_to_export:
		collections_to_export = [col for col in root_col.children if any(obj.type == 'MESH' for obj in col.objects) and col.replicant_export]
		if collections_to_export:
			out[root_col] = collections_to_export
	return out