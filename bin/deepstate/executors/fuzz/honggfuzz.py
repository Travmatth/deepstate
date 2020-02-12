# Copyright (c) 2019 Trail of Bits, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import logging
import argparse

from tempfile import mkdtemp
from typing import List, Dict, Optional

from deepstate.core import FuzzerFrontend, FuzzFrontendError

L = logging.getLogger(__name__)


class Honggfuzz(FuzzerFrontend):

  NAME = "HonggFuzz"
  SEARCH_DIRS = ["hfuzz_cc"]
  EXECUTABLES = {"FUZZER": "honggfuzz",
                  "COMPILER": "hfuzz-clang++"
                  }


  @classmethod
  def parse_args(cls) -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
      description="Use Honggfuzz as a backend for DeepState")

    cls.parser = parser
    super(Honggfuzz, cls).parse_args()


  def compile(self) -> None: # type: ignore
    lib_path: str = "/usr/local/lib/libdeepstate_HFUZZ.a"

    # check if we should fallback to default static library
    if not os.path.isfile(lib_path):
      flags: List[str] = ["-ldeepstate"]
    else:
      flags = ["-ldeepstate_HFUZZ"]

    if self.compiler_args:
      flags += [arg for arg in self.compiler_args.split(" ")]
    super().compile(lib_path, flags, self.out_test_name + ".hfuzz")


  def pre_exec(self):
    super().pre_exec()

    # require input seeds
    if self.input_seeds is None:
      self.input_seeds = mkdtemp()
      with open(os.path.join(self.input_seeds, "fake_seed"), 'wb') as f:
        f.write(b'X')
      L.info("Creating fake input seeds directory: %s", self.input_seeds)


  @property
  def cmd(self):
    cmd_list: List[str] = list()

    # guaranteed arguments
    cmd_list.extend([
      "--output", self.output_test_dir,  # auto-create, reusable
      "--workspace", self.output_test_dir,
      "--rlimit_rss", str(self.mem_limit),
    ])

    if self.max_input_size == 0:
      cmd_list.extend(["--max_file_size", "1099511627776"])  # use 1TiB as unlimited
    else:
      cmd_list.extend(["--max_file_size", str(self.max_input_size)])

    # TODO add qemu mode
    if self.blackbox == True:
      cmd_list.append("--noinst")

    for key, val in self.fuzzer_args:
      if len(key) == 1:
        cmd_list.append('-{}'.format(key))
      else:
        cmd_list.append('--{}'.format(key))
      if val is not None:
        cmd_list.append(val)

    # optional arguments:
    # required, if provided: not auto-create and not require any files inside
    if self.input_seeds:
      cmd_list.extend(["--input", self.input_seeds])

    if self.exec_timeout:
      cmd_list.extend(["--timeout", str(self.exec_timeout  / 1000)])

    if self.dictionary:
      cmd_list.extend(["--dict", self.dictionary])

    # TODO: autodetect hardware features
    cmd_list.append("--linux_keep_aslr")

    return self.build_cmd(cmd_list, input_symbol="___FILE___")


  @property
  def stats(self) -> Dict[str, Optional[str]]:
    """
    Retrieves and parses the stats file produced by Honggfuzz
    """
    out_dir: str = os.path.abspath(self.output_test_dir)
    report_file: str = "HONGGFUZZ.REPORT.TXT"

    # read report file generated by honggfuzz
    stat_file: str = os.path.join(out_dir + report_file)
    with open(stat_file, "r") as sf:
      lines = sf.readlines()

    stats: Dict[str, Optional[str]] = {
      "mutationsPerRun": None,
      "externalCmd": None,
      "fuzzStdin": None,
      "timeout": None,
      "ignoreAddr": None,
      "ASLimit": None,
      "RSSLimit": None,
      "DATALimit": None,
      "wordlistFile": None,
      "fuzzTarget": None,
      "ORIG_FNAME": None,
      "FUZZ_FNAME": None,
      "PID": None,
      "SIGNAL": None,
      "FAULT ADDRESS": None,
      "INSTRUCTION": None,
      "STACK HASH": None,
    }

    # strip first 4 and last 5 lines to make a parseable file
    lines = lines[4:][:-5]

    for l in lines:
      for k in stats.keys():
        if k in l:
          stats[k] = l.split(":")[1].strip()

    # add crash metrics
    crashes: int = len([name for name in os.listdir(out_dir) if name != report_file])
    stats.update({
      "CRASHES": str(crashes)
    })

    return stats


  def reporter(self) -> Dict[str, Optional[str]]:
    """
    Report a summarized version of statistics, ideal for ensembler output.
    """
    return dict({
      "Unique Crashes": self.stats["CRASHES"],
      "Mutations Per Run": self.stats["mutationsPerRun"]
    })


  def post_exec(self) -> None:
    if self.post_stats:
      print("\n")
      for k, v in self.stats.items():
        print(f"{k} : {v}")


def main():
  fuzzer = Honggfuzz(envvar="HONGGFUZZ_HOME")
  return fuzzer.main()


if __name__ == "__main__":
  exit(main())
