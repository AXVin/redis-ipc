"""
Copyright (C) 2021-present  AXVin

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import NamedTuple
from redisipc.ipc import *

__title__ = 'redis-ipc'
__author__ = 'AXVin'
__license__ = 'AGPL v3'
__copyright__ = 'Copyright 2021-present AXVin'
__version__ = "0.0.4"


class VersionInfo(NamedTuple):
    major: int
    minor: int
    micro: int
    releaselevel: str
    serial: int


version_info = VersionInfo(major=0, minor=0, micro=4, releaselevel='final', serial=0)
