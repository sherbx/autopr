import ast
from dataclasses import dataclass


@dataclass
class CodeChunk:
    file_path: str
    symbol_name: str
    chunk_type: str
    start_line: int
    end_line: int
    content: str


class ASTCodeChunker:
    @staticmethod
    def chunk_python_file(file_path: str, source_code: str) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            # Fallback to naive chinking if file is broken.
            return [
                CodeChunk(
                    file_path,
                    "file_raw",
                    "raw",
                    1,
                    len(source_code.splitlines()),
                    source_code,
                )
            ]

        lines = source_code.splitlines()

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                content = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        symbol_name=node.name,
                        chunk_type="function",
                        start_line=node.lineno,
                        end_line=node.end_lineno,
                        content=content,
                    )
                )
            elif isinstance(node, ast.ClassDef):
                content = "\n".join(lines[node.lineno - 1 : node.end_lineno])
                chunks.append(
                    CodeChunk(
                        file_path=file_path,
                        symbol_name=node.name,
                        chunk_type="class",
                        start_line=node.lineno,
                        end_line=node.end_lineno,
                        content=content,
                    )
                )

        return chunks
