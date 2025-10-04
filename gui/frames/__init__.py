# gui/frames/__init__.py

from .footer_frame import FooterFrame
from .header_frame import HeaderFrame
from .history_frame import HistoryFrame
from .input_frame import InputFrame
from .notebook_frame import NotebookFrame
from .settings_frame import SettingsFrame
from .status_frame import StatusFrame

__all__ = [
    'HeaderFrame',
    'InputFrame',
    'NotebookFrame',
    'StatusFrame',
    'FooterFrame',
    'HistoryFrame',
    'SettingsFrame'
]