import typer

from umuannotator.io.html import write_html_output
from umuannotator.io.json import read_json_input
from umuannotator.renderers.console import render_corpus
from umuannotator.renderers.html import render_html

app = typer.Typer(help="Render annotated outputs.")


@app.command("console")
def console(
    input_path: str = typer.Option(..., "--input", "-i"),
):
    data = read_json_input(input_path)

    render_corpus(data)


@app.command("html")
def html(
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str = typer.Option(..., "--output", "-o"),
    title: str = typer.Option("UMU Annotator", "--title"),
):
    data = read_json_input(input_path)

    html_content = render_html(
        data,
        title=title,
    )

    write_html_output(
        html_content,
        output_path,
    )