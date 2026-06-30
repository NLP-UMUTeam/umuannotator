import typer

from umuannotator.io.html import write_html_output
from umuannotator.io.render import read_render_input
from umuannotator.renderers.console import render_corpus
from umuannotator.renderers.html import render_html

app = typer.Typer(help="Render annotated outputs.")


@app.command("console")
def console(
    input_path: str = typer.Option(..., "--input", "-i"),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help="Input format: json or jsonl. Required when --input - is JSONL.",
    ),
):
    data = read_render_input(
        input_path,
        input_format=input_format,
    )

    render_corpus(data)


@app.command("html")
def html(
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str = typer.Option(..., "--output", "-o"),
    title: str = typer.Option("UMU Annotator", "--title"),
    input_format: str | None = typer.Option(
        None,
        "--input-format",
        help="Input format: json or jsonl. Required when --input - is JSONL.",
    ),
):
    data = read_render_input(
        input_path,
        input_format=input_format,
    )

    html_content = render_html(
        data,
        title=title,
    )

    write_html_output(
        html_content,
        output_path,
    )