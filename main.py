import os
import sys

import uvicorn

package_path = [os.path.dirname(os.path.abspath(__file__)), "/CodeSnippetAPI"]
sys.path.append("".join(package_path))

from eventLoop_processPool.app import application as app


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000,
                loop="uvloop",
                reload=True,
                timeout_keep_alive=60)
