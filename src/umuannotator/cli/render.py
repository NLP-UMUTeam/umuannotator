import json
from pathlib import Path

import typer

from umuannotator.renderers.console import render_corpus
from umuannotator.renderers.html import render_html

app = typer.Typer(help="Render annotated outputs.")


@app.command("console")
def console(
    input_path: str = typer.Option(..., "--input", "-i"),
):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    render_corpus(data)


@app.command("html")
def html(
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str = typer.Option(..., "--output", "-o"),
    title: str = typer.Option("UMU Annotator", "--title"),
):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_content = render_html(
        data,
        title=title,
    )

    Path(output_path).write_text(
        html_content,
        encoding="utf-8",
    )