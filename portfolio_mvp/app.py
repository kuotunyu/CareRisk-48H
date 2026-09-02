"""Hugging Face Space entry point for the portfolio MVP."""

from carerisk_mvp.ui import create_demo


demo = create_demo()


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=False,
    )
