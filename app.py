"""Hugging Face Space entry point."""

from app.dashboard import create_app

demo = create_app()

if __name__ == "__main__":
    demo.launch()
