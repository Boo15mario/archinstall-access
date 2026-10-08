from dataclasses import dataclass
from typing import Any, Self, TypedDict, override

from archinstall.lib.models.config import SubConfig, SummaryLevel
from archinstall.lib.translationhandler import tr


class DistroSerialization(TypedDict):
	libvirt: bool
	chaotic_aur: bool
	gnome_defaults: bool
	breeze_dark: bool


@dataclass
class DistroConfiguration(SubConfig):
	libvirt: bool = False
	chaotic_aur: bool = False
	gnome_defaults: bool = False
	breeze_dark: bool = False

	NAME: str = tr('Distro Setup')

	@classmethod
	def parse_arg(cls, args: dict[str, Any] | None = None) -> Self:
		config = cls()

		if args:
			config.libvirt = args.get('libvirt', False)
			config.chaotic_aur = args.get('chaotic_aur', False)
			config.gnome_defaults = args.get('gnome_defaults', False)
			config.breeze_dark = args.get('breeze_dark', False)

		return config

	@override
	def json(self) -> DistroSerialization:
		return {
			'libvirt': self.libvirt,
			'chaotic_aur': self.chaotic_aur,
			'gnome_defaults': self.gnome_defaults,
			'breeze_dark': self.breeze_dark,
		}

	@override
	def summary(self, _level: SummaryLevel = SummaryLevel.BASIC) -> list[str]:
		def _state(enabled: bool) -> str:
			return tr('Enabled') if enabled else tr('Disabled')

		return [
			f'{tr("Virtualization (libvirt)")}: {_state(self.libvirt)}',
			f'{tr("Chaotic AUR repository")}: {_state(self.chaotic_aur)}',
			f'{tr("GNOME desktop defaults")}: {_state(self.gnome_defaults)}',
			f'{tr("Breeze Dark theming")}: {_state(self.breeze_dark)}',
		]
