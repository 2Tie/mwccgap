import subprocess
import sys
import tempfile

from pathlib import Path
from typing import Optional

from .exceptions import AssemblerException


class Assembler:
    def __init__(
        self,
        as_path="mipsel-linux-gnu-as",
        as_march="allegrex",
        as_mabi="32",
        as_flags: Optional[list[str]] = None,
        macro_inc_path: Optional[Path] = None,
    ):
        if as_flags is None:
            as_flags = []

        self.as_path = as_path
        self.as_march = as_march
        self.as_mabi = as_mabi
        self.as_flags = as_flags
        self.macro_inc_path = macro_inc_path

    def assemble_file(
        self,
        asm_filepath: Path,
        encoding: str,
    ) -> bytes:
        with tempfile.NamedTemporaryFile(suffix=".o") as temp_file:
          with tempfile.NamedTemporaryFile(suffix=".s") as localfile:
            conv = [
                "iconv",
                "-f", "utf-8",
                "-t", encoding,
                asm_filepath,
                "-o", localfile.name
            ]


            cmd = [
                self.as_path,
                "-EL",
                f"-march={self.as_march}",
                f"-mabi={self.as_mabi}",
                "-o",
                temp_file.name,
                *self.as_flags,
            ]

            in_path = asm_filepath
            if self.macro_inc_path:
                cmd.insert(4, f"-I{str(self.macro_inc_path.resolve().parent)}")
            if encoding != "utf-8" and asm_filepath.stem[0] == "@":
                print(f"converting encoding for {asm_filepath} to {encoding}")
                result = subprocess.run(
                    conv,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                    #in_bytes = asm_filepath.read_bytes()
                    #if self.macro_inc_path and self.macro_inc_path.is_file():
                    #    in_bytes = self.macro_inc_path.read_bytes() + in_bytes

                if result.stdout:
                    sys.stderr.write(result.stdout.decode(encoding))
                if result.stderr:
                    sys.stderr.write(result.stderr.decode(encoding))

                #print(result.args)

                if result.returncode != 0:
                    raise AssemblerException(
                        f"Failed to reencode {asm_filepath} (iconv returned {result.returncode})"
                    )
                in_path = Path(localfile.name)
                #print(asm_filepath.read_bytes())

            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ) as process:
                in_bytes = in_path.read_bytes()
                #print(in_bytes)
                if len(in_bytes) == 0:
                    raise AssemblerException(f"{asm_filepath}: file empty!")
                if self.macro_inc_path and self.macro_inc_path.is_file():
                    in_bytes = self.macro_inc_path.read_bytes() + in_bytes

                stdout, stderr = process.communicate(input=in_bytes)

                if stdout:
                    sys.stderr.write(stdout.decode(encoding))
                if stderr:
                    sys.stderr.write(stderr.decode(encoding))

                if process.returncode != 0:
                    raise AssemblerException(
                        f"Failed to assemble {asm_filepath} (assembler returned {process.returncode})"
                    )

            obj_bytes = temp_file.read()
            #print(obj_bytes)

        if len(obj_bytes) == 0:
            raise AssemblerException(
                f"Failed to assemble {asm_filepath} (object is empty)"
            )
        #print(len(obj_bytes))
        return obj_bytes
