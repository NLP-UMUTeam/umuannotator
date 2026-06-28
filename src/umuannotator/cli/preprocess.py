from __future__ import annotations

import typer

app = typer.Typer(help="Preprocessing commands.")


@app.command("stanza")
def stanza_preprocess(
    input_path: str = typer.Option(..., "--input", "-i"),
    output_path: str = typer.Option(..., "--output", "-o"),
    text_column: str = typer.Option("text", "--text-column"),
    sep: str = typer.Option(",", "--sep"),
    language: str = typer.Option("es", "--language", "-l"),
    processors: str = typer.Option(
        "tokenize,pos,lemma,ner",
        "--processors",
    ),
    limit: int | None = typer.Option(None, "--limit"),
):
    from umuannotator.preprocessing.stanza_cache import build_stanza_cache

    build_stanza_cache(
        input_path=input_path,
        output_path=output_path,
        text_column=text_column,
        sep=sep,
        language=language,
        processors=processors,
        limit=limit,
    )