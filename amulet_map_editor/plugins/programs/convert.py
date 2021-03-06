from amulet_map_editor.amulet_wx.simple import SimplePanel
from amulet_map_editor.amulet_wx.world_select import WorldSelectWindow, WorldUI
from amulet_map_editor.plugins.programs import BaseWorldProgram
from amulet import world_interface
from amulet.api.world import World
from amulet.world_interface.formats import Format
import wx
from amulet_map_editor import lang, log
from concurrent.futures import ThreadPoolExecutor

thread_pool_executor = ThreadPoolExecutor(max_workers=1)
work_count = 0


class ConvertExtension(BaseWorldProgram):
    def __init__(self, container, world: World):
        super(ConvertExtension, self).__init__(
            container
        )
        self.world = world

        self._close_world_button = wx.Button(self, wx.ID_ANY, label='Close World')
        self._close_world_button.Bind(wx.EVT_BUTTON, self._close_world)
        self.add_object(self._close_world_button, 0, wx.ALL | wx.CENTER)

        self._input = SimplePanel(self, wx.HORIZONTAL)
        self.add_object(self._input, 0, wx.ALL|wx.CENTER)
        self._input.add_object(
            wx.StaticText(
                self._input,
                wx.ID_ANY,
                'Input World: ',
                wx.DefaultPosition,
                wx.DefaultSize,
                0,
            ), 0, wx.ALL|wx.CENTER
        )
        self._input.add_object(
            WorldUI(self._input, self.world.world_path), 0, wx.ALL|wx.CENTER
        )

        self._output = SimplePanel(self, wx.HORIZONTAL)
        self.add_object(self._output, 0, wx.ALL | wx.CENTER)
        self._output.add_object(
            wx.StaticText(
                self._output,
                wx.ID_ANY,
                'Output World: ',
                wx.DefaultPosition,
                wx.DefaultSize,
                0,
            ), 0, wx.ALL | wx.CENTER
        )

        self._select_output_button = wx.Button(self, wx.ID_ANY, label='Select Output World')
        self._select_output_button.Bind(wx.EVT_BUTTON, self._show_world_select)
        self.add_object(self._select_output_button, 0, wx.ALL | wx.CENTER)

        self._convert_bar = SimplePanel(self, wx.HORIZONTAL)
        self.add_object(self._convert_bar, 0, wx.ALL | wx.CENTER)

        self.loading_bar = wx.Gauge(
            self._convert_bar,
            wx.ID_ANY,
            100,
            wx.DefaultPosition,
            wx.DefaultSize,
            wx.GA_HORIZONTAL,
        )
        self._convert_bar.add_object(self.loading_bar, options=wx.ALL | wx.EXPAND)
        self.loading_bar.SetValue(0)

        self.convert_button = wx.Button(self._convert_bar, wx.ID_ANY, label=lang.get('convert'))
        self._convert_bar.add_object(self.convert_button)
        self.convert_button.Bind(wx.EVT_BUTTON, self._convert_event)

        self.out_world_path = None

    def _show_world_select(self, evt):
        self.Disable()
        WorldSelectWindow(self._output_world_callback, self.Enable)

    def _output_world_callback(self, path):
        if path == self.world.world_path:
            wx.MessageBox(
                'The input and output worlds must be different'
            )
            return
        try:
            out_world = world_interface.load_format(path)
            self.out_world_path = path

        except Exception:
            return

        for child in list(self._output.GetChildren())[1:]:
            child.Destroy()
        self._output.add_object(
            WorldUI(self._output, self.out_world_path), 0
        )
        self._output.Layout()
        self._output.Fit()
        self.Layout()
        # self.Fit()

    def _update_loading_bar(self, chunk_index, chunk_total):
        wx.CallAfter(self.loading_bar.SetValue, int(100*chunk_index/chunk_total))

    def _convert_event(self, evt):
        if self.out_world_path is None:
            wx.MessageBox(
                'Select a world before converting'
            )
            return
        self.convert_button.Disable()
        global work_count
        work_count += 1
        thread_pool_executor.submit(self._convert_method)
        # self.world.save(self.out_world, self._update_loading_bar)

    def _convert_method(self):
        global work_count
        try:
            out_world = world_interface.load_format(self.out_world_path)
            log.info(f'Converting world {self.world.world_path} to {out_world.world_path}')
            out_world: Format
            out_world.open()
            self.world.save(out_world, self._update_loading_bar)
            out_world.close()
            message = 'World conversion completed'
            log.info(f'Finished converting world {self.world.world_path} to {out_world.world_path}')
        except Exception as e:
            message = f'Error during conversion\n{e}'
            log.error(message, exc_info=True)
        self._update_loading_bar(0, 100)
        self.convert_button.Enable()
        wx.MessageBox(
            message
        )
        work_count -= 1

    def is_closeable(self):
        if work_count:
            log.info(f'World {self.world.world_path} is still being converted. Please let it finish before closing')
        return work_count == 0

    def _close_world(self, evt):
        self.GetGrandParent().GetParent().close_world(self.world.world_path)


export = {
    "name": "Convert",
    "ui": ConvertExtension
}
