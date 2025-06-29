from pathlib import Path
from shutil import copy2, copystat, make_archive, rmtree

parents = Path(__file__).parents
src = parents[1]
dest = parents[0]
release_root = dest / 'release'
release = release_root / 'pathfinder'

flist = [
    '__init__.py',
    'pathfinder.py',
    'metadata.txt',
    'LICENSE',
    'i18n/pathfinder_de.qm',
    'icons/__init__.py',
    'icons/open_in_explorer.svg',
    'icons/copy.svg',
    'lib/core.py',
    'lib/i18n.py',
    'lib/constants.py',
    'lib/gui.py',
    'lib/settings.py',
    'ui/settingsdiag.ui'
]

dirs = ['i18n', 'icons', 'lib', 'ui']

release.mkdir(parents=True)

for d in dirs:
    release.joinpath(d).mkdir(parents=True)
    copystat(src / d, release / d)

for f in flist:
    copy2(src / f, release / f)

make_archive('pathfinder', 'zip', root_dir=release_root)
rmtree(release_root)
