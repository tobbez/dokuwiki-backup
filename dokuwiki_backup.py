#!/usr/bin/env python3
#
# Copyright 2019 Torbjörn Lönnemark <tobbez@ryara.net>
#
# Permission to use, copy, modify, and distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright
# notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

import argparse
import datetime
import io
import os
import phpserialize
import tarfile

from pathlib import Path


def filter_changes_file(path):
  output = io.BytesIO()
  with open(path, 'rb') as infile:
    for ln in infile:
      fields = ln.split(b'\t', 2)
      output.write(b'\t'.join([fields[0], b'redacted-ip', fields[2]]))
  size = output.tell()
  output.seek(0)
  return output, size


def filter_meta_file(path):
  with open(path, 'rb') as f:
    data = phpserialize.load(f)

  for key in [b'current', b'persistent']:
    if key in data and b'last_change' in data[key] and isinstance(data[key][b'last_change'], dict) and b'ip' in data[key][b'last_change']:
      if data[key][b'last_change'][b'ip'] != b'127.0.0.1':
        data[key][b'last_change'][b'ip'] = b'redacted-ip'

  output = io.BytesIO()
  phpserialize.dump(data, output)
  size = output.tell()
  output.seek(0)

  return output, size


def make_empty_users_auth_file():
  """
  Return a default dokuwiki conf/users.auth.php file (with no users).
  """
  output = io.BytesIO()
  output.write(b'''# users.auth.php
# <?php exit()?>
# Don't modify the lines above
#
# Userfile
#
# Format:
#
# login:passwordhash:Real Name:email:groups,comma,separated
''')
  size = output.tell()
  output.seek(0)
  return output, size


class DokuwikiBackuper:
  def __init__(self):
    self.arg_parser = argparse.ArgumentParser(allow_abbrev=False)
    self.arg_parser.add_argument('--output-dir', '-o', help='Directory where the backup archive should be stored. It is passed through strftime before it is used. Created if it does not exist.', required=True)
    self.arg_parser.add_argument('--name-prefix', '-p', type=str, default=(), nargs=1, help='Optional prefix to prepend to the output archive name.')
    self.arg_parser.add_argument('--keep-users', action='store_false', dest='exclude_users', help='Include the user file in the backup. The default is to exclude it.')
    self.arg_parser.add_argument('--keep-ips', action='store_false', dest='strip_ips', help='Keep IP addresses in the backup. The default is to strip them.')
    self.arg_parser.add_argument('dokuwiki_root', type=Path, help='Path to the dokuwiki directory that should be backed up.')

  def run(self):
    self.args = self.arg_parser.parse_args()

    now = datetime.datetime.utcnow()

    output_dir = Path(now.strftime(self.args.output_dir))

    output_filename = '-'.join(list(self.args.name_prefix) + [self.args.dokuwiki_root.absolute().name, now.strftime('%Y-%m-%d_%H-%M-%SZ') + '.tar.xz'])
    output_path_temp = output_dir / (output_filename + '.tmp')

    output_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(output_path_temp, mode='w:xz', preset=9) as tf:
      os.chdir(self.args.dokuwiki_root.parent)
      for path, dirs, files in os.walk(self.args.dokuwiki_root.name):
        relpath = os.path.relpath(path, self.args.dokuwiki_root)
        if relpath in ('data/cache', 'data/index', 'data/locks'):
          # exclude contents of cache directories
          dirs.clear()
          files.clear()

        for name in dirs:
          tf.add(os.path.join(path, name), recursive=False)

        for name in files:
          if self.args.strip_ips and relpath.startswith('data/') and os.path.splitext(name)[1] in ('.changes', '.meta'):
            file_path = os.path.join(path, name)
            info = tf.gettarinfo(file_path)
            if name.endswith('.changes'):
              filtered_file, info.size = filter_changes_file(file_path)
            elif name.endswith('.meta'):
              filtered_file, info.size = filter_meta_file(file_path)
            tf.addfile(info, filtered_file)
          elif relpath == 'conf' and name == 'users.auth.php' and self.args.exclude_users:
            info = tf.gettarinfo(os.path.join(path, name))
            empty_users_auth_file, info.size = make_empty_users_auth_file()
            tf.addfile(info, empty_users_auth_file)
          else:
            tf.add(os.path.join(path, name), recursive=False)

    output_path_temp.rename(output_path_temp.with_name(output_filename))


if __name__ == '__main__':
  DokuwikiBackuper().run()
