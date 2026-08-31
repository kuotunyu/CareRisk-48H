"""Fixed FastAPI/Gradio composition for the public Docker Space."""

import gradio as gr
import uvicorn
from carerisk_space.ui import (
    PublicSurfaceGuard,
    build_package_asset_membership,
    create_app,
)
from fastapi import FastAPI

demo = create_app()
parent = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
gr.mount_gradio_app(
    parent,
    demo,
    path="/",
    server_name="0.0.0.0",
    server_port=7860,
    footer_links=[],
    run_history=False,
    root_path="",
    allowed_paths=["/__carerisk_no_allowed_files__"],
    blocked_paths=["/"],
    favicon_path=None,
    show_error=False,
    max_file_size=0,
    ssr_mode=False,
    enable_monitoring=False,
    pwa=False,
    mcp_server=False,
)
app = PublicSurfaceGuard(parent, build_package_asset_membership())


def main() -> None:
    """Serve the preconstructed outer ASGI application with fixed h11."""

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860,
        workers=1,
        http="h11",
        proxy_headers=False,
        forwarded_allow_ips="",
        access_log=False,
        server_header=False,
        date_header=False,
        reload=False,
        factory=False,
        env_file=None,
        log_config=None,
    )


if __name__ == "__main__":
    main()
