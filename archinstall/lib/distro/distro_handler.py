import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from archinstall.lib.log import info, warn
from archinstall.lib.models.distro import DistroConfiguration

if TYPE_CHECKING:
	from archinstall.lib.installer import Installer

# Chaotic AUR keyring bootstrap (official documented key id and package URLs)
_CHAOTIC_SIGNING_KEY = '30565152B0F46513'
_CHAOTIC_KEYSERVER = 'keyserver.ubuntu.com'
_CHAOTIC_KEYRING_URL = 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'
_CHAOTIC_MIRRORLIST_URL = 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'

_CHAOTIC_AUR_BLOCK = """\
[chaotic-aur]
Include = /etc/pacman.d/chaotic-mirrorlist
"""

# Personal distro repository. Set these once the repo exists
# (see the distro repo plan); left unset the entry is skipped.
_CUSTOM_REPO_NAME = 'custom'
_CUSTOM_REPO_URL: str | None = None  # e.g. 'https://repo.example.com/$arch'

# Desktop defaults shipped on the install ISO (live system paths)
_LIVE_DCONF_DEFAULTS = Path('/etc/dconf/db/local.d/00-gnome-custom')
_LIVE_GTK_SKEL_SETTINGS = Path('/etc/skel/.config/gtk-3.0/settings.ini')
_LIVE_LIBVIRTD_CONF = Path('/etc/libvirt/libvirtd.conf')
_LIVE_LIBVIRT_POLKIT_RULE = Path('/etc/polkit-1/rules.d/50-libvirt.rules')


class DistroHandler:
	def install_distro(self, installation: Installer, distro_config: DistroConfiguration) -> None:
		if distro_config.libvirt:
			self._setup_libvirt(installation)

		if distro_config.chaotic_aur or distro_config.custom_repo:
			self._setup_repositories(installation, distro_config)

		if distro_config.gnome_defaults or distro_config.breeze_dark:
			self._setup_desktop_defaults(installation, distro_config)

	def _setup_libvirt(self, installation: Installer) -> None:
		info('Setting up libvirt virtualization support')

		installation.add_additional_packages(
			[
				'libvirt',
				'qemu-desktop',
				'virt-manager',
				'virt-viewer',
				'dnsmasq',
				'dmidecode',
			]
		)
		installation.enable_service('libvirtd')

		# user group membership is seeded onto the User objects before
		# create_users() runs (see guided.py)
		self._copy_live_file(
			_LIVE_LIBVIRTD_CONF,
			installation.target / 'etc/libvirt/libvirtd.conf',
		)
		self._copy_live_file(
			_LIVE_LIBVIRT_POLKIT_RULE,
			installation.target / 'etc/polkit-1/rules.d/50-libvirt.rules',
		)

	def _setup_repositories(self, installation: Installer, distro_config: DistroConfiguration) -> None:
		pacman_conf = installation.target / 'etc' / 'pacman.conf'

		if distro_config.chaotic_aur:
			if self._bootstrap_chaotic_keyring(installation):
				with pacman_conf.open('a') as fp:
					fp.write('\n' + _CHAOTIC_AUR_BLOCK)
				info('Enabled Chaotic AUR repository on target')
			else:
				warn('Skipping Chaotic AUR: keyring bootstrap failed')

		if distro_config.custom_repo:
			if _CUSTOM_REPO_URL:
				with pacman_conf.open('a') as fp:
					fp.write(f'\n[{_CUSTOM_REPO_NAME}]\nSigLevel = Required\nServer = {_CUSTOM_REPO_URL}\n')
				info(f'Enabled custom repository "{_CUSTOM_REPO_NAME}" on target')
			else:
				warn('Skipping custom repository: no repo URL configured yet')

	def _bootstrap_chaotic_keyring(self, installation: Installer) -> bool:
		info('Bootstrapping Chaotic AUR keyring on target')

		commands = [
			'pacman-key --init',
			f'pacman-key --recv-keys {_CHAOTIC_SIGNING_KEY} --keyserver {_CHAOTIC_KEYSERVER}',
			f'pacman-key --lsign-key {_CHAOTIC_SIGNING_KEY}',
			f'pacman -U --noconfirm {_CHAOTIC_KEYRING_URL} {_CHAOTIC_MIRRORLIST_URL}',
		]

		for cmd in commands:
			try:
				result = installation.run_command(cmd)
			except Exception as err:
				warn(f'Chaotic AUR keyring bootstrap failed at "{cmd}": {err}')
				return False

			if result.exit_code != 0:
				warn(f'Chaotic AUR keyring bootstrap failed at "{cmd}": {result}')
				return False

		return True

	def _setup_desktop_defaults(self, installation: Installer, distro_config: DistroConfiguration) -> None:
		if distro_config.gnome_defaults:
			target_dir = installation.target / 'etc/dconf/db/local.d'
			if self._copy_live_file(_LIVE_DCONF_DEFAULTS, target_dir / _LIVE_DCONF_DEFAULTS.name):
				try:
					installation.run_command('dconf update')
				except Exception as err:
					warn(f'Could not run dconf update on target: {err}')

		if distro_config.breeze_dark:
			installation.add_additional_packages(
				[
					'breeze-gtk',
					'breeze',
					'qt5ct',
					'qt6ct',
					'kvantum',
				]
			)
			self._copy_live_file(
				_LIVE_GTK_SKEL_SETTINGS,
				installation.target / 'etc/skel/.config/gtk-3.0/settings.ini',
			)

	@staticmethod
	def _copy_live_file(source: Path, destination: Path) -> bool:
		if not source.exists():
			warn(f'Distro default not found on install media: {source} (skipping)')
			return False

		destination.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(source, destination)
		info(f'Installed distro default: {destination}')
		return True
