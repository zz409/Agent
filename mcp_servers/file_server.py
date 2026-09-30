import pathlib
from mcp.server import MCPServer

mcp = MCPServer("file_server")

WORKSPACE = pathlib.Path("generated_site")

WORKSPACE.mkdir(
    exist_ok = True
)

@mcp.tool()
def write_file(
    path:str,
    content:str
)->str:
    """Create or modify a file"""
    try:

        file_path=WORKSPACE/path

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        file_path.write_text(
            content,
            encoding="utf-8"
            )
        
        return f"file write successful:{file_path}"

    except Exception as e:
        return (
            f"write file failed:"
            f"{type(e).__name__}:{e}"
        )

@mcp.tool()
def read_file(
    path:str
)->str:
    """read a file"""
    try:
        file_path = WORKSPACE/path

        return file_path.read_text(encoding="utf-8")

    except Exception as e:
        return (
            f"read file failed:"
            f"{type(e).__name__}:{e}"
        )

@mcp.tool()
def list_files()->str:
    """List all files in the workspace"""
    try:
        files=[]
        for path in WORKSPACE.rglob("*"):
            if path.is_file():
                files.append(
                    str(
                        path.relative_to(WORKSPACE)
                    )
                )
        return "\n".join(files)
    except Exception as e:
        return (
            f"list files failed:"
            f"{type(e).__name__}:{e}"
        )

if __name__ == "__main__":
    mcp.run()