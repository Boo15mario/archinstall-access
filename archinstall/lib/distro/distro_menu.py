from typing import override

from archinstall.lib.menu.abstract_menu import AbstractSubMenu
from archinstall.lib.menu.helpers import Confirmation
from archinstall.lib.models.distro import DistroConfiguration
from archinstall.lib.translationhandler import tr
from archinstall.tui.menu_item import MenuItem, MenuItemGroup
from archinstall.tui.result import ResultType


class DistroMenu(AbstractSubMenu[DistroConfiguration]):
	def __init__(
		self,
		preset: DistroConfiguration | None = None,
	) -> None:
		if preset:
			self._distro_config = preset
		else:
			self._distro_config = DistroConfiguration()

		menu_options = self._define_menu_options()
		self._item_group = MenuItemGroup(menu_options, checkmarks=True)

		super().__init__(
			self._item_group,
			config=self._distro_config,
			allow_reset=True,
		)

	@override
	async def show(self) -> DistroConfiguration | None:
		_ = await super().show()
		return self._distro_config

	def _define_menu_options(self) -> list[MenuItem]:
		return [
			MenuItem(
				text=tr('Virtualization (libvirt)'),
				action=lambda preset: _select_toggle(
					tr('Enable libvirt virtualization support?'),
					preset,
				),
				value=self._distro_config.libvirt,
				preview_action=self._prev_toggle,
				key='libvirt',
			),
			MenuItem(
				text=tr('Chaotic AUR repository'),
				action=lambda preset: _select_toggle(
					tr('Enable the Chaotic AUR repository?'),
					preset,
				),
				value=self._distro_config.chaotic_aur,
				preview_action=self._prev_toggle,
				key='chaotic_aur',
			),
			MenuItem(
				text=tr('Custom distro repository'),
				action=lambda preset: _select_toggle(
					tr('Enable the custom distro repository?'),
					preset,
				),
				value=self._distro_config.custom_repo,
				preview_action=self._prev_toggle,
				key='custom_repo',
			),
			MenuItem(
				text=tr('GNOME desktop defaults'),
				action=lambda preset: _select_toggle(
					tr('Apply the distro GNOME desktop defaults?'),
					preset,
				),
				value=self._distro_config.gnome_defaults,
				preview_action=self._prev_toggle,
				key='gnome_defaults',
			),
			MenuItem(
				text=tr('Breeze Dark theming'),
				action=lambda preset: _select_toggle(
					tr('Apply Breeze Dark theming for GTK and Qt?'),
					preset,
				),
				value=self._distro_config.breeze_dark,
				preview_action=self._prev_toggle,
				key='breeze_dark',
			),
		]

	def _prev_toggle(self, item: MenuItem) -> str | None:
		if item.value is None:
			return None

		state = tr('Enabled') if item.value else tr('Disabled')
		return f'{item.text}: {state}'


async def _select_toggle(header: str, preset: bool | None = None) -> bool:
	preset_val = preset if preset is not None else False

	result = await Confirmation(
		header=header + '\n',
		allow_skip=True,
		preset=preset_val,
	).show()

	match result.type_:
		case ResultType.Selection:
			return result.get_value()
		case ResultType.Skip:
			return preset_val
		case _:
			raise ValueError('Unhandled result type')
