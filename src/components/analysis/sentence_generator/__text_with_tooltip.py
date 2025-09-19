import re
import dash_mantine_components as dmc


TOKEN_RE = re.compile(r"\[\[CI:(?P<label>[^|\]]+)\|(?P<display>[^\]]+)\]\]")


def render_text_with_tooltips(paragraph: str) -> dmc.Text:

    children = [] # Children for the resulting dmc.Text
    pos = 0
    for match in TOKEN_RE.finditer(paragraph):
        if match.start() > pos:
            # Text between the start of paragraph and the start of our first token.
            before = paragraph[pos:match.start()] # Text before a CI token
            children.append(before)
        # Handle the token
        label = match.group('label')
        display = match.group('display')
        children.append(
            dmc.Tooltip(
                label=label,
                withArrow=True,
                position="top",
                withinPortal=True,
                children=dmc.Text(display, span=True, w=700),
                boxWrapperProps={"style": {"display": "inline-block"}}
            )
        )
        pos = match.end() # Update position to the end of this token

    if pos < len(paragraph):
        # Residual text between last token and end of paragraph.
        children.append(paragraph[pos:])

    return dmc.Text(children, span=True)