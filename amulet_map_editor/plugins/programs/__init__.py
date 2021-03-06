import wx
import os
from typing import List, Dict, Callable, Union, Tuple, Any
import importlib
import pkgutil

from amulet.api.errors import LoaderNoneMatched
from amulet import world_interface

from amulet_map_editor.amulet_wx.simple import SimpleNotebook, SimplePanel

MenuData = Dict[
    str, Dict[
        str, Dict[
            str, Union[
                Callable,
                Tuple[Callable],
                Tuple[Callable, str],
                Tuple[Callable, str, Any],
            ]
        ]
    ]
]

# this is where most of the magic will happen

_extensions: List['BaseWorldProgram'] = []


def load_extensions():
    if not _extensions:
        for _, name, _ in pkgutil.iter_modules([os.path.join(os.path.dirname(__file__))]):
            # load module and confirm that all required attributes are defined
            module = importlib.import_module(f'amulet_map_editor.plugins.programs.{name}')

            if hasattr(module, 'export'):
                export = getattr(module, 'export')
                if 'ui' in export and issubclass(export['ui'], BaseWorldProgram):
                    _extensions.append([export.get('name', 'missingno'), export['ui']])


class BaseWorldUI:
    def disable(self):
        pass

    def enable(self):
        pass

    def close(self):
        pass

    def menu(self, menu: MenuData) -> MenuData:
        return menu


class WorldManagerUI(SimpleNotebook, BaseWorldUI):
    def __init__(self, parent, path):
        SimpleNotebook.__init__(
            self,
            parent,
            wx.NB_LEFT
        )
        self._finished = False
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._page_change)
        try:
            self.world = world_interface.load_world(path)
        except LoaderNoneMatched as e:
            self.Destroy()
            raise e
        self.world_name = self.world.world_wrapper.world_name
        self._extensions: List[BaseWorldProgram] = []
        self._last_extension: int = -1
        self._load_extensions()
        self._finished = True

    def menu(self, menu: MenuData) -> MenuData:
        menu.setdefault('&File', {}).setdefault('system', {}).setdefault('Save\tCtrl+s', lambda evt: self.world.save())
        # menu.setdefault('&File', {}).setdefault('system', {}).setdefault('Save As', lambda evt: self.GetGrandParent().close_world(self.world.world_path))
        menu.setdefault('&File', {}).setdefault('exit', {}).setdefault('Close World\tCtrl+w', lambda evt: self.GetGrandParent().close_world(self.world.world_path))
        return self._extensions[self.GetSelection()].menu(menu)

    def _load_extensions(self):
        """Load and create instances of each of the extensions"""
        load_extensions()
        for extension_name, extension in _extensions:
            ext = extension(self, self.world)
            self._extensions.append(ext)
            self.AddPage(ext, extension_name, True)

    def is_closeable(self) -> bool:
        """Check if all extensions are safe to be closed"""
        return all(e.is_closeable() for e in self._extensions)

    def close(self):
        """Close the world and destroy the UI
        Check is_closeable before running this"""
        for ext in self._extensions:
            ext.close()
        self.world.close()

    def _page_change(self, evt):
        """Method to fire when the page is changed"""
        if self.GetSelection() != self._last_extension:
            if self._finished:
                self._extensions[self._last_extension].disable()
                self._extensions[self.GetSelection()].enable()
                self.GetGrandParent().create_menu()
            self._last_extension = self.GetSelection()
        evt.Skip()

    def disable(self):
        self._extensions[self.GetSelection()].disable()

    def enable(self):
        self._extensions[self.GetSelection()].enable()
        self.GetGrandParent().create_menu()


class BaseWorldProgram(SimplePanel):

    def enable(self):
        """Run when the panel is shown/enabled"""
        pass

    def disable(self):
        """Run when the panel is hidden/disabled"""
        pass

    def is_closeable(self):
        return True

    def close(self):
        """Run when the world is closed"""
        pass

    def menu(self, menu: MenuData) -> MenuData:
        return menu
